#%%
# 从远程服务器上按图索骥copy markdown 文件，按文件夹分类
import pandas as pd
import os
from parameters import friday_date, download_file,get_filename
import datetime
# from web_scrawler import scrape_url_to_md, driver
# Read URLs from CSV
urls = pd.read_csv(f'./data/1_urls/{friday_date}_article_urls.csv')

# Set up output folder
local_folder_path = f'./data/2_raw_mds/{friday_date}'
os.makedirs(local_folder_path, exist_ok=True)

print(f"Processing {len(urls)} URLs")
# Process each URL
for _, row in urls.iterrows():
    # Copy file from remote server
    url = row['url']  # Adjust column name if different
    title = row['title']  # Make sure 'title' column exists in your CSV
    
    if row['source'] == 'wechat':
        filename = f"{url.split('/')[-1]}.md"
        output_path = os.path.join(local_folder_path, filename)
        if os.path.exists(output_path):
            continue
        remote_md_url = f"http://118.193.44.18:8000/data/articles/{friday_date}/{filename}"
        status=download_file(remote_md_url, output_path)
        if not status:
            last_friday_date=datetime.datetime.strptime(friday_date, '%Y-%m-%d') - datetime.timedelta(days=7)
            last_friday_date=last_friday_date.strftime('%Y-%m-%d')
            remote_md_url = f"http://118.193.44.18:8000/data/articles/{last_friday_date}/{filename}"
            status=download_file(remote_md_url, output_path)
    elif row['source'] == 'rss':
        pass
        # print(f"RSS article {title}")
        # print(f"RSS article {row['url']}")
        # filename = f'{get_filename(url,row['source'])}.md'
        # output_path = os.path.join(local_folder_path, filename)
        # if os.path.exists(output_path):
        #     continue
        # print(output_path)
        # scrape_url_to_md(row['url'], output_path)
# driver.quit()
print(f"Processed {len(urls)} URLs")