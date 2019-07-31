#!/usr/bin/python3.7
import random as rand
import string
import os

from stockfish import Stockfish  # Stockfish chess engine for the chess ai
import chess  # python-chess chess board manedgement
import yaml  # To read the 'save file' of difficulty progress

from speaker import Speaker


# TODO CLEANUP
SAVE_FILE_NAME = 'save.yaml'


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

    # Get the difficulty from the save data, starting with a default of,
    # idk, say 30% stockfish, 70% random moves
    # TODO use a nested for save data that has its own save/load
    difficulty = SAVE_DATA.get('difficulty', .3)

    def __init__(self, get_move_func=None):
        # Initilize stockfish chess AI for computer moves
        self.stockfish = self.get_stockfish()

        # Initlize python-chess playing board
        self.board = chess.Board()

        # Holdss logic for speaking moves, greetings, etc
        self.speaker = Speaker()

        # Say howdy
        self.speaker.say_greeting()

        # TODO DOC
        self.get_human_move = get_move_func
        if self.get_human_move is None:
            self.get_human_move = self.get_move

    def get_stockfish(self):
        prefixed = [filename for filename in os.listdir('.')
                    if filename.startswith('stockfish_10')]

        if len(prefixed) == 0:
            raise ValueError('Stockfish engine file not found. Download '
                             '"stockfish_10_x64", or whichever archatecture '
                             'version suits the platform.')
        if len(prefixed) > 1:
            raise ValueError(f'Found multiple possible stockfish files: '
                             f'{prefixed}. Change prefix on (or remove) '
                             f'unwated files.')

        stock_file = f'./{prefixed[0]}'
        return Stockfish(stock_file)

    def get_move(self):
        # Flip a coin based on difficulty level, either returning a random move
        # or stockfishes best move
        self.speaker.say_thinking()
        if rand.random() < self.difficulty:
            return self.stockfish.get_best_move()
        moves = [m.uci() for m in self.board.legal_moves]
        return rand.choice(moves)

    def play_move(self):
        """
        If a uci move is given, play that move, otherwise, generate your own
        move using get_move.
        A move is added to the board, turn advancing and all that.
        """
        if not self.is_human_turn():
            move = self.get_move()
            self.speaker.say_move(move)
        else:
            move = self.get_human_move()
            self.speaker.say_response(move)

        if move is None:
            raise ValueError('It is the human turn, please enter a move')

        # Apply move to board and to stockfish
        self.board.push_uci(move)
        self.stockfish.set_fen_position(self.board.fen())

    def is_over(self):
        # Returns true if there is a checkmate, draw, or other game over
        return self.board.is_game_over()

    def is_human_turn(self):
        return not self.board.turn

    def play_game(self):
        """
        Play a game of chess, where 'get_move_func' is a function that retuns
        the human player input in UCI format.
        TODO add special returns from input, such as resetting game, etc
        """
        while not self.is_over():
            self.play_move()

        # Depending on the outcome, we have different ending functs to call
        res_dict = {
            '0-1': self.loose_game,
            '1-0': self.win_game,
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
        self.difficulty += 0.02
        self.difficulty = min(1, self.difficulty)
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
        self.difficulty -= 0.02
        self.difficulty = max(0, self.difficulty)
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
        data = {
            'difficulty': self.difficulty
        }
        with open(SAVE_FILE_NAME, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)


if __name__ == '__main__':
    def text_input():
        # Function that we are using (for now) to get the human move

        # Taking in digits from the (for now) keypad
        while True:
            inp = input('Enter move: ')
            print('Raw', inp)

            if len(inp) != 4 or not inp.isdigit():
                print(f'"{inp}" should be 4 digits')
                continue

            # 0000 is 'pass my turn'
            if inp == '0000':
                return inp

            # Assuming we only have digit character at this point,
            # turn each digit to an int
            nums = [int(c) for c in inp]

            # Because chess UCI looks like 'a1e4', we turn half the digits
            # to the corisponding letter
            def n_to_uci(nums, i):
                n = nums[i]
                if i % 2 != 0:
                    return str(n)
                return string.ascii_lowercase[n]

            uci = [n_to_uci(nums, i) for i in range(4)]
            uci = ''.join(uci)
            print('uci', uci)
            return uci

    # TODO add human input to init
    lb = LivingBoard(text_input)
    lb.play_game()
