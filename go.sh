#!/bin/sh
set -e  # Exit immediately on error
help_text="""
Script for launching a python text-based chess ai.
First argument changes the 'environment'. Options:
  local - Run through terminal
  email - Run over email
  email_daemon - Run email in background, giving A.I. 30m per turn
    (in background, detached from terminal, output in nohup.out)
  kill - kill any currently running email daemons
"""

# TODO add an automatic option for post-ssh, what we are doing now as:
# nohup bash go.sh email &
# Could do it with python or nohup

# Enter python virtual enviornment
source env/bin/activate

function local_chess {
  # Run the chess client locally in this bash shell (default)
  python3 src/main.py
}

function email_chess {
  # Run the email chess in this bash shell (ends if terminal closes)
  python3 src/main.py email
}


function email_daemon_chess {
  # Run the email chess in this a nohup shell, gives ai player 30m to think
  # (does not end when user logs out. The 'production' env)
  kill_previous

  echo "Removing old nohup.out..."
  rm -f nohup.out

  # Start in nohup shell
  echo "Starting in nohup..."
  nohup python3 src/main.py email 30m &
  sleep 1
  echo "Done!"
}

function find_previous {
  # Return the PIDs of any currently running email daemons
  PAST_PIDS=$(ps aux | grep -i 'python3 src/main.py' | grep -v "grep" | awk '{print $2}') || true
  echo "$PAST_PIDS"
}

function print_previous {
  # In case user is curious, print running PIDs
  PAST_PIDS=$(find_previous)
  if [ ! -z $PAST_PIDS ]; then
    echo "Found: $PAST_PIDS"
  else
    echo "None found"
  fi
}

function kill_previous {
  # Find and kill any currently running 'email daemons' on nohup
  echo "Looking for currently running processes..."
  # List all processes, grep the pertinent ones,
  # remove this grep search (as, obviously, it contains the same string),
  # take only the pid, use that pid to kill
  PAST_PIDS=$(find_previous)
  if [ ! -z $PAST_PIDS ]; then
    echo "  Killing: $PAST_PIDS"
    kill $PAST_PIDS
  else
    echo "  None found"
  fi
}

env=${1:-'local'}
# Execute depending on environment
case $env in
  local) local_chess ;;
  email) email_chess ;;
  email_daemon) email_daemon_chess ;;
  kill) kill_previous ;;
  find) print_previous ;;
  *) echo -e "Unknown env: '$env'.\n$help_text" ;;
esac
