import random as rand
import os

from stockfish import Stockfish  # Stockfish chess engine for the chess ai
import chess  # python-chess chess board manedgement
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
        return Stockfish(stock_file)

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

    def get_ai_move_uci(self):
        # Flip a coin based on difficulty level, either returning a random move
        # or stockfishes best move
        self.speaker.say_thinking()
        # TODO have it sample from the ordered list of best moves
        if rand.random() < self.save_data['difficulty']:
            return self.stockfish.get_best_move()
        moves = [m.uci() for m in self.board.legal_moves]
        return rand.choice(moves)

    def get_human_move(self):
        while True:
            try:
                move = self.uci_to_move(self.get_human_move_uci())
                # If move is good, we are done, return it
                if move in self.board.legal_moves:
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
        self.stockfish.set_fen_position(fen)

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
        while not self.is_over():
            self.play_move()

        # Depending on the outcome, we have different ending functs to call
        res_dict = {
            '0-1': self.win_game,
            '1-0': self.loose_game,
            '1/2-1/2': self.draw_game,
            '*': self.game_ongoing
        }

        # Check result, call corrisponding func
        res_dict[self.board.result()]()

    def win_game(self):
        """
        WHen the computer wins the game, we want to:
        1. increase difficulty
        2. save increase in difficulty
        3. announce it
        """
        # Increase difficulty, keeping below 1
        self.save_data['difficulty'] += 0.02
        self.save_data['difficulty'] = min(1, self.save_data['difficulty'])
        self.save()
        self.speaker.say_win()

    def loose_game(self):
        """
        WHen the computer looses the game, we want to:
        1. decrease difficulty
        2. save decrease in difficulty
        3. announce it
        """
        # decrease difficulty, keeping above 0
        self.save_data['difficulty'] -= 0.02
        self.save_data['difficulty'] = max(0, self.save_data['difficulty'])
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
