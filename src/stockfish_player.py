import random as rand
import os
from datetime import timedelta

from chess.engine import Limit, SimpleEngine, Cp

from player import Player
import save_file


class StockfishPlayer(Player):
    """
    An AI which gets it's moves from the stock-fish engine
    """

    # Only load the stockfish engine once it is actually needed
    stockfish = None

    def __init__(self, difficulty=None, turn_time=timedelta(seconds=10)):
        """
        Creates a stockfish AI chess player.
        The AI difficulty is modulated by limiting stockfish's intelligence
        (difficulty is float [0-1], roughly what % of it's brain it can to use)
        The amount of time stockfish can spend
        thinking on a turn is limited to the given turn_time (default 10)
        """
        self.turn_time = turn_time

        # If we were given a difficulty, use that
        if difficulty is not None:
            self.difficulty = difficulty
        # Otherwise, load it from file (default of .5)
        else:
            self.difficulty = save_file.load()['difficulty']

    def get_stockfish(self):
        """
        Load the stockfish engine from an asset file
        (searches for any file that starts with stockfish_10)
        """
        prefixed = [filename for filename in os.listdir('assets')
                    if filename.startswith('stockfish_10')]

        if len(prefixed) == 0:
            raise ValueError('Stockfish engine file not found. Download '
                             '"stockfish_10_x64", or whichever archatecture '
                             'version suits the platform.')
        if len(prefixed) > 1:
            raise ValueError(f'Found multiple possible stockfish files: '
                             f'{prefixed}. Change prefix on (or remove) '
                             f'unwated files.')

        stock_file = f'assets/{prefixed[0]}'
        return SimpleEngine.popen_uci(stock_file)

    def get_move(self):
        """
        Assign all possible moves a score, then choose
        one that this difficulty level of stockfish thinks
        is 'good enough'. Also, can choose to resign.
        """
        moves = self.get_sorted_moves()
        if self.should_resign(moves):
            return '*resign'
        return self.choose_move(moves).uci()

    def get_sorted_moves(self):
        """
        Return a list of all the moves, as rated by
        stockfish's score (in centipawns)
        """

        # How long we can to spend thinking about the possible moves this turn
        turn_time = self.turn_time.seconds

        # First move is more open, and we want immediate feedback, so
        # limit time spent thinking about the first move
        # TODO bit sloppy, and maybe not what we want
        if self.referee.board.fullmove_number <= 1 and turn_time > 5:
            turn_time = 5

        move_time = turn_time / len(list(self.referee.board.legal_moves))

        # Get the score for each move, add to list as tuple for easy sorting
        # (We use enumeration just as a tiebreaker, could use a specific
        # tiebreaker class instance, but this works for now)
        moves_with_score = sorted([
            (self.get_move_score(m, move_time), i, m)
            for i, m in enumerate(self.referee.board.legal_moves)
        ], reverse=False)
        moves = [move for score, idx, move in moves_with_score]
        return moves

    def get_move_score(self, move, move_time=1):
        """
        Return stockfish's score for a move (in centipawns)
        """
        b = self.referee.board.copy()
        b.push(move)

        # Only load when we need it (once the game has started)
        # because it spawns new threads
        if self.stockfish is None:
            self.stockfish = self.get_stockfish()

        info = self.stockfish.analyse(
            b, Limit(time=move_time)
        )
        return info['score'].relative

    def should_resign(self, move_list):
        """
        Have ai decide if it wishes to resign or offer a draw,
        returning true if it wishes to resign
        """
        # If the best move is still pretty bad, then resign
        best_move = move_list[0]
        move_score = self.get_move_score(best_move)
        # TODO may still need to fine tune
        if move_score > Cp(2000):
            return True
        return False

    def choose_move(self, move_list):
        """
        Given the sorted list of possible moves, choose one 'organically'
        (by randomly sampling according to the difficulty)
        """
        # TODO ideally we would choose with some sort of linear or bell curve
        # determined from the difficulty, but for now:
        # randomly choose from the x% of moves, where %x is 1 - difficulty
        # (e.g., 1 difficulty chooses best move, .5 difficulty,
        # chooses randomly from the top half of moves, etc)
        limit = len(move_list) * (1 - self.difficulty)
        limit = int(limit)
        limit = max(limit, 1)
        return rand.choice(move_list[:limit])

    def hear_move(self, move):
        """
        Stockfish get's info about board directly from referee,
        doesn't care about opponent's move
        """
        return

    def hear(sefl, s):
        return

    def win(self):
        """
        TODO when saving difficulty, win causes decrease
        """
        self.difficulty -= 0.02
        self.difficulty = max(self.difficulty, 0)
        self.quit()

    def lose(self):
        """
        TODO when saving difficulty, lose causes increase
        """
        self.difficulty += 0.02
        self.difficulty = min(self.difficulty, 1)
        self.quit()

    def draw(self):
        """
        Because there was a draw, difficulty does not change
        """
        self.quit()

    def quit(self):
        """
        Need to kill the stockfish thread to allow the script to exit,
        as well as saving any changes to difficulty
        """
        self.stockfish.quit()
        self.stockfish = None
        self.save()

    def save(self):
        """
        Save any changes in difficulty to the yaml save file
        """
        dikt = save_file.load()
        dikt['difficulty'] = self.difficulty
        save_file.save(dikt)
