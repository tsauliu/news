# AI agent to read the md file and summarize the news at a higher level
#%%
import os
import glob
from datetime import datetime
import pandas as pd
from models import OneAPI_request
from parameters import friday_date,errorkeywords,sector_list
from utils import archive_existing_in_target
output_dir = f'data/4_combined_mds'
os.makedirs(output_dir, exist_ok=True)
archive_existing_in_target(output_dir)

def merge_md_files():
    """Merge markdown files in raw_mds into separate files by sector"""
    
    # Setup paths and find markdown files
    raw_mds_dir = f'data/3_article_summary'
    
    
    # Create a dictionary to store content for each sector
    sector_contents = {sector: [] for sector in sector_list}
    
    md_files = glob.glob(f'{raw_mds_dir}/{friday_date}/*.md', recursive=True)
    
    # Process each markdown file
    for md_file in md_files:            
        try:
            with open(md_file, 'r', encoding='utf-8') as infile:
                content = infile.read()
                
                if any(keyword in content for keyword in errorkeywords):
                    continue
                
                # Extract sector, relevance, and date from the content
                file_sector = None
                relevant_score = 0
                date = None
                
                for line in content.split('\n'):
                    if line.startswith('sector:'):
                        file_sector = line.replace('sector:', '').strip()
                    elif line.startswith('relevant:'):
                        try:
                            relevant_score = int(line.replace('relevant:', '').strip())
                        except ValueError:
                            relevant_score = 0
                    elif line.startswith('date:'):
                        date = line.replace('date:', '').strip()
                
                # Only include files with relevant score >= 3
                if file_sector in sector_list and relevant_score >= 3:
                    sector_contents[file_sector].append((date, content))
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    # Write each sector's content to a separate file, sorted by date in descending order
    output_files = []
    for sector, content_list in sector_contents.items():
        if content_list:  # Only create files for sectors with content
            # Sort by date in descending order (newest first)
            sorted_content = sorted(content_list, key=lambda x: x[0] if x[0] else "", reverse=True)
            
            # Join the sorted content
            combined_content = "\n\n---\n\n".join([content for _, content in sorted_content])
            
            sector_file = f'{output_dir}/{friday_date}_{sector}_merged_news.md'
            with open(sector_file, 'w', encoding='utf-8') as outfile:
                outfile.write(combined_content)
            output_files.append(sector_file)
    
    return output_files

output_files=merge_md_files()
# Create a combined summary file with all sectors in the specified order
combined_summary_file = f'{output_dir}/{friday_date}_combined_news.md'

with open(combined_summary_file, 'w', encoding='utf-8') as combined_file:
    for sector in sector_list:
        sector_file = next((file for file in output_files if f"_{sector}_merged_news.md" in file), None)
        if sector_file:            
            with open(sector_file, 'r', encoding='utf-8') as sector_content:
                combined_file.write(sector_content.read())
            combined_file.write("\n\n---\n\n")

print(f"Combined news file created at: {combined_summary_file}")

prompt = open('./prompt/auto_md_to_summary.md', 'r', encoding='utf-8').read()

# Create summary directory
summary_dir = f'data/5_summary_mds'
os.makedirs(summary_dir, exist_ok=True)
archive_existing_in_target(summary_dir)

#%%
# Initialize a dictionary to store summaries by sector
sector_summaries = {sector: None for sector in sector_list}

# Process each sector file
for output_file in output_files:
    try:
        # Extract sector name from filename
        sector_name = os.path.basename(output_file).split('_')[1]
        
        # Read the merged content
        with open(output_file, 'r', encoding='utf-8') as f:
            combined_md = f.read()
            
        print(f"Generating summary for sector: {sector_name}")
        
        # Generate summary via OneAPI
        md_summary = OneAPI_request(prompt, combined_md)
        
        # Save individual sector summary
        sector_summary_file = os.path.join(summary_dir, f'{friday_date}_{sector_name}_summary.md')
        with open(sector_summary_file, 'w', encoding='utf-8') as f:
            f.write(md_summary)
        print(f"Summary saved to {sector_summary_file}")
        
        # Store in dictionary by sector
        sector_summaries[sector_name] = md_summary
        
    except Exception as e:
        print(f"Error processing {output_file}: {e}")

#%%
# Combine all summaries in the order defined by sector_list
ordered_summaries = []
for sector in sector_list:
    if sector_summaries[sector]:
        ordered_summaries.append(sector_summaries[sector])

combined_summary = "\n\n".join(ordered_summaries)
combined_summary_file = os.path.join(summary_dir, f'{friday_date}_summary.md')

try:
    with open(combined_summary_file, 'w', encoding='utf-8') as f:
        f.write(combined_summary)
    print(f"Combined summary saved to {combined_summary_file}")
except Exception as e:
    print(f"Error saving combined summary: {e}")
