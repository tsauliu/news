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
    # RSS mode: 0_RSS.py should have written raw MDs locally.
    # Backfill minimal placeholders for any missing MDs so step 3 doesn't fail.
    print("RSS mode: verifying raw MDs; backfilling placeholders if missing.")
    missing = 0
    for _, row in urls.iterrows():
        url = row.get('url')
        source = row.get('source', 'rss')
        rawfilename = f"{get_filename(url, source)}.md"
        output_path = os.path.join(local_folder_path, rawfilename)
        if not os.path.exists(output_path):
            missing += 1
            try:
                safe_title = row.get('title') or 'Untitled'
                published = row.get('publish_time') or row.get('published') or ''
                mp_name = row.get('mp_name') or row.get('source_name') or ''
                placeholder = (
                    "[No content extracted]\n"
                    f"Source: {mp_name}\nTitle: {safe_title}\nLink: {url}\nPublished: {published}\n"
                )
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(placeholder)
            except Exception as e:
                print(f"  Warning: failed to write placeholder for {url}: {e}")
    if missing:
        print(f"Backfilled {missing} placeholder MD(s) under {local_folder_path}")
    else:
        print("All expected MDs present.")
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
