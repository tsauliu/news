#%%
# 从远程服务器上按图索骥copy markdown 文件，按文件夹分类
import pandas as pd
import os
from parameters import friday_date, download_file

# Read URLs from CSV
urls = pd.read_csv(f'./data/1_urls/{friday_date}_article_urls.csv')

# Set up output folder
local_folder_path = f'./data/2_raw_mds/{friday_date}'
os.makedirs(local_folder_path, exist_ok=True)

# Process each URL
for _, row in urls.iterrows():
    url = row['url']  # Adjust column name if different
    title = row['title']  # Make sure 'title' column exists in your CSV
    url_id = url.split('/')[-1]
    filename = f"{url_id}.md"
    output_path = os.path.join(local_folder_path, filename)
    # Skip if file already exists
    if os.path.exists(output_path):
        # print(f"File already exists: {output_path}, skipping...")
        continue
    # Copy file from remote server
    remote_md_url = f"http://118.193.44.18:8000/data/articles/{friday_date}/{filename}"
    download_file(remote_md_url, output_path)
