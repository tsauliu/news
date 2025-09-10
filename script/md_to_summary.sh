#!/bin/bash
screen -ls | grep 'summarysummary' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true
screen -dmS summarysummary bash -c 'cd ~/Dropbox/BDAcode/AutoNews && source ~/pyenv/bin/activate && python3 3_article_to_overall_summary.py'