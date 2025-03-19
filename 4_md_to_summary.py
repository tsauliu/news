# AI agent to read the md file and summarize the news at a higher level
#%%
import os
import glob
from datetime import datetime

def merge_md_files():
    """Merge all markdown files in raw_mds into a single file"""
    # Define paths
    raw_mds_dir = os.path.join('data', 'raw_mds')
    output_dir = os.path.join('data', 'combined_mds')
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

if __name__ == "__main__":
    merge_md_files()



