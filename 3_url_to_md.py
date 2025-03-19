# AI agent to read the webpage and summarize the news
#%%
import os
import datetime
import pandas as pd
from openai import OpenAI
from apikey import api_key,model_id_url_to_summary

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key=api_key
)

def summary(url):
    completion = client.chat.completions.create(
        model=model_id_url_to_summary,
        messages=[
            {"role": "user", "content": url},
        ],
    )
    return completion.choices[0].message.content

today_date = datetime.datetime.now().strftime('%Y-%m-%d')

urls=pd.read_csv(f'./data/0_urls/{today_date}_article_urls.csv')

folder_path = f'./data/1_raw_mds/{today_date}'
os.makedirs(folder_path, exist_ok=True)

# Loop through existing MD files to check and remove irrelevant content
for file in os.listdir(folder_path):
    if file.endswith('.md'):
        file_path = os.path.join(folder_path, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if the file contains irrelevant content about WeChat product updates
            if any(keyword in content for keyword in ["微信，是一个生活方式","参数错误"]):
                os.remove(file_path)
                print(f"Deleted irrelevant file: {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

#%%
import concurrent.futures
import time

def process_url(row):
    safe_title = ''.join(c if c.isalnum() else '_' for c in row['title'])
    filename = f"{folder_path}/{row['publish_time'].split()[0]}_{row['mp_name']}_{safe_title[:30]}.md"
    print(filename)
    
    if os.path.exists(filename):
        return
    
    try:
        content = summary(row['url'])
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Processed: {row['url']}"
    except Exception as e:
        return f"Error: {row['url']} - {e}"

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

