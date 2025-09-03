#!/usr/bin/env python3
"""
Generate English PDF from existing or translated markdown files
This script creates a professional English PDF, using existing translations if available
"""

import os
import sys
from pathlib import Path
import datetime
import markdown
from weasyprint import HTML, CSS
from parameters import friday_date

def create_combined_english_html():
    """Create combined HTML from English markdown files"""
    
    # Input markdown files - try English versions first, fallback to Chinese
    input_dir = Path('data/6_final_mds')
    
    # Check for existing English files first
    sellside_eng_md = input_dir / f'{friday_date}_sellside_highlights_english.md'
    takeaway_eng_md = input_dir / f'{friday_date}_key_takeaway_english.md'
    detailed_eng_md = input_dir / f'{friday_date}_detailed_news_english.md'
    
    # Fallback to Chinese files if English don't exist
    sellside_md = sellside_eng_md if sellside_eng_md.exists() else input_dir / f'{friday_date}_sellside_highlights.md'
    takeaway_md = takeaway_eng_md if takeaway_eng_md.exists() else input_dir / f'{friday_date}_key_takeaway.md'
    detailed_md = detailed_eng_md if detailed_eng_md.exists() else input_dir / f'{friday_date}_detailed_news.md'
    
    html_content = []
    
    # Add HTML header with CSS styling for English
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
                line-height: 1.7;
                color: #2c3e50;
                background: #ffffff;
                margin: 0;
                padding: 0;
            }
            
            .cover-page {
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                page-break-after: always;
                background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
                color: white;
                padding: 2em;
            }
            
            .cover-page h1 {
                font-size: 42pt;
                font-weight: 700;
                margin-bottom: 0.3em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                letter-spacing: -1px;
            }
            
            .cover-page .subtitle {
                font-size: 18pt;
                font-weight: 300;
                margin-bottom: 1.5em;
                opacity: 0.95;
                letter-spacing: 1px;
            }
            
            .cover-page .week-info {
                font-size: 16pt;
                font-weight: 500;
                margin-bottom: 3em;
                padding: 0.5em 2em;
                border: 2px solid rgba(255,255,255,0.5);
                border-radius: 30px;
                background: rgba(255,255,255,0.1);
            }
            
            .cover-page .date {
                font-size: 13pt;
                font-weight: 400;
                position: absolute;
                bottom: 3em;
                opacity: 0.9;
            }
            
            .content {
                padding: 2.5cm 2cm;
                max-width: 21cm;
                margin: 0 auto;
            }
            
            .toc {
                page-break-after: always;
                padding: 2.5cm 2cm;
            }
            
            .toc h2 {
                font-size: 28pt;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 1em;
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 0.5em;
            }
            
            .toc-item {
                font-size: 13pt;
                margin: 1em 0;
                padding-left: 1em;
                border-left: 3px solid transparent;
                transition: all 0.3s;
            }
            
            .toc-item:hover {
                border-left-color: #3498db;
                padding-left: 1.5em;
            }
            
            .toc-item a {
                color: #34495e;
                text-decoration: none;
            }
            
            h1 {
                font-size: 24pt;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 1em;
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 0.3em;
                page-break-after: avoid;
            }
            
            h2 {
                font-size: 18pt;
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 0.5em;
                background: #ecf0f1;
                padding: 0.3em 0.5em;
                page-break-after: avoid;
            }
            
            h3 {
                font-size: 14pt;
                font-weight: 600;
                margin-top: 1.2em;
                margin-bottom: 0.6em;
                color: #2c3e50;
                page-break-after: avoid;
            }
            
            p {
                margin-bottom: 1em;
                text-align: justify;
                text-justify: inter-word;
            }
            
            ul, ol {
                margin: 0.5em 0 1em 2em;
                padding: 0;
            }
            
            li {
                margin-bottom: 0.5em;
                line-height: 1.7;
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
                color: #3498db;
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
                margin: 1em 0;
                padding: 1em;
                background: #ecf0f1;
                border-left: 4px solid #3498db;
                font-style: italic;
            }
            
            .section-break {
                page-break-before: always;
                padding-top: 2.5cm;
            }
            
            .news-item {
                margin-bottom: 2em;
                padding-bottom: 1em;
                border-bottom: 1px dashed #bdc3c7;
            }
            
            .news-item:last-child {
                border-bottom: none;
            }
            
            .news-meta {
                font-size: 10pt;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 0.5em;
            }
            
            .highlight-box {
                background: #e8f4f8;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 1em;
                margin: 1em 0;
            }
            
            @page {
                size: A4;
                margin: 2cm;
                
                @bottom-center {
                    content: "Page " counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                    font-family: 'Inter', sans-serif;
                }
                
                @top-right {
                    content: "Autonomous Driving AI News";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: 'Inter', sans-serif;
                }
            }
            
            @page:first {
                @bottom-center { content: none; }
                @top-right { content: none; }
                margin: 0;
            }
            
            @page:nth(2) {
                @bottom-center { content: none; }
                @top-right { content: none; }
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
    
    # Add cover page
    current_date = datetime.datetime.now().strftime('%B %d, %Y')
    week_date = datetime.datetime.strptime(friday_date, '%Y-%m-%d').strftime('%B %d, %Y')
    
    html_content.append(f"""
        <div class="cover-page">
            <h1>Autonomous Driving AI</h1>
            <div class="subtitle">Weekly News Summary</div>
            <div class="week-info">Week Ending {week_date}</div>
            <div class="date">Generated on {current_date}</div>
        </div>
    """)
    
    # Add table of contents
    html_content.append("""
        <div class="toc">
            <h2>Table of Contents</h2>
            <div class="toc-item">
                <a href="#sellside">1. Sellside Research Highlights</a>
            </div>
            <div class="toc-item">
                <a href="#takeaway">2. Key News Takeaway</a>
            </div>
            <div class="toc-item">
                <a href="#detailed">3. Detailed News</a>
            </div>
        </div>
    """)
    
    # Process each markdown file
    sections = [
        ('sellside', sellside_md, 'Sellside Research Highlights'),
        ('takeaway', takeaway_md, 'Key News Takeaway'),
        ('detailed', detailed_md, 'Detailed News')
    ]
    
    for section_id, md_file, section_title in sections:
        if not md_file.exists():
            print(f"Warning: {md_file} not found, skipping...")
            continue
        
        print(f"Processing {md_file.name}...")
        
        # Add section break
        html_content.append(f'<div class="section-break content" id="{section_id}">')
        
        # Read markdown
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
    print("📄 English PDF Generator (Simple Version)")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path('data/7_pdfs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML content
    print("📝 Generating content from existing English files...")
    html_content = create_combined_english_html()
    
    # Generate output filename
    output_file = output_dir / f'Autonomous Driving AI News Summary {friday_date.replace("-", " ")}_ENG.pdf'
    
    try:
        print("🔄 Converting to PDF...")
        
        # Create PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { size: A4; margin: 2cm; }
                @page:first { margin: 0; }
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
        print("Note: This version uses existing English translations if available")
    else:
        print("\n⚠️ Error occurred during PDF generation, please check logs")
        sys.exit(1)

if __name__ == "__main__":
    main()