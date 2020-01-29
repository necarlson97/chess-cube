import time
from datetime import timezone, timedelta, datetime as dt
from dateutil.parser import parse as date_parse

import smtplib
import poplib
from email.parser import Parser
from email.mime.text import MIMEText
import yaml

from living_board import LivingBoard
from speaker import Speaker
from text_input import TextInput
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


class EmailSpeaker(Speaker):
    # A class that allows us to override the method that would
    # normally speak the result to the player, and instead have it
    # sent as an email

    # For now, we are voicing always as false until I get espeak
    # working on the rpi
    voiced = False

    def __init__(self, email_chess, living_board=None, quiet=False):
        super().__init__(living_board, quiet)
        self.email_chess = email_chess
        # TODO DOC
        self._email_list = []

    def say(self, s, wait=False, slow=False, end=None, voiced=False):
        """
        After performing normal 'say' action
        (printing, but not speaking out load)
        then perform email.
        """
        s = str(s)
        super().say(s, wait, slow, end, voiced)
        self._email_list.append(s)

    def send_email(self, s):
        # TODO DOC
        msg = MIMEText(s)
        msg['Subject'] = self.email_chess.get_subject()
        msg['From'] = CONFIG.sender
        msg['To'] = ','.join(CONFIG.targets)

        server = smtplib.SMTP_SSL(CONFIG.smtp_ssl_host, CONFIG.smtp_ssl_port)
        server.login(CONFIG.username, CONFIG.password)
        server.sendmail(CONFIG.sender, CONFIG.targets, msg.as_string())
        server.quit()

    def commit(self):
        # TODO DOC
        s = '\n'.join(self._email_list)
        self._email_list = []
        if s.replace('\n', ''):
            self.send_email(s)


class EmailInput(TextInput):
    """
    Because we want to add long pauses between email moves,
    we modify the email input (that way, we only pause)
    on 'actual' inputs, not codes of failed inputs
    """

    def __init__(self, email_chess):
        self.email_chess = email_chess
        self.living_board = email_chess.living_board
        self.speaker = self.living_board.speaker

    def pause_to_think(self):
        """
        When playing a game, we want the game to stretch out slowley
        over the course of the day, and not be particularly. To do this,
        we simply have the thread pause for an hour (or whatever time
        delta) after recieving a move.

        '*' codes (show board, reset game, etc) happen immediatly
        """
        if self.email_chess.THINK_TIME_DELTA is None:
            return
        print(f'Pausing to "think" for {self.email_chess.THINK_TIME_DELTA}')
        secs = self.email_chess.THINK_TIME_DELTA.total_seconds()
        time.sleep(secs)

    def get_input_func(self):
        """
        Returns a function which can be called to get the user input from
        email AND handles the long pausing (a desired trait of the email AI)
        """

        # Taking in digits from the (for now) keypad
        def text_input():
            while True:
                raw = self.email_chess.get_email_input()
                print(f'Email input raw: "{raw}"')

                res = self.try_input(raw)
                if res is not None:
                    print(f'Valid input "{res}", pausing to think...')
                    self.pause_to_think()
                    return res

        return text_input


class EmailChess():
    """
    Play chess over email! Email your responses just the same
    as you would into the terminal - thats the idea at least
    """

    # TODO would be nice to have this as a var that can be passed
    # for easier testing
    RESET_TIME_DELTA = None
    THINK_TIME_DELTA = timedelta(minutes=30)

    def __init__(self):

        # Used to tell what emails are concidered 'recent'
        self.last_check_date = dt.now(timezone.utc)
        # In the past, we used the date:
        # f'Chess {self.last_check_date}'
        # But for now, we will use a silly name
        self.match_name = generate_match_name()
        # USe this match name as the starting subject of our email
        # (will become RE: subject then RE: RE: subject, etc)
        self._subject = self.match_name

        self.speaker = EmailSpeaker(self)
        self.living_board = LivingBoard(speaker=self.speaker)
        # Use a special text input as the retriever for human moves
        ti = EmailInput(self)
        self.living_board.get_human_move_uci = ti.get_input_func()

    def play_game(self):
        self.living_board.play_game()
        # When the game is over, we need to email final results
        # because emails are normally sent when listening for replies
        self.speaker.commit()

    def get_email_messages(self):
        # TODO DOC
        try:
            return self._get_email_messages()
        except Exception as e:
            print(f'"get_email_messages" exception caught: {e}')
            return []

    def _get_email_messages(self):
        # TODO DOC

        # Send any unsent responses
        self.speaker.commit()

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

    def get_subject(self):
        # TODO DOC
        return self._subject

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

    def get_email_input(self):
        # Parse message intom an email object:
        while True:
            check_time = dt.now(timezone.utc)
            print(f'Checking at {check_time}...')
            message = self.get_email_message()

            # If we have a non-trivial message
            if message.replace('\n', ''):
                return message

            time.sleep(10)

            # If no update has occurred in a long time, reset the game
            should_reset = (
                EmailChess.RESET_TIME_DELTA is not None and
                (check_time - self.last_check_date) >=
                EmailChess.RESET_TIME_DELTA
            )
            # TODO could have it kill the process, but for now, reset is fine
            if should_reset:
                self.speaker.say(
                    f'No email input for {EmailChess.RESET_TIME_DELTA}, '
                    f'resetting game.'
                )
                return '*2'  # The special code for a game reset


if __name__ == '__main__':
    # TODO is this the best way to have repeating games
    # after the first is finished?
    while True:
        ec = EmailChess()
        ec.play_game()
