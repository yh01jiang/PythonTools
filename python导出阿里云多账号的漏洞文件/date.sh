#!/bin/sh
if [ $(date +\%u) -eq 5 ] && [ $(expr $(date +\%W) \% 2) -eq 0 ]; then
  python all-account-app-emg-chaifen-more-excel.py
else
  echo "Not executing the Python script."
fi
