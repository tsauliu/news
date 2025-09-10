#!/usr/bin/env python3
"""
Generate Chinese PDF from markdown files
This script reads three markdown files and creates a professional PDF with Chinese support
"""

import os
import sys
from pathlib import Path
import datetime
import markdown
from weasyprint import HTML, CSS
from parameters import friday_date

def create_combined_html():
    """Create combined HTML from three markdown files"""
    
    # Input markdown files
    input_dir = Path('data/6_final_mds')
    sellside_md = input_dir / f'{friday_date}_sellside_highlights.md'
    takeaway_md = input_dir / f'{friday_date}_key_takeaway.md'
    detailed_md = input_dir / f'{friday_date}_detailed_news.md'
    
    html_content = []
    
    # Add HTML header with CSS styling for Chinese
    html_content.append("""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>自动驾驶AI新闻摘要 - {friday_date}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
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
                    font-family: 'Noto Sans SC', sans-serif;
                }
                
                @top-right {
                    content: "BDA Autonomous Driving New Update";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: 'Noto Sans SC', sans-serif;
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
    
    # Process each markdown file - reordered with takeaway first
    sections = [
        ('takeaway', takeaway_md, '本周要闻提炼'),
        ('sellside', sellside_md, '卖方研究精选'),
        ('detailed', detailed_md, '详细新闻内容')
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

def generate_pdf():
    """Generate PDF from HTML content"""
    
    print("=" * 50)
    print("📄 中文PDF生成器 (Chinese PDF Generator)")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path('data/7_pdfs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML content
    print("📝 生成HTML内容...")
    html_content = create_combined_html()
    
    # Generate output filename
    output_file = output_dir / f'Autonomous Driving AI News Summary {friday_date.replace("-", " ")}.pdf'
    
    try:
        print("🔄 转换为PDF...")
        
        # Create PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { size: A4; margin: 2cm 1cm; }
            ''')]
        )
        
        # Check file size
        file_size = output_file.stat().st_size / (1024 * 1024)  # Convert to MB
        
        print(f"✅ PDF生成成功!")
        print(f"📁 文件位置: {output_file}")
        print(f"📊 文件大小: {file_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = generate_pdf()
    
    if success:
        print("\n✨ 中文PDF文档生成完成!")
    else:
        print("\n⚠️ PDF生成过程中出现错误，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    main()