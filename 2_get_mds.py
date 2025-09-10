#%%
# 从远程服务器上按图索骥copy markdown 文件，按文件夹分类
import pandas as pd
import os
from parameters import friday_date, download_file, get_filename, ARTICLE_SOURCE
import datetime
# from web_scrawler import scrape_url_to_md, driver
# Read URLs from CSV
urls = pd.read_csv(f'./data/1_urls/{friday_date}_article_urls.csv')

# Set up output folder
local_folder_path = f'./data/2_raw_mds/{friday_date}'
os.makedirs(local_folder_path, exist_ok=True)

if ARTICLE_SOURCE == 'rss':
    # RSS mode: 0_RSS.py has already written raw MDs locally
    print("RSS mode: skipping remote markdown download; MDs are generated in 0_RSS.py.")
else:
    print(f"Processing {len(urls)} URLs (remote_db mode)")
    # Process each URL
    for _, row in urls.iterrows():
        # Copy file from remote server
        url = row['url']  # Adjust column name if different
        # Treat any mp.weixin links as wechat content regardless of 'source' label
        if 'mp.weixin.qq.com' in url or row.get('source') in ('wechat', 'wewerss'):
            filename = f"{get_filename(url, 'wechat')}.md"
            output_path = os.path.join(local_folder_path, filename)
            if os.path.exists(output_path):
                continue
            remote_md_url = f"http://118.193.44.18:8000/data/articles/{friday_date}/{filename}"
            status = download_file(remote_md_url, output_path)
            if not status:
                last_friday_date = datetime.datetime.strptime(friday_date, '%Y-%m-%d') - datetime.timedelta(days=7)
                last_friday_date = last_friday_date.strftime('%Y-%m-%d')
                remote_md_url = f"http://118.193.44.18:8000/data/articles/{last_friday_date}/{filename}"
                status = download_file(remote_md_url, output_path)
        else:
            # Non-wechat URL in remote_db mode; nothing to fetch here
            continue
    print(f"Processed {len(urls)} URLs")
