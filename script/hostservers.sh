#!/bin/bash
screen -ls | grep 'dataserver' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS dataserver bash -c 'cd ~/AutoNews/data && source ~/pyenv/bin/activate && python3 -m http.server 8000; exec bash'
screen -ls | grep 'pdfserver' | cut -d. -f1 | awk '{print $1}' | xargs kill 2>/dev/null || true; screen -dmS pdfserver bash -c 'cd ~/AutoNews/pdfreport/01\ raw/ && source ~/pyenv/bin/activate && python3 -m http.server 8100; exec bash'
