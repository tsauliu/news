# Calculate the date of the Friday of the current week
#%%
import datetime

current_date = datetime.datetime.now()
days_until_friday = (6 - (current_date.weekday() + 2) % 7) % 7  # 6 represents Friday in this system
friday_date = (current_date + datetime.timedelta(days=days_until_friday)).strftime('%Y-%m-%d')

#%%