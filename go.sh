#!/bin/sh
set -e
help_text="""
Script for launching a python text-based chess ai.
First argument changs the 'enviornment'. Options:
  local - Run game with text and speech through terminal input
  email - Run with input and output over email
"""

# TODO add an automatic option for post-ssh, what we are doing now as:
# nohup bash go.sh email &
# Could do it with python or nohup

# Enter python virtual enviornment
source env/bin/activate

env=${1:-'local'}
# Excecute depending on enviorment
case $env in
  local) python3.7 src/driver.py ;;
  email) python3.7 src/email_chess.py ;;
  *) echo -e "Unknwon env: '$env'.\n$help_text" ;;
esac
