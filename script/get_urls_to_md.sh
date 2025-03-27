#!/bin/bash

screen -ls | grep 'sqlurl' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS sqlurl bash -c 'cd ~/wewe-rss && source ~/pyenv/bin/activate && python3 1_sql_to_urls.py; exec bash'
sleep 60
screen -ls | grep 'urlmd' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS urlmd bash -c 'cd ~/wewe-rss && source ~/pyenv/bin/activate && python3 2_url_to_md.py; exec bash'