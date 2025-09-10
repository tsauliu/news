#!/bin/bash
# Consolidated pipeline for new scripts:
# - 1_fetching_news.py: replaces 0_RSS.py + 1_sql_to_urls.py + 2_get_mds.py
# - 2_md_to_article_summary.py: replaces 3_md_to_article_summary.py

# Kill any existing sessions from previous runs
screen -ls | grep 'rss' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true
screen -ls | grep 'mdsummary' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true

# Run both stages sequentially in one screen session to avoid race conditions
screen -dmS rss bash -c 'cd ~/Dropbox/BDAcode/AutoNews && source ~/pyenv/bin/activate && python3 1_fetching_news.py && python3 2_md_to_article_summary.py'
