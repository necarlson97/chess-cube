import sys
from datetime import timedelta

from referee import Referee
from player import TerminalPlayer
from stockfish_player import StockfishPlayer
from email_player import EmailPlayer


def main():

    # TODO rudimentary, but works for now
    turn_time = timedelta(seconds=10)
    if '1s' in sys.argv:
        turn_time = timedelta(seconds=1)
    elif '30m' in sys.argv:
        turn_time = timedelta(minutes=30)

    white = StockfishPlayer(turn_time=turn_time)

    if 'email' in sys.argv:
        black = EmailPlayer()
    elif 'fishes' in sys.argv:
        black = StockfishPlayer(turn_time=turn_time)
    else:
        black = TerminalPlayer()

    print(f'Starting game with {white} vs {black} - ({turn_time} per turn)')
    r = Referee(white, black)

    # For now, just have it play games forever
    while True:
        r.play_game()


main()
