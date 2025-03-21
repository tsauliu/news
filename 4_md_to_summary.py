# AI agent to read the md file and summarize the news at a higher level
#%%
import os
import glob
from datetime import datetime
import pandas as pd
from openai import OpenAI
from apikey import api_key,model_id_md_to_summary
from parameters import friday_date,errorkeywords,sector_list

def merge_md_files():
    """Merge markdown files in raw_mds into separate files by sector"""
    
    # Setup paths and find markdown files
    raw_mds_dir = f'data/1_raw_mds'
    output_dir = f'data/2_combined_mds'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a dictionary to store content for each sector
    sector_contents = {sector: "" for sector in sector_list}
    
    md_files = glob.glob(f'{raw_mds_dir}/{friday_date}/*.md', recursive=True)
    
    # Process each markdown file
    for md_file in md_files:            
        try:
            with open(md_file, 'r', encoding='utf-8') as infile:
                content = infile.read()
                
                if any(keyword in content for keyword in errorkeywords):
                    continue
                
                # Extract sector and relevance from the content
                file_sector = None
                relevant_score = 0
                
                for line in content.split('\n'):
                    if line.startswith('sector:'):
                        file_sector = line.replace('sector:', '').strip()
                    elif line.startswith('relevant:'):
                        try:
                            relevant_score = int(line.replace('relevant:', '').strip())
                        except ValueError:
                            relevant_score = 0
                
                # Only include files with relevant score >= 3
                if file_sector in sector_list and relevant_score >= 3:
                    sector_contents[file_sector] += content + "\n\n---\n\n"
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    # Write each sector's content to a separate file
    output_files = []
    for sector, content in sector_contents.items():
        if content:  # Only create files for sectors with content
            sector_file = f'{output_dir}/{friday_date}_{sector}_merged_news.md'
            with open(sector_file, 'w', encoding='utf-8') as outfile:
                outfile.write(content)
            output_files.append(sector_file)
    
    return output_files

output_files=merge_md_files()

#%%
combined_md=open(output_files[0], 'r', encoding='utf-8').read()
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

