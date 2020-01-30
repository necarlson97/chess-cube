import yaml

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
            'turns': self.show_turns,
            'load': self.load_board,
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
        return s.startswith('*')

    def run(self, s):
        """
        Given a raw input (that is a code), find the
        code it references and run that code (with the remainder of the string).
        Return the result (a suggested next move, if there is one, or none if
        the player should provide their own next move)
        """
        if not s.startswith('*'):
            raise ValueError(f'Code must start with *: {s}')
        # Get the first 'word' (and remove the *)
        code_name, sep, code_remainder = s[1:].partition(' ')

        try:
            code_int = int(code_name)
            code_func = list(self.codes.values())[code_int]
        except:
            if code_name not in self.codes:
                raise ValueError(f'Could not find given code {code_name} in codes: {list(self.codes.keys())}')
            code_func = self.codes[code_name]

        return code_func(code_remainder)

    def help(self, code_str=None):
        """
        List the available codes
        """
        s = 'Chess moves are inputted as UCI. Special codes are inputted starting with an asterisk "*".'
        s += 'Codes Available:\n'
        for i, code_name in enumerate(self.codes.keys()):
            desc = self.code_descriptions.get(code_name, 'Missing description')
            s += f'  (*{i}) *{code_name} - {desc}\n'

        self.referee.active_player().hear(s)

    def show_board(self, code_str=None):
        """
        Show the current board state (in ascii art string)
        to the active player
        """
        self.referee.active_player().hear(self.referee.board)

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
        return self.show_board()

    def show_turns(self, code_str):
        """
        Show previous boards stored in memory
        """
        raise NotImpelemtedError()

    def load_board(self, code_str):
        """
        Load a previous board from memory
        """
        raise NotImpelemtedError()
