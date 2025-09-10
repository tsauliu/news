#!/bin/bash
set -euo pipefail

# Helper to kill a screen session by name if it exists
kill_screen() {
  local name="$1"
  screen -S "$name" -X quit || true
}

# Screen session names
S3="s3_summary"
S4="s4_pdf"
S5="s5_podcast"
S6="s6_sellside"
S7="s7_email"
S10="s10_two_week"

# Clean up any old sessions
kill_screen "$S3"
kill_screen "$S4"
kill_screen "$S5"
kill_screen "$S6"
kill_screen "$S7"
kill_screen "$S10"

REPO_DIR=~/Dropbox/BDAcode/AutoNews

# Commands to activate env in each screen
ACTIVATE='if [ -f ~/pyenv/bin/activate ]; then . ~/pyenv/bin/activate; elif [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi'

echo "Launching 3_article_to_overall_summary.py in $S3"
screen -dmS "$S3" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 3_article_to_overall_summary.py"

# After summary, sleep 120 seconds before launching the rest
sleep 120

echo "Launching 4_news_summary_pdf.py in $S4"
screen -dmS "$S4" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 4_news_summary_pdf.py"

echo "Launching 5_podcast_summary.py in $S5"
screen -dmS "$S5" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 5_podcast_summary.py"

echo "Launching 6_sellside_highlights.py in $S6"
screen -dmS "$S6" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 6_sellside_highlights.py"

echo "Launching 7_generate_email.py in $S7"
screen -dmS "$S7" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 7_generate_email.py"

# When all started, sleep 600s then run the two-week summary
sleep 600

echo "Launching 10_two_week_summary.py in $S10"
screen -dmS "$S10" bash -lc "cd $REPO_DIR && $ACTIVATE && python3 10_two_week_summary.py"

echo "All screens launched. Attach with: screen -r <name>"
