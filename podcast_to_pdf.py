#!/usr/bin/env python3
"""
Convert translated podcast markdown files to PDF
Uses WeasyPrint with professional styling similar to the main PDF generator
"""

import os
import re
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

def create_podcast_html(markdown_content, podcast_title):
    """Convert podcast markdown to styled HTML"""
    
    # Extract podcast name from title if available
    title_match = re.search(r'Episode:\s*(.+)', markdown_content)
    if title_match:
        full_title = title_match.group(1)
    else:
        full_title = podcast_title
    
    # Convert markdown to HTML
    md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists', 'tables'])
    html_body = md_converter.convert(markdown_content)
    
    # Process HTML for better structure
    # Add special styling for Q&A section
    html_body = html_body.replace('<h1>Q &amp; A</h1>', '<h1 class="qa-section">Q &amp; A</h1>')
    html_body = html_body.replace('<h1>Keywords</h1>', '<h1 class="keywords-section">Keywords</h1>')
    html_body = html_body.replace('<h1>Highlights</h1>', '<h1 class="highlights-section">Highlights</h1>')
    
    # Wrap Q&A items for better styling
    html_body = re.sub(r'<p><strong>Q:', r'<div class="qa-item"><p class="question"><strong>Q:', html_body)
    html_body = re.sub(r'</p>\n<hr />', r'</p></div>\n<hr class="qa-separator" />', html_body)
    
    # Build complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{full_title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: 'Inter', 'Arial', 'Helvetica', sans-serif;
                font-size: 11pt;
                line-height: 1.4;
                color: #2c3e50;
                background: #ffffff;
                margin: 0;
                padding: 0;
            }}
            
            .content {{
                padding: 0;
                margin: 0;
            }}
            
            /* Cover page title */
            .cover-title {{
                margin-top: 3cm;
                text-align: center;
                font-size: 24pt;
                font-weight: 700;
                color: #2c3e50;
                line-height: 1.3;
                padding: 0 2cm;
                page-break-after: always;
            }}
            
            h1 {{
                font-size: 20pt;
                font-weight: 700;
                margin-top: 0.8em;
                margin-bottom: 0.4em;
                color: #2c3e50;
                border-bottom: 3px solid #2E7D32;
                padding-bottom: 0.3em;
                page-break-after: avoid;
            }}
            
            h1:first-of-type {{
                margin-top: 0.5em;
            }}
            
            /* Special sections */
            h1.qa-section {{
                border-bottom-color: #1976D2;
            }}
            
            h1.keywords-section {{
                border-bottom-color: #7B1FA2;
            }}
            
            h1.highlights-section {{
                border-bottom-color: #D32F2F;
            }}
            
            h2 {{
                font-size: 16pt;
                font-weight: 600;
                margin-top: 0.6em;
                margin-bottom: 0.3em;
                color: #34495e;
                border-left: 4px solid #43A047;
                padding-left: 0.5em;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 13pt;
                font-weight: 600;
                margin-top: 0.5em;
                margin-bottom: 0.3em;
                color: #2c3e50;
                page-break-after: avoid;
            }}
            
            p {{
                margin-bottom: 0.6em;
                text-align: justify;
                text-justify: inter-word;
            }}
            
            /* Info section styling */
            ul {{
                margin: 0.3em 0 0.6em 1.5em;
                padding: 0;
            }}
            
            li {{
                margin-bottom: 0.3em;
                line-height: 1.4;
            }}
            
            ul li {{
                list-style-type: none;
                position: relative;
                padding-left: 1.5em;
            }}
            
            ul li:before {{
                content: "•";
                position: absolute;
                left: 0;
                color: #43A047;
                font-weight: bold;
                font-size: 1.2em;
            }}
            
            /* Q&A styling */
            .qa-item {{
                margin: 1em 0;
                padding: 0.8em;
                background: #f8f9fa;
                border-left: 3px solid #1976D2;
                border-radius: 4px;
            }}
            
            .qa-item .question {{
                color: #1976D2;
                font-weight: 600;
                margin-bottom: 0.5em;
            }}
            
            hr.qa-separator {{
                margin: 1.5em 0;
                border: none;
                border-top: 1px dashed #bdc3c7;
            }}
            
            /* Table styling for Keywords section */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }}
            
            th {{
                background-color: #f5f5f5;
                font-weight: 600;
                padding: 0.6em;
                text-align: left;
                border: 1px solid #ddd;
                color: #2c3e50;
            }}
            
            td {{
                padding: 0.6em;
                border: 1px solid #ddd;
                vertical-align: top;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            /* Links */
            a {{
                color: #3498db;
                text-decoration: none;
                border-bottom: 1px dotted #3498db;
            }}
            
            a:hover {{
                color: #2980b9;
                border-bottom-style: solid;
            }}
            
            /* Emphasis and strong */
            em {{
                font-style: italic;
                color: #7f8c8d;
            }}
            
            strong {{
                font-weight: 600;
                color: #2c3e50;
            }}
            
            /* Blockquotes */
            blockquote {{
                margin: 0.5em 0;
                padding: 0.8em;
                background: #f5f5f5;
                border-left: 4px solid #66BB6A;
                font-style: italic;
            }}
            
            /* Page breaks */
            .section-break {{
                page-break-before: always;
                padding-top: 0;
                margin-top: 0;
            }}
            
            /* Transcript section - smaller font for long content */
            h1:contains("Transcript") + * {{
                font-size: 10pt;
            }}
            
            @page {{
                size: A4;
                margin: 2cm 1.5cm;
                
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                    font-family: 'Inter', sans-serif;
                }}
                
                @top-right {{
                    content: "Podcast Transcript";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: 'Inter', sans-serif;
                }}
            }}
            
            @page :first {{
                @top-right {{
                    content: "";
                }}
            }}
            
            @media print {{
                .section-break {{
                    page-break-before: always;
                }}
                
                .qa-item {{
                    page-break-inside: avoid;
                }}
                
                h1, h2, h3 {{
                    page-break-after: avoid;
                }}
                
                table {{
                    page-break-inside: auto;
                }}
                
                tr {{
                    page-break-inside: avoid;
                    page-break-after: auto;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_body}
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_podcast_pdf(input_file, output_file):
    """Generate PDF from a single podcast markdown file"""
    
    print(f"  Processing: {input_file.name}")
    
    try:
        # Read markdown content
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Extract title from filename (remove .md extension)
        podcast_title = input_file.stem
        
        # Create HTML content
        html_content = create_podcast_html(markdown_content, podcast_title)
        
        # Generate PDF
        print(f"    Converting to PDF...")
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { 
                    size: A4; 
                    margin: 2cm 1.5cm;
                }
                @page :first {
                    margin-top: 2cm;
                }
            ''')]
        )
        
        # Check file size
        file_size = output_file.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"    ✓ PDF generated ({file_size:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Failed to generate PDF: {e}")
        return False

def main():
    """Main function to convert all translated podcast markdown files to PDFs"""
    
    # Use specific date for podcast processing (hardcoded as requested)
    friday_date = '2025-08-29'
    
    # Directory paths
    podcast_eng_dir = Path('podcast') / f'{friday_date}_ENG'
    podcast_pdf_dir = Path('podcast') / f'{friday_date}_ENG_PDFs'
    
    print("=" * 60)
    print("📚 Podcast Markdown to PDF Converter")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {podcast_eng_dir}")
    print(f"Output: {podcast_pdf_dir}")
    print("=" * 60)
    
    # Check if source directory exists
    if not podcast_eng_dir.exists():
        print(f"\n❌ Source directory not found: {podcast_eng_dir}")
        print("Please run the translation script first.")
        return False
    
    # Find all markdown files
    md_files = list(podcast_eng_dir.glob('*.md'))
    
    if not md_files:
        print(f"\n❌ No markdown files found in {podcast_eng_dir}")
        return False
    
    print(f"\n📋 Found {len(md_files)} markdown files to convert")
    
    # Create output directory
    podcast_pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each file
    successful = 0
    failed = 0
    
    print("\n🔄 Converting markdown files to PDF...")
    for md_file in md_files:
        output_file = podcast_pdf_dir / f"{md_file.stem}.pdf"
        
        # Skip if PDF already exists
        if output_file.exists():
            print(f"  ⏭️  Skipping (already exists): {md_file.name}")
            successful += 1
            continue
        
        if generate_podcast_pdf(md_file, output_file):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Conversion Summary")
    print("=" * 60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 PDFs saved to: {podcast_pdf_dir}")
    
    # List generated PDFs
    pdf_files = list(podcast_pdf_dir.glob('*.pdf'))
    if pdf_files:
        print(f"\n📄 Generated PDFs ({len(pdf_files)} files):")
        for pdf_file in pdf_files:
            file_size = pdf_file.stat().st_size / (1024 * 1024)
            print(f"  • {pdf_file.name} ({file_size:.2f} MB)")
    
    print("\n" + "=" * 60)
    
    return successful > 0

if __name__ == '__main__':
    success = main()
    if success:
        print("\n✨ PDF generation completed successfully!")
    else:
        print("\n⚠️ PDF generation encountered issues")