# Crontab entries for data processing
# Run sql_to_urls.py at 15 minutes past every hour from 8 AM to 11 PM
15 8-23 * * * ~/wewe-rss/script/get_urls_to_md.sh