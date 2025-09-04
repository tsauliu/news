#!/usr/bin/env python3
"""
Generate English PDF from translated markdown files
This script translates Chinese content and creates a professional English PDF
"""

import os
import sys
from pathlib import Path
import datetime
import markdown
from weasyprint import HTML, CSS
from parameters import friday_date
from models import deepseek_model, gemini_model
import pandas as pd
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Thread lock for print statements
print_lock = threading.Lock()

def safe_print(message):
    """Thread-safe print function"""
    with print_lock:
        print(message)

# Translation prompt for DeepSeek (line by line translation)
translation_prompt = """You are a professional translator specializing in automotive industry content. 
Translate the following Chinese text to natural, accurate English. 
Context: This is automotive industry news, research reports, and market analysis.
Requirements:
1. Maintain professional automotive terminology
2. Keep the original meaning and tone
3. Use natural, native English expressions
4. Keep company names, brand names, or proper nouns accurate
5. Keep technical terms accurate
6. Only return the translated text, no explanations or additional content
7. IMPORTANT: Your output must be ENGLISH ONLY - no Chinese characters allowed in the response
8. If the input is already in English, return it unchanged
9. Never include any Chinese text in your response under any circumstances

Specific translation guidelines for key terms:
- 商业落地 → Commercialization
- 核心技术 → New Technology
- 政策监管 → Policy Regulation
- 企业战略 → Corporate Strategy
- 硬件设备 → Hardware
- 资本动向 → Capital Trends

Please translate the following text:
"""

# Special translation prompt for Gemini (full file translation)
gemini_translation_prompt = """You are a professional translator specializing in automotive industry content. 
Translate the following Chinese text to natural, accurate English. 
Context: This is automotive industry news, research reports, and market analysis.

CRITICAL FORMATTING REQUIREMENTS:
1. ONLY translate text content - DO NOT modify any formatting or structure
2. Keep ALL markdown formatting (headers #, ##, ###, bullet points -, etc.)
3. Keep ALL links COMPLETELY unchanged (URLs and markdown link syntax)
4. Preserve ALL line breaks and spacing structure
5. Do not add, remove, or modify any special characters or symbols

Translation Requirements:
1. Maintain professional automotive terminology
2. Keep the original meaning and tone
3. Use natural, native English expressions
4. Keep company names, brand names, or proper nouns accurate
5. Keep technical terms accurate
6. IMPORTANT: Your output must be ENGLISH ONLY - no Chinese characters allowed in the response
7. If text is already in English, keep it unchanged
8. Never include any Chinese text in your response under any circumstances

Specific translation guidelines for key terms:
- 商业落地 → Commercialization
- 核心技术 → New Technology
- 政策监管 → Policy Regulation
- 企业战略 → Corporate Strategy
- 硬件设备 → Hardware
- 数据与地图 → Data & Mapping
- 资本动向 → Capital Trends

REMEMBER: Only translate the text content, preserve all formatting exactly as it is.

Please translate the following text:
"""

def translate_with_gemini(text):
    """Translate entire file content using Gemini model with retries"""
    if not text or len(text.strip()) < 3:
        return text
    
    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            translated = gemini_model(gemini_translation_prompt, text)
            return translated.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # 5, 10, 20 seconds
                safe_print(f"Gemini translation error (attempt {attempt + 1}/{max_retries}): {e}")
                safe_print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                safe_print(f"Gemini translation failed after {max_retries} attempts: {e}")
                return ""  # Return blank instead of Chinese text

def translate_with_deepseek(text):
    """Translate text using DeepSeek model with retries"""
    if not text or len(text.strip()) < 3:
        return text
    
    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            translated = deepseek_model(translation_prompt, text)
            return translated.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # 5, 10, 20 seconds
                safe_print(f"DeepSeek translation error (attempt {attempt + 1}/{max_retries}): {e}")
                safe_print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                safe_print(f"DeepSeek translation failed after {max_retries} attempts: {e}")
                return ""  # Return blank instead of Chinese text

def translate_file_with_gemini(input_file, output_file):
    """Translate entire file using Gemini"""
    print(f"Translating {input_file} with Gemini...")
    
    if not os.path.exists(input_file):
        print(f"Warning: File {input_file} not found, skipping...")
        return False
    
    # Read the entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Translate the entire content
    translated_content = translate_with_gemini(content)
    
    if not translated_content:
        print(f"Warning: Translation failed for {input_file}")
        return False
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    print(f"Gemini translation completed: {output_file}")
    return True

