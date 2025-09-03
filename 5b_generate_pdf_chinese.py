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
                line-height: 1.8;
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2em;
            }
            
            .cover-page h1 {
                font-size: 36pt;
                font-weight: 700;
                margin-bottom: 0.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .cover-page .subtitle {
                font-size: 18pt;
                font-weight: 300;
                margin-bottom: 2em;
                opacity: 0.95;
            }
            
            .cover-page .date {
                font-size: 14pt;
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
                font-size: 24pt;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 1em;
                text-align: center;
                border-bottom: 3px solid #667eea;
                padding-bottom: 0.5em;
            }
            
            .toc-item {
                font-size: 12pt;
                margin: 0.8em 0;
                padding-left: 1em;
                border-left: 3px solid transparent;
                transition: all 0.3s;
            }
            
            .toc-item:hover {
                border-left-color: #667eea;
                padding-left: 1.5em;
            }
            
            .toc-item a {
                color: #34495e;
                text-decoration: none;
            }
            
            .toc-item .page-num {
                float: right;
                color: #7f8c8d;
            }
            
            h1 {
                font-size: 22pt;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 1em;
                color: #2c3e50;
                border-bottom: 3px solid #667eea;
                padding-bottom: 0.3em;
                page-break-after: avoid;
            }
            
            h2 {
                font-size: 16pt;
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
                color: #34495e;
                border-left: 4px solid #667eea;
                padding-left: 0.5em;
                background: #f8f9fa;
                padding: 0.3em 0.5em;
                page-break-after: avoid;
            }
            
            h3 {
                font-size: 13pt;
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
                line-height: 1.8;
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
                color: #667eea;
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
                border-left: 4px solid #667eea;
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
                background: #fff9e6;
                border: 2px solid #f1c40f;
                border-radius: 8px;
                padding: 1em;
                margin: 1em 0;
            }
            
            @page {
                size: A4;
                margin: 2cm;
                
                @bottom-center {
                    content: counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                    font-family: 'Noto Sans SC', sans-serif;
                }
                
                @top-right {
                    content: "自动驾驶AI新闻摘要";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: 'Noto Sans SC', sans-serif;
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
    current_date = datetime.datetime.now().strftime('%Y年%m月%d日')
    week_date = friday_date.replace('-', '年', 1).replace('-', '月', 1) + '日'
    
    html_content.append(f"""
        <div class="cover-page">
            <h1>自动驾驶AI新闻周报</h1>
            <div class="subtitle">Autonomous Driving AI Weekly News Summary</div>
            <div class="subtitle">第 {week_date} 期</div>
            <div class="date">生成日期: {current_date}</div>
        </div>
    """)
    
    # Add table of contents
    html_content.append("""
        <div class="toc">
            <h2>目录</h2>
            <div class="toc-item">
                <a href="#sellside">一、卖方研究精选 (Sellside Highlights)</a>
            </div>
            <div class="toc-item">
                <a href="#takeaway">二、本周要闻提炼 (Key News Takeaway)</a>
            </div>
            <div class="toc-item">
                <a href="#detailed">三、详细新闻内容 (Detailed News)</a>
            </div>
        </div>
    """)
    
    # Process each markdown file
    sections = [
        ('sellside', sellside_md, '卖方研究精选'),
        ('takeaway', takeaway_md, '本周要闻提炼'),
        ('detailed', detailed_md, '详细新闻内容')
    ]
    
    for section_id, md_file, section_title in sections:
        if not md_file.exists():
            print(f"Warning: {md_file} not found, skipping...")
            continue
        
        # Add section break
        html_content.append(f'<div class="section-break content" id="{section_id}">')
        
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
                @page { size: A4; margin: 2cm; }
                @page:first { margin: 0; }
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