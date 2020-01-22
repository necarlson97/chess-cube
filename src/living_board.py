import random as rand
import os

import chess  # python-chess chess board management
from chess.engine import Limit, SimpleEngine, Cp
import yaml  # To read the 'save file' of difficulty progress

from speaker import Speaker


# TODO CLEANUP
SAVE_FILE_NAME = 'assets/save.yaml'


def read_save_file():
    # Read in the save data yaml, returning it as a dict (if it exists),
    # and returning an empty dict otherwise
    try:
        with open(SAVE_FILE_NAME, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError) as e:
        print('Save data not recovered:', e)

    return {}


# Get save data from yaml file
SAVE_DATA = read_save_file()


class LivingBoard():
    # TODO time to split into multiple files...

    # TODO add to save file the last fen or whatever nad then have an input
    # that will reload last save (if mistaken input, or restart killed game)

    # Get the difficulty from the save data, starting with a default of,
    # idk, say 30% stockfish, 70% random moves
    # TODO use a nested for save data that has its own save/load
    save_data = SAVE_DATA

    # Dict of piece types to their names, used better describe names in
    # english, and also for some inputs
    piece_names = {
        1: 'pawn',
        2: 'knight',
        3: 'bishop',
        4: 'rook',
        5: 'queen',
        6: 'king'
    }

    seconds_per_move = 10

    def __init__(self, get_move_func=None, quiet=False, speaker=None):
        # Initilize stockfish chess AI for computer moves
        self.stockfish = self.get_stockfish()

        # Initlize python-chess playing board
        self.board = chess.Board()
        self.commit_fen()

        # Holds logic for speaking moves, greetings, etc
        if speaker is None:
            self.speaker = Speaker(self, quiet=quiet)
        else:
            self.speaker = speaker
        self.speaker.living_board = self

        # Say howdy
        self.speaker.say_greeting()

        self.save_data.setdefault('difficulty', .3)

        # TODO DOC
        if get_move_func is not None:
            self.get_human_move_uci = get_move_func
        else:
            self.get_human_move_uci = self.get_ai_move_uci

    def get_stockfish(self):
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

    def load_fen(self, fen=None, previous=0):
        """
        Load into the board a given fen, or a previous fen from the list
        saved in the file
        """
        if fen is None:
            fen = self.save_data.get('fens')[previous]
        self.commit_fen(fen, save=False)

    def uci_to_move(self, uci):
        # TODO ERROR CHECKING
        # TODO REMOVE TESTING
        return chess.Move.from_uci(uci)

    def accept_draw(self):
        """
        Player can trigger this function to accept a draw if the ai
        offered it the previous turn
        """
        # For now, the AI never offers draws, so they cannot be accepted
        if True:
            self.speaker.say('NO DRAW OFFERED')
        else:
            # This signifies that the game is over and ends in a draw
            # TODO do something better
            self.board.clear()

    def resign(self, is_ai=True):
        if is_ai:
            self.speaker.say('RESIGNING')
            last_piece = 'K'
        else:
            self.speaker.say('YOU RESIGNED')
            last_piece = 'k'
        # We need to set a move that ends the game and assigns a win to
        # whomever, so for now, we just have a single king for the winner
        self.board.set_fen(f'8/8/8/8/8/8/8/{last_piece}7 w - -')

    def get_move_score(self, move, move_time=1):
        """
        Helper method to return the engine's score
        """
        b = self.board.copy()
        b.push(move)
        info = self.stockfish.analyse(
            b, Limit(time=move_time)
        )
        return info['score'].relative

    def get_sorted_moves(self):
        """
        Return a list of all the moves, as rated by their score to the
        ai player
        """
        # Helper method, return stockfish's score for each of the moves it
        # could make
        # (We allow the ai to think for ten seconds, so the time spent on each
        # possible moves depends on the # of possible moves)
        move_time = self.seconds_per_move / len(list(self.board.legal_moves))

        # Get the score for each move, add to list as tuple for easy sorting
        # (We use enumeration just as a tiebreaker, could use a specific
        # tiebreaker class instance, but this works for now)
        moves_with_score = sorted([
            (self.get_move_score(m, move_time), i, m)
            for i, m in enumerate(self.board.legal_moves)
        ], reverse=False)
        moves = [move for score, idx, move in moves_with_score]
        return moves

    def ponder_resignation(self, move_list):
        """
        Have ai decide if it wishes to resign or offer a draw
        """
        # The engine seems to have the ability to do this,
        # the code looks something like:
        # res = self.stockfish.play(
        #     self.board.copy(), Limit(time=0.1)
        # )
        # if res.draw_offered:
        #     self.speaker.say("OFFERING DRAW")
        # if res.resigned:
        #     self.resign()
        #     return
        # However, I was not seeing it in practice,
        # so for now, I will use this:

        # TODO could also think of custom logic for offering a draw
        best_move = move_list[0]
        move_score = self.get_move_score(best_move)
        # If the best move is still worse than a pretty awful move
        # TODO need to fine tune. Even with very few moves it still wont
        # resign. Weirdly, when it just has a king roaming around it
        # still thinks it is has advantage on mate. Try flipping?
        print('move score', move_score)
        if move_score > Cp(2000):
            self.resign()
            return True

    def choose_from_moves(self, move_list):
        """
        Given the sorted list of possible moves, choose one 'organically'
        (by randomly sampling according to the difficulty)
        """
        # TODO ideally we would choose with some sort of linear or bell curve
        # determined from the difficulty, but for now:
        # randomly choose from the x% of moves, where %x is 1 - difficulty
        # (e.g., 1 difficulty chooses best move, .5 difficulty,
        # chooses randomly from the top half of moves, etc)
        diff = self.save_data['difficulty']
        limit = len(move_list) * (1 - diff)
        limit = int(limit)
        limit = max(limit, 1)
        return rand.choice(move_list[:limit])

    def get_ai_move_uci(self):
        """
        For each possible move, have the stockfish test it,
        and assign a score. Once we have this ordered list of moves,
        randomly sample from it according to the difficulty
        (1 = will choose best move, 0 = totally random).
        Return the UCI of that move.
        (Can also resign)
        """
        self.speaker.say_thinking()

        choices = self.get_sorted_moves()

        # If the ai chooses to resign, simply return the null move
        if self.ponder_resignation(choices):
            return '0000'

        return self.choose_from_moves(choices).uci()

    def get_human_move(self):
        while True:
            try:
                move = self.uci_to_move(self.get_human_move_uci())
                # If move is good (or is a null move), we are done, return it
                if move in self.board.legal_moves or not move:
                    return move

                # Otherwise, move was illegal, read uci back to user
                uci = move.uci()
                self.speaker.say(f'ILLEGAL: {uci[:2]} to {uci[2:]}')
            except ValueError as e:
                # IF pthon-chess threw error, saw error
                # TODO more clear speech
                self.speaker.say(f'ERROR: {e}')

    def get_ai_move(self):
        return self.uci_to_move(self.get_ai_move_uci())

    def play_move(self):
        """
        If a uci move is given, play that move, otherwise, generate your own
        move using get_move.
        A move is added to the board, turn advancing and all that.
        """

        if self.is_human_turn():
            move = self.get_human_move()
            self.speaker.say_human_move(move)
        else:
            move = self.get_ai_move()
            self.speaker.say_ai_move(move)

        if move is None:
            raise ValueError('It is the human turn, please enter a move')

        # Apply move
        self.commit_move(move)

        # TODO could (with some fuckery) add to speaker english method
        if self.board.is_checkmate():
            self.speaker.say('Checkmate')
        if self.board.is_stalemate():
            self.speaker.say('Stalemate')

    def commit_move(self, move):
        """
        Ai or Human move has been confirmed, add to python chess board,
        to stockfish, and to the save file which allows rollbacks (and loaded
        saves)
        """
        self.board.push(move)
        self.commit_fen()

    def commit_fen(self, fen=None, save=True):
        # TODO can make board setting a param if it is slow
        if fen is None:
            fen = self.board.fen()

        self.board.set_fen(fen)
        if save:
            # Add this fen to the list of previous board states
            self.save_data.setdefault('fens', []).insert(0, fen)

            # Only keep (for now) the past 3 board states
            while len(self.save_data['fens']) > 4:
                self.save_data['fens'].pop()

            self.save()

    def reset(self):
        self.board.reset()
        self.commit_fen()

    def is_over(self):
        # Returns true if there is a checkmate, draw, or other game over
        return self.board.is_game_over()

    def is_human_turn(self):
        return self.board.turn

    def play_game(self):
        """
        Play a game of chess, where 'get_move_func' is a function that retuns
        the human player input in UCI format.
        TODO add special returns from input, such as resetting game, etc
        """
        self.speaker.say('GAME START')
        # If case we call 'play_game' again, for now, just reset board
        self.reset()
        while not self.is_over():
            self.play_move()

        # Depending on the outcome, we have different ending functs to call
        # TODO need to re-doc and rename, they seem backwards currently
        res_dict = {
            '0-1': self.win_game,
            '1-0': self.loose_game,
            '1/2-1/2': self.draw_game,
            '*': self.game_ongoing
        }

        # Check result, call corrisponding func
        res_dict[self.board.result()]()
        self.stockfish.quit()

    def win_game(self):
        """
        When the computer wins the game, we want to:
        1. decrease difficulty
        2. save decrease in difficulty
        3. announce it
        """
        # decrease difficulty, keeping above 0
        self.save_data['difficulty'] -= 0.02
        self.save_data['difficulty'] = max(0, self.save_data['difficulty'])
        self.save()
        self.speaker.say_win()

    def loose_game(self):
        """
        When the computer looses the game, we want to:
        1. increase difficulty
        2. save increase in difficulty
        3. announce it
        """
        # increase difficulty, keeping below 1
        self.save_data['difficulty'] += 0.02
        self.save_data['difficulty'] = min(1, self.save_data['difficulty'])
        self.save()
        self.speaker.say_loose()

    def draw_game(self):
        """
        Announce draw
        """
        self.speaker.say_draw()

    def game_ongoing(self):
        raise ValueError('How did this happen?')

    def save(self):
        # Write a save data dict to the save file
        with open(SAVE_FILE_NAME, 'w') as outfile:
            yaml.dump(self.save_data, outfile, default_flow_style=False)