def translate_line(line):
    """Translate a single line"""
    # Skip very short lines
    if len(line.strip()) < 3:
        return line
    
    # For headers, extract text after # symbols and translate
    if line.startswith('#'):
        # Count the number of # symbols
        header_level = len(line) - len(line.lstrip('#'))
        header_text = line[header_level:].strip()
        
        # Translate the header text
        translated = translate_with_deepseek(header_text)
        if translated:
            return '#' * header_level + ' ' + translated
        else:
            return line
    
    # Handle links with Chinese text
    if line.startswith('[') and '](' in line:
        # Extract link text and URL
        import re
        match = re.match(r'\[(.*?)\]\((.*?)\)', line)
        if match:
            link_text = match.group(1)
            url = match.group(2)
            
            # Always translate "原文链接" to "Original Article"
            if link_text == '原文链接':
                return f'[Original Article]({url})'
            # Translate link text if it's in Chinese
            elif any('\u4e00' <= c <= '\u9fff' for c in link_text):
                translated = translate_with_deepseek(link_text)
                if translated:
                    return f'[{translated}]({url})'
        return line
    
    # Handle metadata lines (date and author)
    if line.startswith('*') and line.endswith('*'):
        # Extract content between asterisks
        content = line[1:-1].strip()
        
        # Check if it contains Chinese
        if any('\u4e00' <= c <= '\u9fff' for c in content):
            # Split by dash to preserve date format
            parts = content.split(' - ')
            if len(parts) == 2:
                date_part = parts[0]
                author_part = parts[1]
                
                # Translate Chinese month names if present
                date_translated = date_part.replace('年', '-').replace('月', '-').replace('日', '')
                
                # Translate author part
                author_translated = translate_with_deepseek(author_part)
                if author_translated:
                    return f'*{date_translated} - {author_translated}*'
            else:
                # Just translate the whole content
                translated = translate_with_deepseek(content)
                if translated:
                    return f'*{translated}*'
        return line
    
    # Translate regular lines
    translated = translate_with_deepseek(line)
    return translated if translated else line

def translate_detailed_news_with_deepseek(input_file, output_file):
    """Translate detailed news file line by line using DeepSeek"""
    print(f"Translating {input_file} with DeepSeek (line by line)...")
    
    if not os.path.exists(input_file):
        print(f"Warning: File {input_file} not found, skipping...")
        return False
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Filter lines that need translation
    lines_to_translate = []
    line_indices = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Translate all non-empty lines (including links)
        if stripped:
            lines_to_translate.append(line)
            line_indices.append(i)
    
    print(f"Found {len(lines_to_translate)} lines to translate")
    
    # Use ThreadPoolExecutor for multi-threading
    max_workers = 50  # Adjust based on your system and API limits
    translated_results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks - don't strip lines to preserve headers
        future_to_index = {
            executor.submit(translate_line, line.rstrip('\n')): (idx, line)
            for idx, line in zip(line_indices, lines_to_translate)
        }
        
        # Process completed translations with progress bar
        with tqdm(total=len(future_to_index), desc="Translating with DeepSeek") as pbar:
            for future in as_completed(future_to_index):
                idx, original_line = future_to_index[future]
                try:
                    result = future.result()
                    if result:
                        translated_results[idx] = result + '\n' if not result.endswith('\n') else result
                    else:
                        translated_results[idx] = original_line
                    pbar.update(1)
                except Exception as e:
                    safe_print(f"Translation task failed: {e}")
                    translated_results[idx] = original_line
                    pbar.update(1)
    
    # Reconstruct the file with translated content
    output_lines = []
    for i, line in enumerate(lines):
        if i in translated_results:
            output_lines.append(translated_results[i])
        else:
            output_lines.append(line)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"DeepSeek translation completed: {output_file}")
    return True

