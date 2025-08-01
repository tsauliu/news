# Step 1: Generate three separate markdown files with Word formatting annotations
# This script outputs content to three markdown files for manual review

from pdfreport.run import auto_weekly_reports
auto_weekly_reports()

import pandas as pd
import datetime, os
from parameters import friday_date, sector_list
import shutil

# Create output directory
output_dir = f'data/6_final_mds'
os.makedirs(output_dir, exist_ok=True)

# =============================================================================
# 1. Generate Sellside Highlights Markdown
# =============================================================================
sellside_md = f'{output_dir}/{friday_date}_sellside_highlights.md'

with open(sellside_md, 'w', encoding='utf-8') as f:
    # Research reports for the week
    f.write(f'<!-- WORD_STYLE: heading_level_1 -->\n')
    f.write(f'# Sellside highlights for Week – {friday_date}\n\n')

    raw_path = f'./pdfreport/01 raw/{friday_date}'
    cdn_path = f'./pdfreport/cdn/{friday_date}'

    os.makedirs(cdn_path, exist_ok=True)

    # Sort files by date in filename (yyyy-mm-dd format)
    for file in sorted(os.listdir(raw_path), key=lambda x: x.split('-')[0:3] if '-' in x else x, reverse=True):
        if file.endswith('.pdf'):
            print(f"Processing {file}")
            summary_file_path = f'./pdfreport/04 summary/{friday_date}_ds/{file.replace(".pdf", ".md")}'
            
            # Check if summary file exists before trying to read it
            if not os.path.exists(summary_file_path):
                print(f"Warning: Summary file not found for {file}")
                print(f"Attempting to regenerate summary for {file}...")
                
                # Try to regenerate the missing summary
                from pdfreport.three_md_to_summary import process_single_file
                
                # Check if cleaned markdown exists
                cleaned_md_path = f'./pdfreport/03 cleaned_markdown/{friday_date}/{file.replace(".pdf", ".md")}'
                if os.path.exists(cleaned_md_path):
                    try:
                        # Read prompt
                        prompt = open('pdfreport/prompt.txt','r').read()
                        
                        # Attempt to regenerate summary
                        output_path_ds = f'./pdfreport/04 summary/{friday_date}_ds'
                        os.makedirs(output_path_ds, exist_ok=True)
                        
                        result = process_single_file(
                            f'./pdfreport/03 cleaned_markdown/{friday_date}',
                            output_path_ds,
                            file.replace(".pdf", ".md"),
                            prompt,
                            max_retries=3
                        )
                        
                        print(f"Regeneration result: {result}")
                        
                        # Check if regeneration was successful
                        if not os.path.exists(summary_file_path):
                            print(f"Failed to regenerate summary for {file}, skipping...")
                            continue
                        else:
                            print(f"Successfully regenerated summary for {file}")
                            
                    except Exception as e:
                        print(f"Error regenerating summary for {file}: {str(e)}")
                        continue
                else:
                    print(f"Cleaned markdown not found for {file}, skipping...")
                    continue
                
            ds_summary = open(summary_file_path, 'r', encoding='utf-8').read()
            
            for summary in [ds_summary]:
                lines = summary.strip().split('\n')
                for line in lines:
                    if line.startswith('**'):
                        f.write('\n')
                        f.write('<!-- WORD_STYLE: summarytitle -->\n')
                        f.write(f'{line.replace("**","").strip()}\n\n')
                    elif len(line) > 10:
                        f.write('<!-- WORD_STYLE: bullet -->\n')
                        f.write(f'{line.replace("*","").replace("**","").replace("- ","").replace("#","").strip()}\n\n')
            
            # Handle PDF file copying and link generation
            parts = file.split('-')
            if len(parts) > 1:
                file_id = parts[-1].replace('.pdf', '')
                new_filename = f"{file_id}.pdf"
                source_path = os.path.join(raw_path, file)
                destination_path = os.path.join(cdn_path, new_filename)
                shutil.copy2(source_path, destination_path)
                f.write('<!-- WORD_STYLE: link -->\n')
                f.write(f'https://auto.bda-news.com/{friday_date}/{file_id}.pdf\n\n')

