import save_file


class CodeChecker():
    """
    Some inputs the referee gets are not chess moves,
    but rather codes that load a saved board, resign, etc.
    This class handles performing those codes
    """

    def __init__(self, referee):
        """
        Set the codes with their corresponding names
        that can be used to call them.
        Note that they can also be called with their index
        (e.g. the first one can be called with *0 as well as *the-name)
        """
        self.referee = referee
        self.codes = {
            'help': self.help,
            'show': self.show_board,
            'fen': self.load_fen,
            'prev': self.load_previous,
            'resign': self.resign,
        }
        self.code_descriptions = {
            'help': 'show this help message',
            'show': 'show ascii art of the board',
            'fen': 'load a given fen',
            'turns': 'show previous turns',
            'load': 'load a previous turn',
            'resign': 'resign, forfeiting the game',
        }

    def check(self, s):
        """
        Check that the given raw string is a code
        """
        # TODO check that the code exists, not just that it has *
        return s is not None and s.startswith('*')

    def get_code_info(self, s):
        """
        Given an input string, return the code name
        e.g.:
        *help -> help
        *1 -> help
        """
        if not s.startswith('*'):
            raise ValueError(f'Code must start with *: {s}')
        # Get the first 'word' (and remove the *)
        code_name, sep, code_remainder = s[1:].partition(' ')

        # If given code name is an index,
        # switch it out for the name at that index
        try:
            # TODO catch number to large and too small errors
            code_int = int(code_name)
            code_name = list(self.codes.keys())[code_int]
        except ValueError:
            pass

        if code_name not in self.codes:
            raise ValueError(f'Could not find given code {code_name} '
                             f'in codes: {list(self.codes.keys())}')

        return code_name, code_remainder

    def run(self, s):
        """
        Given a raw input (that is a code), find the
        code it references and run that code function
        # (with the remainder of the string).
        Return the result (a suggested next move, if there is one, or none if
        the player should provide their own next move)
        """
        code_name, code_remainder = self.get_code_info(s)
        code_func = self.codes[code_name]
        return code_func(code_remainder)

    def hear(self, s):
        """
        Pass a string along to the player who gave the code
        """
        self.referee.active_player().hear(s)

    def help(self, code_str=None):
        """
        List the available codes
        """
        s = ('Chess moves are inputted as UCI. '
             'Special codes are inputted starting with an asterisk "*".\n'
             'Codes Available:\n')

        for i, code_name in enumerate(self.codes.keys()):
            desc = self.code_descriptions.get(code_name, 'Missing description')
            s += f'  (*{i}) *{code_name} - {desc}\n'

        self.hear(s)

    def show_board(self, code_str=None):
        """
        Show the current board state (in ascii art string)
        to the active player
        """
        self.hear(self.referee.board)

    def resign(self, code_str=None):
        """
        Active player resigns, forfeiting the game
        """
        self.referee.opponent().hear('Resigning.')
        # We have to set the fen board to one that wins for
        # the opponent. This dict tells, given a desired winner,
        # how to set the fen pieces
        name_to_fen = {
            'white': '7k/5KQ1/8/8/8/8/8/8 w - - 0 1',
            'black': '7K/5kq1/8/8/8/8/8/8 b - - 0 1',
        }
        name = self.referee.opponent().name

        # Set the board as a clear win for our opponent
        self.referee.board.set_fen(name_to_fen[name])

        # TODO GROSS HACK
        # Because the game doesn't end when it is the opponent's
        # turn, it ends on the turn after. So, the fen forces it to jump
        # to the opponent's turn, and then the 'returned move'
        # is actually given to the opponent

        # Null move to advance turn counter, thus end game
        return '0000'

    def load_fen(self, code_str):
        """
        Load the given fen to the game board
        """
        self.referee.board.set_fen(code_str)
        self.show_board()

    def show_turns(self, code_str):
        """
        Show previous boards stored in memory
        """
        # Board so we can print expected fen load
        board = self.referee.board.copy()

        # Load fens from file
        fens = save_file.load().setdefault('fens', [])
        self.hear('Previously played boards:')
        for i, fen in enumerate(fens):
            board.set_fen(fen)
            player_name = self.referee.active_player(board).name
            # Get string explain that saved fen
            s = f'\n#{i} {player_name}:\n{fen}\n{board}'
            # Add indentation
            s = '\n    '.join(s.split('\n'))
            self.hear(s)
        self.hear('\nTo load one of these, use the prev code.\n'
                  'Eg, to load #5, input: "*prev 5"')

    def load_previous(self, code_str):
        """
        Load a previous board from memory
        """
        if code_str is None or code_str == '':
            return self.show_turns(code_str)

        # Load fens from file
        fens = save_file.load().setdefault('fens', [])
        fen = fens[int(code_str)]
        self.referee.board.set_fen(fen)
        self.show_board()