def translate_podcast_files():
    """Translate podcast markdown files from YYYY-MM-DD to YYYY-MM-DD_ENG"""
    
    podcast_dir = Path('podcast') / friday_date
    podcast_eng_dir = Path('podcast') / f'{friday_date}_ENG'
    
    # Check if source podcast directory exists
    if not podcast_dir.exists():
        print(f"\nℹ️ Podcast directory {podcast_dir} not found, skipping podcast translation")
        return False
    
    # Create English podcast directory
    podcast_eng_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all markdown files in the podcast directory
    md_files = list(podcast_dir.glob('*.md'))
    
    if not md_files:
        print(f"\nℹ️ No markdown files found in {podcast_dir}")
        return False
    
    print(f"\n=== Translating Podcast Files ===")
    print(f"Found {len(md_files)} podcast files to translate")
    
    success_count = 0
    for md_file in md_files:
        output_file = podcast_eng_dir / md_file.name
        
        # Skip if English version already exists
        if output_file.exists():
            print(f"✓ English version already exists: {output_file.name}")
            success_count += 1
            continue
        
        print(f"\nTranslating podcast: {md_file.name}")
        
        # Use Gemini for podcast translation (full file translation)
        if translate_file_with_gemini(md_file, output_file):
            success_count += 1
            print(f"✓ Translated: {md_file.name}")
        else:
            print(f"✗ Failed to translate: {md_file.name}")
    
    print(f"\n=== Podcast Translation Summary ===")
    print(f"Successfully translated {success_count}/{len(md_files)} podcast files")
    print(f"English podcasts saved to: {podcast_eng_dir}")
    
    return success_count == len(md_files)

