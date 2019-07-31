from gtts import gTTS  # Google text to speech for the computer player speech
import subprocess  # Python os for playing google speech mp3s


class Speaker():
    """
    Used to perform the reporting of the computer moves, as well as banter
    like announcing wins, saying hello, etc. Is, for now, writing to
    terminal and using google text-to-speech, but in the future
    could add lights, mtion, etc
    """

    # TODO return to true, off for speed testing
    voiced = False

    def say_greeting(self):
        self.say('Let the game begin.')

    def say_thinking(self):
        pass

    def say_response(self, move):
        print('human move:', move)

    def say_loose(self):
        # Utter a phrase upon compuer losing a game
        self.say('You win')

    def say_win(self):
        # Utter a phrase upon computer winning a game
        self.say('I win')

    def say_draw(self):
        self.say('Draw!')

    def say_move(self, move):
        # Turn the chess UCI format to something that sounds better
        # (Google says the move better if we space it out)
        # TODO might not want to use uci here, migjt want to use
        # more plain english
        say_move = move[:2] + ' to ' + move[2:]
        self.say(say_move)

    def say(self, s, slow=False):
        """
        Take in a string s and communicate that phrase to the user. Can be
        through printed text, voice, displaying on screen, anything.
        Current: print out and audio speech
        """
        print(s)

        if self.voiced:
            speech = gTTS(text=s, lang='en', slow=slow)
            # TODO could cache
            file_name = 'speech/s.mp3'
            speech.save(file_name)
            cmd = ['mpg123', '-q', file_name]
            subprocess.Popen(cmd)
