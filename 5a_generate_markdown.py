# Step 1: Generate three separate markdown files
# This script outputs content to three markdown files for PDF generation

from pdfreport.run import auto_weekly_reports
auto_weekly_reports()

import pandas as pd
import datetime, os
from parameters import friday_date, sector_list
import shutil

# Create output directory
output_dir = f'data/6_final_mds'
os.makedirs(output_dir, exist_ok=True)

# Move existing markdown files to SS subdirectory (only non-current week files)
ss_dir = os.path.join(output_dir, 'SS')
os.makedirs(ss_dir, exist_ok=True)

# Find and move only old markdown files (not from current week)
existing_files = [f for f in os.listdir(output_dir) 
                  if f.endswith('.md') and os.path.isfile(os.path.join(output_dir, f))
                  and not f.startswith(friday_date)]  # Don't move current week's files

if existing_files:
    print(f"Moving {len(existing_files)} legacy markdown files to SS/ subdirectory...")
    for file in existing_files:
        source = os.path.join(output_dir, file)
        destination = os.path.join(ss_dir, file)
        # Use shutil.move to handle overwrites
        shutil.move(source, destination)
        print(f"  Moved: {file}")
    print("Legacy files moved successfully.\n")

# =============================================================================
# 1. Generate Sellside Highlights Markdown
# =============================================================================
sellside_md = f'{output_dir}/{friday_date}_sellside_highlights.md'

if os.path.exists(sellside_md):
    print(f"Sellside highlights already exists: {sellside_md}, skipping...")
else:
    with open(sellside_md, 'w', encoding='utf-8') as f:
        # Research reports for the week
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
                            f.write(f'**{line.replace("**","").strip()}**\n\n')
                        elif len(line) > 10:
                            f.write(f'- {line.replace("*","").replace("**","").replace("- ","").replace("#","").strip()}\n')
                
                # Handle PDF file copying and link generation
                parts = file.split('-')
                if len(parts) > 1:
                    file_id = parts[-1].replace('.pdf', '')
                    new_filename = f"{file_id}.pdf"
                    source_path = os.path.join(raw_path, file)
                    destination_path = os.path.join(cdn_path, new_filename)
                    shutil.copy2(source_path, destination_path)
                    f.write(f'\n[Report Link](https://auto.bda-news.com/{friday_date}/{file_id}.pdf)\n\n')

    print(f"Sellside highlights generated: {sellside_md}")

# =============================================================================
# 2. Generate Key News Takeaway Markdown
# =============================================================================
takeaway_md = f'{output_dir}/{friday_date}_key_takeaway.md'

if os.path.exists(takeaway_md):
    print(f"Key takeaway already exists: {takeaway_md}, skipping...")
else:
    with open(takeaway_md, 'w', encoding='utf-8') as f:
        # Key takeaway for the week
        summary_md = open(f'data/5_summary_mds/{friday_date}_summary.md', 'r', encoding='utf-8').read()

        f.write(f'# Key News takeaway for Week – {friday_date}\n\n')
        
        # Parse the summary markdown and add headings and paragraphs
        lines = summary_md.strip().split('\n')
        for line in lines:
            if line.startswith('##'):
                f.write('\n')
                f.write(f'{line}\n\n')
            elif len(line) > 10 and line.startswith('#'):
                f.write(f'- {line.replace("*","").replace("**","").replace("- ","").replace("#","").strip()}\n')

    print(f"Key takeaway generated: {takeaway_md}")

# =============================================================================
# 3. Generate Detailed News Markdown
# =============================================================================
detailed_md = f'{output_dir}/{friday_date}_detailed_news.md'

if os.path.exists(detailed_md):
    print(f"Detailed news already exists: {detailed_md}, skipping...")
else:
    with open(detailed_md, 'w', encoding='utf-8') as f:
        # Detailed News for the week
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
            
            f.write(f'## {sector}\n\n')
            
            for _, row in news_df_sector.iterrows():
                f.write(f'### {row["title"]}\n\n')
            
                if 'link' in row and not pd.isna(row['link']):
                    f.write(f'[原文链接]({row["link"]})\n\n')
                
                if 'author' in row and not pd.isna(row['author']):
                    if 'date' in row and not pd.isna(row['date']):
                        f.write(f'*{row["date"]} - {row["author"]}*\n\n')
                    else:
                        f.write(f'*{row["author"]}*\n\n')
                
                if 'content' in row and not pd.isna(row['content']):
                    f.write(f'{row["content"]}\n\n')

    print(f"Detailed news generated: {detailed_md}")