def create_combined_english_html():
    """Create combined HTML from English markdown files"""
    
    # Input markdown files
    input_dir = Path('data/6_final_mds')
    
    # Define file paths for Chinese and English versions
    sellside_md = input_dir / f'{friday_date}_sellside_highlights.md'
    takeaway_md = input_dir / f'{friday_date}_key_takeaway.md'
    detailed_md = input_dir / f'{friday_date}_detailed_news.md'
    
    sellside_eng_md = input_dir / f'{friday_date}_sellside_highlights_english.md'
    takeaway_eng_md = input_dir / f'{friday_date}_key_takeaway_english.md'
    detailed_eng_md = input_dir / f'{friday_date}_detailed_news_english.md'
    
    # Translate files if English versions don't exist
    if not sellside_eng_md.exists() and sellside_md.exists():
        print("\n=== Translating Sellside Highlights ===")
        translate_file_with_gemini(sellside_md, sellside_eng_md)
    
    if not takeaway_eng_md.exists() and takeaway_md.exists():
        print("\n=== Translating Key Takeaway ===")
        translate_file_with_gemini(takeaway_md, takeaway_eng_md)
    
    if not detailed_eng_md.exists() and detailed_md.exists():
        print("\n=== Translating Detailed News ===")
        translate_detailed_news_with_deepseek(detailed_md, detailed_eng_md)
    
    html_content = []
    
    # Add HTML header with CSS styling matching Chinese version exactly
    html_content.append("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Autonomous Driving AI News Summary - {friday_date}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Inter', 'Arial', 'Helvetica', sans-serif;
                font-size: 11pt;
                line-height: 1.3;
                color: #2c3e50;
                background: #ffffff;
                margin: 0;
                padding: 0;
            }
            
            
            .content {
                padding: 0;
                margin: 0;
                padding-top: 0;
            }
            
            h1 {
                font-size: 22pt;
                font-weight: 700;
                margin-top: 0.8em;  /* Two lines from page top */
                margin-bottom: 0.3em;
                color: #2c3e50;
                border-bottom: 3px solid #2E7D32;
                padding-bottom: 0.2em;
                page-break-after: avoid;
            }
            
            /* First h1 on each page (after page break) */
            .section-break h1:first-child {
                margin-top: 0.8em;  /* Consistent two lines from page top */
            }
            
            h2 {
                font-size: 16pt;
                font-weight: 600;
                margin-top: 0.5em;
                margin-bottom: 0.3em;
                color: #34495e;
                border-left: 4px solid #43A047;
                padding-left: 0.5em;
                page-break-after: avoid;
            }
            
            h3 {
                font-size: 13pt;
                font-weight: 600;
                margin-top: 0.4em;
                margin-bottom: 0.2em;
                color: #2c3e50;
                page-break-after: avoid;
            }
            
            p {
                margin-bottom: 0.5em;
                text-align: justify;
                text-justify: inter-word;
            }
            
            ul, ol {
                margin: 0.3em 0 0.5em 2em;
                padding: 0;
            }
            
            li {
                margin-bottom: 0.3em;
                line-height: 1.3;
            }
            
            ul li {
                list-style-type: none;
                position: relative;
                padding-left: 1.5em;
            }
            
            ul li:before {
                content: "•";
                position: absolute;
                left: 0;
                color: #43A047;
                font-weight: bold;
                font-size: 1.2em;
            }
            
            a {
                color: #3498db;
                text-decoration: none;
                border-bottom: 1px dotted #3498db;
            }
            
            a:hover {
                color: #2980b9;
                border-bottom-style: solid;
            }
            
            em {
                font-style: italic;
                color: #7f8c8d;
            }
            
            strong {
                font-weight: 600;
                color: #2c3e50;
            }
            
            blockquote {
                margin: 0.3em 0;
                padding: 0.5em;
                background: #f5f5f5;
                border-left: 4px solid #66BB6A;
                font-style: italic;
            }
            
            .section-break {
                page-break-before: always;
                padding-top: 0;
                margin-top: 0;
            }
            
            .news-item {
                margin-bottom: 0.5em;
                padding-bottom: 0.3em;
                border-bottom: 1px dashed #bdc3c7;
            }
            
            .news-item:last-child {
                border-bottom: none;
            }
            
            .news-meta {
                font-size: 10pt;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 0.2em;
            }
            
            .highlight-box {
                background: #f9f9f9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 0.5em;
                margin: 0.3em 0;
            }
            
            @page {
                size: A4;
                margin: 2cm 1cm;
                
                @bottom-center {
                    content: counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                    font-family: 'Inter', sans-serif;
                }
                
                @top-right {
                    content: "BDA Autonomous Driving New Update";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: 'Inter', sans-serif;
                }
            }
            
            
            @media print {
                .cover-page {
                    height: 100vh;
                }
                
                .section-break {
                    page-break-before: always;
                }
            }
        </style>
    </head>
    <body>
    """.replace('{friday_date}', friday_date))
    
    # Process each markdown file - reordered with takeaway first (matching Chinese version)
    sections = [
        ('takeaway', takeaway_eng_md, 'Key News Takeaway'),
        ('sellside', sellside_eng_md, 'Sellside Research Highlights'),
        ('detailed', detailed_eng_md, 'Detailed News')
    ]
    
    for section_id, md_file, section_title in sections:
        if not md_file.exists():
            print(f"Warning: {md_file} not found, skipping...")
            continue
        
        # Add section break
        if section_id != 'takeaway':  # Only add section break for non-first sections
            html_content.append(f'<div class="section-break content" id="{section_id}">')
        else:
            html_content.append(f'<div class="content" id="{section_id}">')
        
        # Read and convert markdown to HTML
        with open(md_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # Convert markdown to HTML
        md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        html_from_md = md_converter.convert(markdown_text)
        
        # Process the HTML to add styling classes
        if section_id == 'detailed':
            # Wrap each news item for better styling
            html_from_md = html_from_md.replace('<h3>', '<div class="news-item"><h3>')
            html_from_md = html_from_md.replace('<h2>', '</div><h2>')
            html_from_md = html_from_md + '</div>'  # Close last news item
            html_from_md = html_from_md.replace('</div><h2>', '<h2>')  # Fix first occurrence
        
        html_content.append(html_from_md)
        html_content.append('</div>')  # Close section
    
    # Close HTML
    html_content.append('</body></html>')
    
    return '\n'.join(html_content)

def generate_english_pdf():
    """Generate English PDF from HTML content"""
    
    print("=" * 50)
    print("📄 English PDF Generator with Translation")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path('data/7_pdfs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Translate podcast files first (if they exist)
    translate_podcast_files()
    
    # Generate HTML content (includes translation if needed)
    print("\n📝 Generating English content...")
    html_content = create_combined_english_html()
    
    # Generate output filename
    output_file = output_dir / f'Autonomous Driving AI News Summary {friday_date.replace("-", " ")}_ENG.pdf'
    
    try:
        print("🔄 Converting to PDF...")
        
        # Create PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { size: A4; margin: 2cm 1cm; }
            ''')]
        )
        
        # Check file size
        file_size = output_file.stat().st_size / (1024 * 1024)  # Convert to MB
        
        print(f"✅ PDF generated successfully!")
        print(f"📁 File location: {output_file}")
        print(f"📊 File size: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = generate_english_pdf()
    
    if success:
        print("\n✨ English PDF document generated successfully!")
        print("Note: Content has been translated from Chinese to English")
        print("Note: Podcast files (if any) have been translated to podcast/{}_ENG".format(friday_date))
    else:
        print("\n⚠️ Error occurred during PDF generation, please check logs")
        sys.exit(1)

if __name__ == "__main__":
    main()