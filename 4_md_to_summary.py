# AI agent to read the md file and summarize the news at a higher level
#%%
import os
import glob
from datetime import datetime
import pandas as pd
from openai import OpenAI
from apikey import api_key,model_id_md_to_summary
from parameters import friday_date,errorkeywords

def merge_md_files():
    """Merge all markdown files in raw_mds into a single file"""
    
    # Setup paths and find markdown files
    raw_mds_dir = f'data/1_raw_mds'
    output_dir = f'data/2_combined_mds'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/{friday_date}_merged_news.md'
    md_files = glob.glob(f'{raw_mds_dir}/{friday_date}/*.md', recursive=True)
    
    # Merge content
    with open(output_file, 'w', encoding='utf-8') as outfile:        
        for md_file in md_files:
            date=md_file.split('\\')[-1].split('_')[0]
            if date <= '2025-03-18':
                continue
            if any(keyword in open(md_file, 'r', encoding='utf-8').read() for keyword in errorkeywords):
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n---\n\n")
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
    
    return output_file

output_file=merge_md_files()
combined_md=open(output_file, 'r', encoding='utf-8').read()
print(combined_md)

#%%
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key=api_key
)

prompt=open('./prompt/auto_md_to_summary.md','r',encoding='utf-8').read()

def summary(combined_md):
    completion = client.chat.completions.create(
        model=model_id_md_to_summary,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": combined_md},
        ],
    )
    return completion.choices[0].message.content

md_summary=summary(combined_md)

# Save the summary to a file in the summary_mds folder
summary_dir = f'data/3_summary_mds'
os.makedirs(summary_dir, exist_ok=True)

summary_file = os.path.join(summary_dir, f'{friday_date}_summary.md')

try:
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(md_summary)
    print(f"Summary saved to {summary_file}")
except Exception as e:
    print(f"Error saving summary: {e}")

