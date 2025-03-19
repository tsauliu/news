# Calculate the date of the Friday of the current week
#%%
import datetime

current_date = datetime.datetime.now()
days_until_friday = (4 - current_date.weekday()) % 7  # 4 represents Friday (0 is Monday)
friday_date = (current_date + datetime.timedelta(days=days_until_friday)).strftime('%Y-%m-%d')

#%%