import chess  # python-chess chess board management

from code_checker import CodeChecker
from parser import UCIParser



class Referee():
    """
    This class manages the actual board (submitting moves, resetting game, determining winner, etc)
    It represents the heart of the program, but remains agnostic of who the players are (ai or human)
    """

    # Gives us a boolean we can set to false if we want the games to stop
    running = True

    def __init__(self, white_player, black_player):
        """
        Given the two players for this set of games, initialize the
        referee to be able to play continual chess games when 'run' is called
        """
        self.white_player = white_player
        self.black_player = black_player

        self.white_player.prep(self, 'white')
        self.black_player.prep(self, 'black')

        # Allows us to check for special codes (reset, load, etc)
        self.code_checker = CodeChecker(self)
        # Allows us to translate UCI to english
        self.parser = UCIParser(self)

    def play_game(self):
        """
        Play a single game of chess, when the game ends,
        informing both the winner and looser of their status
        TODO is that what we should return?
        """
        self.board = chess.Board()
        while self.running and not self.board.is_game_over():
            move = self.get_move()
            self.board.push(move)
            self.active_player().hear_move(move)

        # TODO who wins if game was called (self.running set to false)? Draw?

        result = self.board.result()

        if result == '1-0': # If white player won
            self.white_player.win()
            self.black_player.lose()
        elif result == '0-1': # if black player won
            self.white_player.lose()
            self.black_player.win()
        elif result == '1/2-1/2': # If there was a draw
            self.black_player.draw()
            self.white_player.draw()
        else:
            raise ValueError(f'Unknown game end: "{result}"\n{self.board}\n\n{self.board.fen()}')

    def get_move(self):
        """
        TODO DOC
        """
        while True:
            raw = self.active_player().get_move()

            try:
                if self.is_code(raw):
                    # If the code returns a suggested next input, then we will submit that
                    move_str = self.run_code(raw)
                    if move_str is not None:
                        return self.to_move(move_str)

                elif self.is_move(raw):
                    return self.to_move(raw)

                else:
                    # TODO could add more info
                    self.active_player().hear(f'Illegal "{raw}"')

            except ValueError as e:
                self.active_player().hear(f'Invalid "{raw}": {e}')


    def active_player(self):
        """
        Return the player obj for whomever's turn it is
        """
        if self.board.turn == chess.WHITE:
            return self.white_player
        elif self.board.turn == chess.BLACK:
            return self.black_player
        raise ValueError(f'Turn was not white or black {self.board.turn} [{chess.WHITE}, {chess.BLACK}]')

    def to_move(self, move_str):
        """
        Given a UCI move string, return the python-chess move object
        """
        return chess.Move.from_uci(move_str)

    def is_move(self, move_str):
        """
        A curtsey's function this referee provides to players,
        allowing them to check if their move is a valid chess move
        (thus allowing them to, say, ask for re-input if it is not).
        Note: the move str should be a UCI move string
        """
        # TODO should really have it return a string if there is a problem,
        # to differentiate between invalid and illegal
        try:
            moves =  list(self.board.legal_moves) + [chess.Move.null()]
            return True if self.to_move(move_str) in moves else False
        except ValueError:
            return False

    def is_code(self, code_str):
        """
        Some inputs are not chess moves, but rather special codes
        (like loading a saved board, resigning etc). Similar to 'is_move',
        allows inputs to check their moves to see if their are special codes
        """
        return self.code_checker.check(code_str)

    def run_code(self, code_str):
        """
        Run a code (loading saved board, resigning, etc) on the code checker,
        returning the next recommended move (or None)
        """
        return self.code_checker.run(code_str)

    def opponent(self, player=None):
        """
        Return the other player
        (either the opponent of the given player,
        or the opponent of the active player)
        """
        if player is None:
            player = self.active_player()

        if player is self.white_player:
            return self.black_player
        elif player is self.black_player:
            return self.white_player
        else:
            raise ValueError(f'{player} was not black ({self.black_player}) nor white ({self.white_player})')
