import string
import chess


class TextInput():
    # TODO DOC all of this

    def __init__(self, living_board):
        self.living_board = living_board
        self.speaker = living_board.speaker

    @classmethod
    def get_square_name(self, square_int):
        """
        Helper method for turning a square index (1-64)
        into an english name (e4, g7, etc)
        """
        lett = string.ascii_lowercase[chess.square_file(square_int)]
        numb = str(chess.square_rank(square_int) + 1)
        return lett + numb

    def read_board(self, raw):
        """
        Read out each piece still on the board, first white, then black.
        (Iterates through each type, listing out the squares they occupy)
        """
        for player, player_name in [(True, 'Human'), (False, 'Computer')]:
            self.speaker.say(f'For the {player_name} player:')
            for piece_type in range(1, 7):
                sq_set = self.living_board.board.pieces(piece_type, player)

                piece_name = self.living_board.piece_names[piece_type]

                if len(sq_set) > 0:
                    readable_sqs = [self.get_square_name(s) for s in sq_set]
                    self.speaker.say(f'{piece_name}s: {readable_sqs}')

    def reset_game(self, raw):
        """
        Start the game over
        """
        self.speaker.say(f'Resetting game...')
        self.living_board.reset()
        self.speaker.say(self.living_board.board, voiced=False)

    def load_current(self, raw):
        """
        Load the most recent move (if, for example, the last game was quit,
        error'd out, etc). If ended on white's turn, loads to white's turn.
        Also useful to print out current board
        """
        self.living_board.load_fen(previous=0)
        self.speaker.say(f'Loading saved board...')
        self.speaker.say(self.living_board.board, voiced=False)

    def load_past(self, raw):
        """
        Load the previous move, i.e. undoes the past 2 moves. Thus if white
        opened, black responded, then white hits undo, we go back the start
        of the game, both white's and black's move being rolled back.
        """
        self.living_board.load_fen(previous=2)
        self.speaker.say(f'Loading previous board...')
        self.speaker.say(self.living_board.board, voiced=False)

    def load_fen(self, raw):
        """
        Given a text fen, set the board (more useful for text-in, not possible
        with just numpad)
        """
        fen = raw[2:]
        self.living_board.load_fen(fen)
        self.speaker.say(f'Setting special board...')
        self.speaker.say(self.living_board.board, voiced=False)

    def show_board(self, raw):
        self.speaker.say(f'Showing board...')
        self.speaker.say(self.living_board.board.fen(), voiced=False)
        self.speaker.say(self.living_board.board, voiced=False)

    def resign(self, raw):
        self.living_board.resign(is_ai=False)
        # Give the null move UCI to advance the game (to the end)
        return '0000'

    def accept_draw(self, raw):
        self.living_board.accept_draw()
        # Give the null move UCI to advance the game (to the end)
        return '0000'

    def run_code(self, raw):
        """
        Given the raw input started with the special 'this is a code'
        character, activate the special behavior requested

        Returns a UCI to pass back to the actual game (if any)
        """
        # TODO need to think about code flow. How do we let the engine know
        # the difference between an 'outside game' code like draw board
        # versus an 'inside game' code like 'resign'
        code = raw[1]

        codes = {
            '1': self.read_board,
            '2': self.reset_game,
            '3': self.load_past,
            '4': self.load_current,
            '5': self.show_board,
            '7': self.resign,
            '8': self.accept_draw,
            '9': self.load_fen
        }

        if code not in codes:
            self.speaker.say(f'Invalid code: {raw}')
        else:
            return codes[code](raw)

    def to_uci(self, i):
        """
        Take text input which could be UCI or digits, and
        return only UCI. Return None if it is not valid
        """
        i = i.lower()
        if len(i) not in {4, 5}:
            return None

        is_uci = ((i[1] + i[3]).isdigit() and
                  (i[0] + i[2]).isalpha())
        if is_uci:
            return i

        # Because chess UCI looks like 'a1e4', we turn half the digits
        # to the corisponding letter to turn 4 digits to UCI
        def n_to_uci(nums, i):
            n = nums[i]
            if i % 2 != 0:
                return str(n)
            if i == 4:
                # For when we are promoting a peice
                piece_name = self.living_board.piece_names.get(n)
                piece_char = piece_name[0]
                return piece_char
            return string.ascii_lowercase[n - 1]

        if i.isdigit():
            # 0000 is 'pass my turn'
            if i == '0000':
                return i

            # Assuming we only have digit character at this point,
            # turn each digit to an int
            nums = [int(c) for c in i]
            uci = [n_to_uci(nums, i) for i in range(len(nums))]
            uci = ''.join(uci)
            print('uci', uci)
            return uci

        return None

    def try_input(self, raw):
        """
        Given a raw input, we return uci to give to the board - if any.
        if the input does not correspond to a normal chess move, it could
        either be a special chess-cube code (which is promptly performed),
        or that the input was errored (in which case the speaker says so).
        In some cases, the chess-cube codes also return uci,
        which is is returned.
        """

        if raw.startswith('*'):
            return self.run_code(raw)

        inp = self.to_uci(raw)
        if inp is None:
            inp_help = (
                f'"{inp}" should be UCI (eg, "a2b3") '
                f'or 4 digits (eg "1223"). '
                f'For promotion, uci of h7h8q becomes 87886'
            )
            self.speaker.say(inp_help, voiced=False)

            # TODO more useful speech
            spaced_raw = ' '.join(r for r in raw)
            self.speaker.say(f'INVALID: {spaced_raw}')
            return None

        return inp

    def get_input_func(self):
        """
        Returns a function that can be called to get the human move.
        (this method is overridden in subclasses)
        """

        # Taking in digits from the (for now) keypad
        def text_input():
            while True:
                raw = input('Enter move: ')
                print('Raw', raw)

                res = self.try_input(raw)
                if res is not None:
                    return res

        return text_input
