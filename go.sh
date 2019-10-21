#!/bin/sh
set -e  # Exit immediately on error
help_text="""
Script for launching a python text-based chess ai.
First argument changes the 'environment'. Options:
  local - Run game with text and speech through terminal input
  email - Run with input and output over email
  email_daemon - Run email, but with nohup
    (in background, detached from terminal, output in nohup.out)
"""

# TODO add an automatic option for post-ssh, what we are doing now as:
# nohup bash go.sh email &
# Could do it with python or nohup

# Enter python virtual enviornment
source env/bin/activate

function local_chess {
  # Run the chess client locally in this bash shell (default)
  python3.7 src/driver.py
}

function email_chess {
  # Run the email chess in this bash shell (ends if terminal closes)
  python3.7 src/email_chess.py
}

function email_daemon_chess {
  # Run the email chess in this a nohup shell
  # (does not end when user logs out. The 'production' env)
  echo "Looking for currently running processes..."
  # List all processes, grep the pertinent ones,
  # remove this grep search (as, obviously, it contains the same string),
  # take only the pid, use that pid to kill
  PAST_PIDS=$(ps aux | grep -i 'python3.7 src/email_chess.py' | grep -v "grep" | awk '{print $2}') || true
  if [ ! -z $PAST_PIDS ]; then
    echo "  Killing: $PAST_PIDS"
    kill $PAST_PIDS
  else
    echo "  None found"
  fi

  echo "Removing old nohup.out..."
  rm -f nohup.out

  # Start in nohup shell
  echo "Starting in nohup..."
  nohup python3.7 src/email_chess.py &
  sleep 1
  echo "Done!"
}

env=${1:-'local'}
# Excecute depending on enviorment
case $env in
  local) local_chess ;;
  email) email_chess ;;
  email_daemon) email_daemon_chess ;;
  *) echo -e "Unknwon env: '$env'.\n$help_text" ;;
esac
