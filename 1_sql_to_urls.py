# %%
# extract news from sqlite
import sqlite3
import pandas as pd
import os
from parameters import friday_date
from apikey import news_start

conn = sqlite3.connect('data/wewe-rss.db')
articles = pd.read_sql_query("SELECT * FROM articles", conn)
articles['publish_time'] = pd.to_datetime(articles['publish_time'], unit='s', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['created_at'] = pd.to_datetime(articles['created_at'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['updated_at'] = pd.to_datetime(articles['updated_at'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['url'] = 'https://mp.weixin.qq.com/s/' + articles['id']

feeds = pd.read_sql_query("SELECT * FROM feeds", conn)

article_clean=articles[['mp_id', 'title','publish_time', 'url']].merge(feeds.rename(columns={'id': 'mp_id'})[['mp_id', 'mp_name']], on='mp_id', how='left').drop(columns=['mp_id'])
article_clean.sort_values(by='publish_time', ascending=False, inplace=True)

article_clean = article_clean[pd.to_datetime(article_clean['publish_time']) >= (pd.to_datetime(friday_date) - pd.Timedelta(days=news_start))]


folder_path = f'data/1_urls/'
os.makedirs(folder_path, exist_ok=True)

# Get current date for the filename
article_clean[['publish_time','mp_name','title', 'url']].to_csv(os.path.join(folder_path, f'{friday_date}_article_urls.csv'), index=False)

print(f'{friday_date}_article_urls.csv saved')
