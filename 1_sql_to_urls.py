'''
在远程服务器上host一个文件服务器,可以access folder
TODO: 1. 合并wewe-rss.db 和我新抓的db，生成新db，只看过去7天发布的文章
'''
# %%
# extract news from sqlite
import sqlite3
import pandas as pd
import os
from parameters import friday_date, download_file
from apikey import news_start

import requests
import shutil

# URL of the remote database file
local_db_path = 'data/wechat_articles.db'

remote_db_url = "http://118.193.44.18:8000/data/wechat_articles.db"
os.makedirs('data', exist_ok=True)
download_file(remote_db_url, local_db_path)

conn_wechat = sqlite3.connect(local_db_path)
wechat_articles = pd.read_sql_query("SELECT * FROM articles", conn_wechat)
conn_wechat.close()
wechat_articles['pub_time']=pd.to_datetime(wechat_articles['pub_time'],format='%Y年%m月%d日 %H:%M').dt.strftime('%Y-%m-%d %H:%M:%S')
wechat_articles['source'] = 'wechat'
wechat_articles.rename(columns={'pub_time':'publish_time','article_title':'title','channel_scraped':'mp_name'}, inplace=True)
wechat_articles=wechat_articles[['mp_name', 'title', 'url', 'publish_time','source']].sort_values(by='publish_time', ascending=False)

conn = sqlite3.connect('data/wewe-rss.db')
articles = pd.read_sql_query("SELECT * FROM articles", conn)
articles['publish_time'] = pd.to_datetime(articles['publish_time'], unit='s', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['created_at'] = pd.to_datetime(articles['created_at'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['updated_at'] = pd.to_datetime(articles['updated_at'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d %H:%M:%S')
articles['url'] = 'https://mp.weixin.qq.com/s/' + articles['id']

feeds = pd.read_sql_query("SELECT * FROM feeds", conn)

article_clean=articles[['mp_id', 'title','publish_time', 'url']].merge(feeds.rename(columns={'id': 'mp_id'})[['mp_id', 'mp_name']], on='mp_id', how='left').drop(columns=['mp_id'])
article_clean.sort_values(by='publish_time', ascending=False, inplace=True)
article_clean['source'] = 'wewerss'
article_clean = pd.concat([article_clean, wechat_articles]).drop_duplicates(subset=['url'])
article_clean = article_clean[pd.to_datetime(article_clean['publish_time']) >= (pd.to_datetime(friday_date) - pd.Timedelta(days=news_start))].sort_values(by='publish_time', ascending=False)
folder_path = f'data/1_urls/'
os.makedirs(folder_path, exist_ok=True)

# Get current date for the filename
article_clean[['publish_time','mp_name','title', 'url']].to_csv(os.path.join(folder_path, f'{friday_date}_article_urls.csv'), index=False)

print(f'{friday_date}_article_urls.csv saved')
