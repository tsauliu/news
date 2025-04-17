# AI agent to read the webpage and summarize the news
#%%
import os
import pandas as pd
from models import deepseek_model
from parameters import friday_date,errorkeywords,get_filename

prompt=open('./prompt/auto_url_to_md.md','r',encoding='utf-8').read()

urls=pd.read_csv(f'./data/1_urls/{friday_date}_article_urls.csv')
mdraw_path=f'./data/2_raw_mds/{friday_date}'
md_summary_path=f'./data/3_article_summary/{friday_date}'
os.makedirs(md_summary_path, exist_ok=True)

def process_url(row):
    safe_title = ''.join(c if c.isalnum() else '_' for c in row['title'])
    filename = f"{md_summary_path}/{row['publish_time'].split()[0]}_{row['mp_name']}_{safe_title[:30]}.md"
    url=row['url']
    source=row['source']

    rawfilename=get_filename(url,source)
    contentpath=f'{mdraw_path}/{rawfilename}.md'
    
    if not os.path.exists(contentpath):
        return f"Error: {row['url']} - {contentpath} not found"
    
    content=open(contentpath,'r',encoding='utf-8').read()
    
    date=pd.to_datetime(row['publish_time']).strftime('%Y年%m月%d日')
    mp_name=row['mp_name']
    print(filename)
    
    if os.path.exists(filename):
        return
    
    try:
        content = deepseek_model(prompt,content)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write(f'\ndate: {date}\n')
            f.write(f'author: {mp_name}\n')
            f.write(f'link: {url}\n')
        return f"Processed: {row['url']}"
    except Exception as e:
        return f"Error: {row['url']} - {e}"

import concurrent.futures
import time
# Use ThreadPoolExecutor to process URLs in parallel
max_workers = 5  # Adjust based on your system capabilities and API rate limits
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all tasks and collect futures
    futures = {executor.submit(process_url, row): row for _, row in urls.iterrows()}
    
    # Process results as they complete
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        if result:
            print(result)
        # Add a small delay to avoid overwhelming the API
        time.sleep(0.1)

