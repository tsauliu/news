# Calculate the date of the Friday of the current week
#%%
import datetime

current_date = datetime.datetime.now()
days_until_friday = (6 - (current_date.weekday() + 2) % 7) % 7  # 6 represents Friday in this system
friday_date = (current_date + datetime.timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
errorkeywords=["微信，是一个生活方式","参数错误","LinkReader","微信输入法"]
sector_list=['商业落地','核心技术','政策监管','企业战略','硬件设备','数据与地图','资本动向']#%%