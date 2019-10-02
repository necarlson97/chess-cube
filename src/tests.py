import pyttsx3
import chess

from living_board import LivingBoard
from text_input import TextInput


def listen_to_voices():
    # Preview the downloaded voices
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)

    voices = engine.getProperty('voices')
    print(f'Testing {len(voices)} voices')
    for voice in voices:
        if 'english' not in voice.id:
            print('Skipping', voice.id)
            continue

        print(voice)

        engine.setProperty('voice', voice.id)
        engine.say('The quick brown fox jumped over the lazy dog.')
        engine.runAndWait()


def run_game():
    # Run an ai game against itself
    lb = LivingBoard(quiet=True)
    lb.play_game()


def test_english_moves():
    # Test that a move gives the desired english output

    lb = LivingBoard(quiet=True)

    # Moves to test:
    # type take type:
    # Every type to square
    # Ambigious take move
    # Ambigious regular move:

    # Test setup fen:
    fen = '1n5n/B1PPP1B1/1r1rN1N1/P1P5/8/1rb1PQK1/qQn5/1p2BRN1 w - -'
    lb.board.set_fen(fen)

    moves = {
        # W Queen take every type
        'b2a2': 'queen takes queen',  # W Queen take B Queen
        'b2b3': 'queen takes rook',  # W Queen take B Rook
        'b2c3': 'queen takes bishop',  # W Queen take B Bishop
        'b2c2': 'queen takes knight',  # W Queen take B Knight
        'b2b1': 'queen takes pawn',  # W Queen take B Pawn

        # W move every type
        'e1d2': 'bishop to d2',  # W bishop move up left
        'f1f2': 'rook to f2',  # W rook move up
        'g1h3': 'knight to h3',  # W knight move up right
        'e3e4': 'pawn to e4',  # W pawn move up
        'f3f4': 'queen to f4',  # W queen move up
        'g3g4': 'king to g4',  # W king move up

        # 2 W Pawns, either could take B pawn
        'a5b6': 'a5 takes rook',
        # 1 W Pawn, either could take either B pawn
        'c5d6': 'pawn takes d6',

        # Both attackers and attacked are ambibious
        'c5b6': 'c5 takes b6',

        # 2 W Knights, either make same move
        'e6f8': 'e6 to f8',
        'g6f8': 'g6 to f8',

        # Two unrelated w bishops threaten b knights
        'a7b8': 'a7 takes knight',
        'g7h8': 'g7 takes knight',

        # Pawns next to eachover are unique
        'd7d8': 'pawn to d8',
    }

    for inp, exp_out in moves.items():
        move = lb.uci_to_move(inp)
        out = lb.speaker.move_to_english_str(move)
        assert out == exp_out, f'{inp} -> "{out}" != "{exp_out}"'

    # TODO Test to make sure the color types makes sense
    # TODO Test en-passant

    print('Done! test_english_moves passed')


def test_reset_codes():
    # TODO DOC

    lb = LivingBoard(quiet=True)

    moves = []

    ti = TextInput(lb)

    # take an english square (like 'a3') and turn it to a number
    def sq_to_int(sq):
        file = ord(sq[0]) - 97
        rank = int(sq[1]) - 1
        return chess.square(file, rank)

    # Swap out actual human input for our 'test human' input
    def test_move():
        print('State of moves', moves)
        for i in range(2):
            raw = moves.pop(0)
            res = ti.try_input(raw)
            if res is not False:
                return res

    lb.get_human_move_uci = test_move

    # Play a number of moves
    def play_moves(count):
        for i in range(count):  # number of 'actual' moves mode
            lb.play_move()  # Text human plays
            lb.play_move()  # AI responds

    def assert_is_pawn(squares):
        for sq in squares:
            i = sq_to_int(sq)
            pt = lb.board.piece_at(i).piece_type
            assert pt == 1, f'Square {sq} {i} should be a pawn {pt}'

    def assert_is_empty(squares):
        for sq in squares:
            i = sq_to_int(sq)
            p = lb.board.piece_at(i)
            assert p is None, f'Square {sq}, {i} should be empty: {p}'

    # TEST INITIAL BOARD SETUP

    # All the squares that should be occupied by pawns
    assert_is_pawn(['a2', 'b2', 'c2', 'h2'])
    # All the squares that should be empty
    assert_is_empty(['a3', 'b3', 'c3', 'h3'])

    # TEST UNDO MOVES
    moves.extend([
        'a2a3',
        'b2b3',
        'c2c3',
        '*3',  # Undo last move
        'h2h3',  # Need an 'actual move' to not wait forever on white
    ])
    play_moves(4)
    # Pawns a,b, and h are moved, but c was undone
    assert_is_pawn(['a3', 'b3', 'c2', 'h3'])
    assert_is_empty(['a2', 'b2', 'c3', 'h2'])

    # TEST BOARD RESET
    moves.extend([
        '*2',
        'd2d3'  # Again, need 'actual move'
    ])
    play_moves(1)
    # Back to initial board setup, except for d
    assert_is_pawn(['a2', 'b2', 'c2', 'd3', 'h2'])
    assert_is_empty(['a3', 'b3', 'c3', 'd2', 'h3'])

    # TEST LOAD MOVES
    moves.extend([
        'a2a3',
        'b2b3',
        'c2c3',
        '*4',  # Load current move
        'h2h3',
    ])
    play_moves(4)
    # Same as above, but c was actually mived
    assert_is_pawn(['a3', 'b3', 'c3', 'd3', 'h3'])
    assert_is_empty(['a2', 'b2', 'c2', 'd2', 'h2'])

    # TODO test popping from empty save file

    print('Done! test_reset_codes passed')


if __name__ == '__main__':
    test_english_moves()
    test_reset_codes()
