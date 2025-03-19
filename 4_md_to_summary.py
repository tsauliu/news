# AI agent to read the md file and summarize the news at a higher level
#%%
import os
import glob
from datetime import datetime
import pandas as pd
from openai import OpenAI
from apikey import api_key,model_id_md_to_summary


def merge_md_files():
    """Merge all markdown files in raw_mds into a single file"""
    # Define paths
    raw_mds_dir = os.path.join('data', '1_raw_mds')
    output_dir = os.path.join('data', '2_combined_mds')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output file
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = os.path.join(output_dir, f'{current_date}_merged_news.md')
    
    # Find all markdown files
    md_files = glob.glob(os.path.join(raw_mds_dir, '**', '*.md'), recursive=True)
    
    # Merge content
    with open(output_file, 'w', encoding='utf-8') as outfile:        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n---\n\n")
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
    
    print(f"Merged {len(md_files)} files into {output_file}")
    return output_file

output_file=merge_md_files()
combined_md=open(output_file, 'r', encoding='utf-8').read()
print(combined_md)

#%%
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key=api_key
)

def summary(combined_md):
    completion = client.chat.completions.create(
        model=model_id_md_to_summary,
        messages=[
            {"role": "user", "content": combined_md},
        ],
    )
    return completion.choices[0].message.content

md_summary=summary(combined_md)

# Save the summary to a file in the summary_mds folder
summary_dir = os.path.join('data', '3_summary_mds')
os.makedirs(summary_dir, exist_ok=True)

current_date = datetime.now().strftime('%Y-%m-%d')
summary_file = os.path.join(summary_dir, f'{current_date}_summary.md')

try:
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(md_summary)
    print(f"Summary saved to {summary_file}")
except Exception as e:
    print(f"Error saving summary: {e}")

