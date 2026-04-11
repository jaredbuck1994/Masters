#!/usr/bin/env bash

set -u

cd "C:\Users\jared\OneDrive\Desktop\Masters_Live" || exit 1

while true; do
  echo "[$(date)] Updating scores..."

  python update_scores.py

  if [ $? -ne 0 ]; then
    echo "[$(date)] update_scores.py failed"
  else
    git add scores.csv

    # Only commit if scores.csv actually changed
    if ! git diff --cached --quiet; then
      git commit -m "update scores $(date '+%Y-%m-%d %H:%M:%S')"
      git push
      echo "[$(date)] Pushed updated scores.csv"
    else
      echo "[$(date)] No score changes to commit"
    fi
  fi

  echo "[$(date)] Sleeping for 5 minutes..."
  sleep 300
done