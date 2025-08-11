#!/bin/sh
if [ $(date +\%u) -eq 5 ] && [ $(expr $(date +\%W) \% 2) -eq 0 ]; then
  python all_account_app_emg_send_more_people.py
else
  echo "Not executing the Python script."
fi
