# Crontab entries for data processing
# 在crontab中，五个星号分别代表：分钟 小时 日期 月份 星期几

# Run sql_to_urls.py at 15 minutes past every hour from 8 AM to 11 PM
15 8,11,12,14,16,20,23 * * * ~/AutoNews/script/get_urls_to_md.sh
# Run mdtosummary every Friday at 13:00
0 13 * * 5 ~/AutoNews/script/md_to_summary.sh