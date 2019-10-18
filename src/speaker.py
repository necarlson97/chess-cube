from gtts import gTTS  # Google text to speech for the computer player speech
import pyttsx3  # Another text to speech engine that offers more voices
import subprocess  # Python os for playing google speech mp3s


class Speaker():
    """
    Used to perform the reporting of the computer moves, as well as banter
    like announcing wins, saying hello, etc. Is, for now, writing to
    terminal and using text-to-speech, but in the future
    could add lights, mtion, etc
    """

    # TODO return to true, off for speed testing
    voiced = True

    rate = 150  # Good place to leave = 150
    volume = 1  # Quiet, just for podcast listening lol

    pytts = pyttsx3.init()

    def __init__(self, living_board=None, quiet=False):
        self.living_board = living_board
        if living_board is not None:
            living_board.speaker = self

        self.pytts.setProperty('rate', self.rate)
        self.pytts.setProperty('volume', self.volume)

        # Set the vocie function (currently using pytts rather than google tts)
        self.voice_func = self.pytts_say

        self.voiced = not quiet

    def say_greeting(self):
        pass

    def say_thinking(self):
        pass

    def say_ai_move(self, move):
        # TODO what do we do for null move?
        if not move:
            return
        self.say('RESPONSE: ', end='')
        self.say_move(move)

    def say_human_move(self, move):
        # TODO what do we do for null move?
        if not move:
            return
        self.say(f'   INPUT: ', end='')
        self.say_move(move)

    def move_to_english_str(self, move):
        """
        Given a move, return the 'best' we can do in english.
        Here are some examples of a priority format
        attacking = Pawn take rook
        unique move = Pawn to a3
        uci = a2 to a3
        """
        # If null move is given:
        if not move:
            return 'null move'

        if self.living_board is None:
            raise ValueError(
                'Cannot translate, as '
                'speaker has no associated board')
        board = self.living_board.board

        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)

        piece_names = self.living_board.piece_names

        from_piece_name = piece_names.get(from_piece.piece_type)
        to_piece_name = (None if to_piece is None
                         else piece_names.get(to_piece.piece_type))

        # What we will actually call the names when we say them
        # (default is the piece name, but dependent on ambiguity)
        to_piece_alias = to_piece_name
        from_piece_alias = from_piece_name

        uci = move.uci()
        from_square_name = uci[:2]
        to_square_name = uci[2:]

        # Check if this attacker could be confused for another of the
        # same type
        def is_ambigious(attacking, from_square=None, to_square=None, limit=1):
            # By default, use this moves squares.
            # However, can set as a param, as func is also
            # useful for finding if there is a simmilar capture
            # (e.g. 'Can a pawn take a knight anwhere else on this board?')
            if from_square is None:
                from_square = move.from_square
            if to_square is None:
                to_square = move.to_square

            if attacking:

                # TODO is this always true?
                # Because pawns don't attack the same way they move, their
                # attacking squares are not in contest with their move,
                # unless they are moving diagonal
                is_pawn = board.piece_type_at(from_square) == 1
                no_victim = board.piece_at(to_square) is None
                if is_pawn and no_victim:
                    return False

                origin_square = from_square
                square_set = board.attackers(board.turn, to_square)
            else:

                # TODO use python-chess 'is_attacking'?
                # If we do not have a victim, we must specify to_square
                if board.piece_at(to_square) is None:
                    return True

                origin_square = to_square
                square_set = board.attacks(from_square)

            origin_p_type = board.piece_type_at(origin_square)

            for square in square_set:
                p_type = board.piece_type_at(square)
                p_color = board.color_at(square)
                # Ambigious if the piece type is the same and either:
                # We are attacking, and the attacker mataches my color
                # We are a victim, and the other victim matches my color
                matching_piece = (
                    p_type == origin_p_type and
                    p_color == (board.turn == attacking)
                )
                if square != origin_square and matching_piece:
                    return True
            return False

        # Determine if this is attack , or regular move
        # TODO gross logic
        verb = 'to'
        if board.is_capture(move):
            verb = 'takes'
        if move.promotion is not None:
            verb = 'promotion to'
            to_piece_alias = piece_names.get(move.promotion)

        # Determine if the 'from piece' is ambigious
        # (because multiple peices of the same type could make this move)
        dupe_attackers = is_ambigious(attacking=True)
        if dupe_attackers:
            from_piece_alias = from_square_name

        # Determine if the 'from piece' is ambigious  (or nothing is there)
        # (because this peice can choose from several victims of the same type)
        dupe_victims = is_ambigious(attacking=False)
        if dupe_victims:
            to_piece_alias = to_square_name

        # Can still be ambigious if there are unrelated captures
        # by the same name elsewhere
        # TODO how best to do this fast?
        def dupe_capture():
            # Cannot be a dupe capture if this move is not a capture!
            if to_piece is None:
                return False

            # If we have already solved ambiguity, return false
            still_named = (
                to_piece_alias == to_piece_name and
                from_piece_alias == from_piece_name
            )
            if not still_named:
                return False

            matching_victims = [
                sq for sq in board.pieces(to_piece.piece_type, not board.turn)
                if sq != move.to_square
            ]
            for sq in matching_victims:
                # If there is an unrelated matching capture,
                # do we change from or to?
                dupe_capture = is_ambigious(attacking=True, to_square=sq)
                if dupe_capture:
                    return True

        dupe_capture = dupe_capture()
        if dupe_capture:
            from_piece_alias = from_square_name

        # TODO check color for this
        # TODO 'move.drop' gives the drop type - is this useful?

        s = f'{from_piece_alias} {verb} {to_piece_alias}'

        if board.is_en_passant(move):
            s += ' - pawn taken in passing'

        if board.is_castling(move):
            s += ' - castling'

        if board.is_into_check(move):
            s += ' - check'

        return s

    def say_move(self, move):
        """
        Turn the chess UCI format to something that sounds better
        (Google says the move better if we space it out)
        TODO might not want to use uci here, migjt want to use
        more plain english
        """
        self.say(self.move_to_english_str(move))

    def say(self, s, wait=False, slow=False, end=None, voiced=True):
        """
        Take in a string s and communicate that phrase to the user. Can be
        through printed text, voice, displaying on screen, anything.
        Current: print out and audio speech
        """
        print(s, end=end)

        # If we were told to voice this string, and voicing has not been
        # disabled globally for this instance
        if voiced and self.voiced:
            self.voice_func(s, wait, slow)

    def pytts_say(self, s, wait=False, slow=False):
        # Use pytts to create audio

        # TODO currently 'slow' and 'wait' not supported

        self.pytts.say(s)
        self.pytts.runAndWait()

    def google_say(self, s, wait=False, slow=False):
        # Use google text to speech to create audio
        speech = gTTS(text=s, lang='en', slow=slow)
        # TODO could cache
        file_name = 'speech/s.mp3'
        speech.save(file_name)
        cmd = ['mpg123', '-q', file_name]
        if wait:
            subprocess.run(cmd)
        else:
            subprocess.Popen(cmd)

    def say_loose(self):
        # Utter a phrase upon compuer losing a game
        self.say('GAME OVER. YOU WIN.')

    def say_win(self):
        # Utter a phrase upon computer winning a game
        self.say('GAME OVER. I WIN.')

    def say_draw(self):
        self.say('GAME OVER. DRAW.')

    def commit(self):
        """
        Stub function, not used for current vocal, but for some speakers
        (like email) it is useful to store up all the things that need
        to be siad in a turn, then sned them all as a single message
        """
        pass
