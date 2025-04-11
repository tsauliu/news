# Crontab entries for data processing
# 在crontab中，五个星号分别代表：分钟 小时 日期 月份 星期几

# Run sql_to_urls.py at 15 minutes past every hour from 8 AM to 11 PM
15 8-23 * * * ~/wewe-rss/script/get_urls_to_md.sh
# Run mdtosummary every Friday at 12 AM
0 12 * * 5 ~/wewe-rss/script/md_to_summary.sh