print(f"Sellside highlights generated: {sellside_md}")

# =============================================================================
# 2. Generate Key News Takeaway Markdown
# =============================================================================
takeaway_md = f'{output_dir}/{friday_date}_key_takeaway.md'

with open(takeaway_md, 'w', encoding='utf-8') as f:
    # Key takeaway for the week
    summary_md = open(f'data/5_summary_mds/{friday_date}_summary.md', 'r', encoding='utf-8').read()

    f.write('<!-- WORD_STYLE: heading_level_1 -->\n')
    f.write(f'# Key News takeaway for Week – {friday_date}\n\n')
    
    # Parse the summary markdown and add headings and paragraphs
    lines = summary_md.strip().split('\n')
    for line in lines:
        if line.startswith('##'):
            f.write('\n')
            f.write('<!-- WORD_STYLE: summarytitle -->\n')
            f.write(f'{line[2:].strip()}\n\n')
        elif len(line) > 10 and line.startswith('#'):
            f.write('<!-- WORD_STYLE: bullet -->\n')
            f.write(f'{line.replace("*","").replace("**","").replace("- ","").replace("#","").strip()}\n\n')

print(f"Key takeaway generated: {takeaway_md}")

# =============================================================================
# 3. Generate Detailed News Markdown
# =============================================================================
detailed_md = f'{output_dir}/{friday_date}_detailed_news.md'

with open(detailed_md, 'w', encoding='utf-8') as f:
    # Detailed News for the week
    f.write('<!-- WORD_STYLE: heading_level_1 -->\n')
    f.write(f'# Detailed News for Week – {friday_date}\n\n')
    
    combined_md = open(f'data/4_combined_mds/{friday_date}_combined_news.md', 'r', encoding='utf-8').read()
    lines = combined_md.strip().split('\n')

    # Convert lines to a dataframe
    news_data = []

    for line in lines:
        if line.startswith('title: '):
            news_data.append({'title': line[7:]})
        elif line.startswith('link: ') and news_data:
            news_data[-1]['link'] = line[6:]
        elif line.startswith('sector: ') and news_data:
            news_data[-1]['sector'] = line[8:].split('、')[0]
        elif line.startswith('author: ') and news_data:
            news_data[-1]['author'] = line[8:]
        elif line.startswith('date: ') and news_data:
            news_data[-1]['date'] = line[6:]
        elif line.startswith('content: ') and news_data:
            news_data[-1]['content'] = line[9:]

    # Create dataframe
    news_df = pd.DataFrame(news_data)
    c1 = news_df.sector != '其他'
    news_df = news_df[c1].sort_values(by=['sector', 'date'], ascending=False)

    # Loop through the dataframe to write to markdown
    for sector in sector_list:
        news_df_sector = news_df[news_df.sector == sector]
        if news_df_sector.empty:
            continue
        
        f.write('<!-- WORD_STYLE: heading_level_2 -->\n')
        f.write(f'## {sector}\n\n')
        
        for _, row in news_df_sector.iterrows():
            f.write('\n')
            f.write('<!-- WORD_STYLE: heading_level_3 -->\n')
            f.write(f'### {row["title"]}\n\n')
        
            if 'link' in row and not pd.isna(row['link']):
                f.write('<!-- WORD_STYLE: link -->\n')
                f.write(f'{row["link"]}\n\n')
            
            if 'author' in row and not pd.isna(row['author']):
                f.write('<!-- WORD_STYLE: author -->\n')
                if 'date' in row and not pd.isna(row['date']):
                    f.write(f'{row["date"]} {row["author"]}\n\n')
                else:
                    f.write(f'{row["author"]}\n\n')
            
            if 'content' in row and not pd.isna(row['content']):
                f.write('<!-- WORD_STYLE: normal_paragraph -->\n')
                f.write(f'{row["content"]}\n\n')

print(f"Detailed news generated: {detailed_md}")

print("All three markdown files generated successfully!")
print("Files created:")
print(f"1. {sellside_md}")
print(f"2. {takeaway_md}")
print(f"3. {detailed_md}") 