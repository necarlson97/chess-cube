import time
from datetime import timezone, timedelta, datetime as dt
from dateutil.parser import parse as date_parse

import smtplib
import poplib
from email.parser import Parser
from email.mime.text import MIMEText
import yaml

from player import Player
from match_names import generate_match_name

def read_config_file():
    # Read in the config file to get sensative (non-git) email info
    with open('assets/config.yaml', 'r') as f:
        dikt = yaml.safe_load(f)['email_config']

    # Allows to access this dict as if it were an object
    # TODO do we need this? Is there a better way?
    class ObjectView():
        def __init__(self, d):
            self.__dict__ = d
    return ObjectView(dikt)

# Get save data from yaml file
CONFIG = read_config_file()

class EmailPlayer(Player):
    """
    A human typing in their moves in the terminal
    """

    email_list = []

    def __init__(slef, *args, **kwargs):
        """
        Initialize normally, only add that this player gives a match
        name to the game (so multiple email players can keep track of separate games)
        """
        super().__init__(*args, **kwargs)
        self.match_name = generate_match_name()

    def get_move(self):
        """
        Poll from std-in until we get an input that
        is a valid move
        """
        inp = self.get_email_input()
        self.email_list.push(f'INPUT: {inp}')
        return inp

    def hear_move(self, move):
        english_str = self.referee.parser.move_to_english(move)
        self.email_list.push(f'REPLY: {english_str}')

    def hear(sefl, s):
        self.email_list.push(s)

    def win(self):
        self.email_list.push(f'You win!')

    def lose(self):
        self.email_list.push(f'You lose...')

    def draw(self):
        self.email_list.push('Game was a draw')

    def get_subject(self):
        """
        Get the current subject to send emails under
        (starts as a root name, but gets 'RE:' added
        with every additional email)
        """
        return self._subject

    def commit_emails(self):
        """
        Send any pending emails.
        (Allows us to prevent sending an email for every little thing,
        but rather store them up to send at once)
        """
        if self.email_list == []:
            return
        self.send_email(email_list.join('\n'))

    def send_email(self, s):
        """
        Given a string 's', send an email with that body as the string
        """
        msg = MIMEText(s)
        msg['Subject'] = self.get_subject()
        msg['From'] = CONFIG.sender
        msg['To'] = ','.join(CONFIG.targets)

        server = smtplib.SMTP_SSL(CONFIG.smtp_ssl_host, CONFIG.smtp_ssl_port)
        server.login(CONFIG.username, CONFIG.password)
        server.sendmail(CONFIG.sender, CONFIG.targets, msg.as_string())
        server.quit()

    def get_email_input(self):
        """
        Wait for an email response, checking periodically.
        Once one is found, return it.
        """
        # Send any unsent responses
        self.commit_emails()
        # TODO could timeout after some amount of polling
        while True:
            check_time = dt.now(timezone.utc)
            print(f'Checking at {check_time}...')

            message = self.get_email_message()
            # If we have a non-trivial message
            if message.replace('\n', ''):
                return message

            time.sleep(10)  # Could make config-able

    def _get_email_messages(self):
        """
        Poll the email server, filtering to find only emails that
        have to do with this game of chess. The 'raw' email
        info is returned as an object with the following dict keys:
        'Subject', 'Date', 'From'
        The body of the email is gotten with:
        '.get_payload()' (though there may be multiple payloads)
        """

        pop_conn = poplib.POP3_SSL('mail.gandi.net')
        pop_conn.user(CONFIG.username)
        pop_conn.pass_(CONFIG.password)

        # Helper function that gets given raw email bytes and returns
        # dict of useful info
        # TODO should use parser or whatever
        def get_message_info(pop_conn, i):
            # Get the raw info from the email
            # (for whatever reason, they are 1-indexed)
            try:
                resp, lines, octets = pop_conn.retr(i + 1)
            except poplib.error_proto:
                return None

            # Decode, and use parser to create useful Message object
            msg_content = b'\r\n'.join(lines).decode('utf-8')
            return Parser().parsestr(msg_content)

        # Get messages from server, and parse them to message objects
        all_messages = []
        numMessages = len(pop_conn.list()[1])
        # We don't need to check all messages, just the most recent ones
        recent_msg_count = 5
        for i in range(numMessages - recent_msg_count, numMessages):
            msg = get_message_info(pop_conn, i)
            if msg is not None:
                all_messages.append(msg)
        pop_conn.quit()

        messages = []
        for m in all_messages:
            # Filer so we only get messages from the targets
            if not any(t in m.get('From') for t in CONFIG.targets):
                continue

            # Filter so it only responds to its own match
            if self.match_name not in m['Subject']:
                continue

            # Check to see if we should have seen this message before
            message_date = date_parse(m.get('Date'))
            if message_date < self.last_check_date:
                continue

            # Update our most recent check as being now, so we don't use
            # these same messages again
            self.last_check_date = dt.now(timezone.utc)
            self._subject = f"Re: {m['Subject']}"
            messages.append(m)

        return messages

    def get_email_message(self):
        # Get all message dicts
        messages = self.get_email_messages()

        # Return all of their bodies
        bodies = []
        for m in messages:
            if m.is_multipart():
                for payload in m.get_payload():
                    # if payload.is_multipart(): ...
                    bodies.append(payload.get_payload())
            else:
                bodies.append(m.get_payload())

        # Because google delivers multiparts with html as one part,
        # we ignore the html for now. Additionally, we want to keep alphanum
        # AND special characters (like when setting fen code) but we want
        # to remove weird newlines (\r\n). For now we just get the first line
        bodies = [
            b.replace('\r', '').split('\n')[0]
            for b in bodies if not b.startswith('<')
        ]
        return '\n'.join(bodies)
