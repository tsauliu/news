screen -ls | grep 'mdsummary' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS mdsummary bash -c 'cd ~/wewe-rss && source ~/pyenv/bin/activate && python3 3_md_to_article_summary.py; exec bash'
sleep 3600
screen -ls | grep 'summarysummary' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS summarysummary bash -c 'cd ~/wewe-rss && source ~/pyenv/bin/activate && python3 4_article_to_overall_summary.py; exec bash'
sleep 1200
screen -ls | grep 'docxsummary' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS docxsummary bash -c 'cd ~/wewe-rss && source ~/pyenv/bin/activate && python3 5_combined_to_docx.py exec bash'
