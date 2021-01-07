from player import QueuePlayer
from referee import Referee


def main():
    test_check()


def test_check():
    # Set of moves to get us to check fast
    white_moves = ['e2e3', 'f1b5']
    black_moves = ['d7d6']

    white = QueuePlayer(white_moves)
    black = QueuePlayer(black_moves)

    r = Referee(white, black)
    r.play_game()
    print('All we were looking for was the " - check"')


main()
