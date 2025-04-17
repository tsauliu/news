#!/bin/bash

screen -ls | grep 'sqlurl' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS sqlurl bash -c 'cd ~/AutoNews && source ~/pyenv/bin/activate && python3 1_sql_to_urls.py; exec bash'
sleep 15
screen -ls | grep 'urlmd' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS urlmd bash -c 'cd ~/AutoNews && source ~/pyenv/bin/activate && python3 2_get_mds.py; exec bash'