# =============================================================================
# 4. Generate Podcast Summary Markdown
# =============================================================================
import re
from pathlib import Path

# Try project directory first, then home directory
podcast_dir = Path(f'podcast/{friday_date}')
if not podcast_dir.exists():
    podcast_dir = Path.home() / 'podcast' / friday_date

podcast_md = f'{output_dir}/{friday_date}_podcast_summary.md'

if podcast_dir.exists():
    if os.path.exists(podcast_md):
        print(f"\nPodcast summary already exists: {podcast_md}, skipping...")
    else:
        print(f"\nProcessing podcast summaries from {podcast_dir}")
        
        # Get all markdown files in the podcast directory
        podcast_files = sorted(podcast_dir.glob('*.md'))
        
        if podcast_files:
            with open(podcast_md, 'w', encoding='utf-8') as f:
                f.write(f'# Podcast Summary for Week – {friday_date}\n\n')
                
                for podcast_file in podcast_files:
                    print(f"Processing podcast: {podcast_file.name}")
                    
                    try:
                        content = podcast_file.read_text(encoding='utf-8')
                        lines = content.strip().split('\n')
                        
                        # Extract podcast info, summary and takeaways
                        episode_title = ""
                        podcast_name = ""
                        publish_time = ""
                        summary_text = ""
                        bullets = []
                        in_summary = False
                        in_takeaways = False
                        
                        for i, line in enumerate(lines):
                            # Extract podcast info
                            if line.startswith('- Podcast:'):
                                podcast_name = line.replace('- Podcast:', '').strip()
                            elif line.startswith('- Episode:'):
                                episode_title = line.replace('- Episode:', '').strip()
                            elif line.startswith('- Publish Time:'):
                                publish_time = line.replace('- Publish Time:', '').strip()
                            # Check for Summary section
                            elif line.strip() == '# Summary':
                                in_summary = True
                                in_takeaways = False
                            # Check for Takeaways section  
                            elif line.strip() == '# Takeaways':
                                in_summary = False
                                in_takeaways = True
                            # Check for other sections (end of takeaways)
                            elif line.startswith('# ') and line.strip() not in ['# Info', '# Summary', '# Takeaways']:
                                in_summary = False
                                in_takeaways = False
                            # Extract summary content
                            elif in_summary and line.strip() and not line.startswith('#'):
                                if summary_text:
                                    summary_text += " " + line.strip()
                                else:
                                    summary_text = line.strip()
                            # Extract takeaway bullets
                            elif in_takeaways and line.strip().startswith('*'):
                                bullets.append(line.strip().replace('*', '-'))
                        
                        # Write formatted content
                        if podcast_name and episode_title:
                            if publish_time:
                                f.write(f'## [{podcast_name}] {episode_title}, {publish_time}\n\n')
                            else:
                                f.write(f'## [{podcast_name}] {episode_title}\n\n')
                        elif episode_title:
                            if publish_time:
                                f.write(f'## {episode_title}, {publish_time}\n\n')
                            else:
                                f.write(f'## {episode_title}\n\n')
                        
                        if summary_text:
                            f.write(f'{summary_text}\n\n')
                        
                        if bullets:
                            for bullet in bullets:
                                f.write(f'{bullet}\n')
                            f.write('\n')
                        
                    except Exception as e:
                        print(f"Error processing {podcast_file.name}: {str(e)}")
                        continue
        
            print(f"Podcast summary generated: {podcast_md}")
        else:
            print(f"No podcast files found in {podcast_dir}")
else:
    print(f"\nPodcast directory {podcast_dir} does not exist, skipping podcast summary")

# Final summary of generated files
generated_files = []
if os.path.exists(sellside_md):
    generated_files.append(sellside_md)
if os.path.exists(takeaway_md):
    generated_files.append(takeaway_md)
if os.path.exists(detailed_md):
    generated_files.append(detailed_md)
if os.path.exists(podcast_md):
    generated_files.append(podcast_md)

if generated_files:
    print(f"\n{len(generated_files)} markdown file(s) exist or were generated:")
    for i, file in enumerate(generated_files, 1):
        print(f"{i}. {file}")
else:
    print("\nNo markdown files were generated (all already existed).") 