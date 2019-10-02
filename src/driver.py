#!/usr/bin/python3.7
from text_input import TextInput
from living_board import LivingBoard

if __name__ == '__main__':
    # TODO add human input to init
    lb = LivingBoard()
    ti = TextInput(lb)
    lb.get_human_move_uci = ti.get_input_func()
    lb.play_game()
