#!/usr/bin/env python3
"""
Generate English PDFs from translated podcast markdown files
"""

import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from parameters import friday_date

def create_podcast_html(md_file):
    """Create HTML from podcast markdown file"""
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Get podcast title from filename
    podcast_title = md_file.stem
    
    # Create HTML with CSS styling
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{podcast_title}</title>
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
                padding: 2em;
            }}
            
            h1 {{
                font-size: 22pt;
                font-weight: 700;
                margin-top: 0.8em;
                margin-bottom: 0.5em;
                color: #2c3e50;
                border-bottom: 3px solid #2E7D32;
                padding-bottom: 0.3em;
                page-break-after: avoid;
            }}
            
            h1:first-child {{
                margin-top: 0;
            }}
            
            h2 {{
                font-size: 16pt;
                font-weight: 600;
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #34495e;
                border-left: 4px solid #43A047;
                padding-left: 0.5em;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 13pt;
                font-weight: 600;
                margin-top: 0.8em;
                margin-bottom: 0.4em;
                color: #2c3e50;
                page-break-after: avoid;
            }}
            
            p {{
                margin-bottom: 0.6em;
                text-align: justify;
                text-justify: inter-word;
            }}
            
            ul, ol {{
                margin: 0.4em 0 0.8em 2em;
                padding: 0;
            }}
            
            li {{
                margin-bottom: 0.4em;
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
            
            a {{
                color: #3498db;
                text-decoration: none;
                border-bottom: 1px dotted #3498db;
            }}
            
            a:hover {{
                color: #2980b9;
                border-bottom-style: solid;
            }}
            
            em {{
                font-style: italic;
                color: #7f8c8d;
            }}
            
            strong {{
                font-weight: 600;
                color: #2c3e50;
            }}
            
            blockquote {{
                margin: 0.5em 0;
                padding: 0.8em;
                background: #f5f5f5;
                border-left: 4px solid #66BB6A;
                font-style: italic;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }}
            
            th, td {{
                padding: 0.5em;
                border: 1px solid #ddd;
                text-align: left;
            }}
            
            th {{
                background-color: #f5f5f5;
                font-weight: 600;
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
            
            @media print {{
                body {{
                    padding: 0;
                }}
                
                h1 {{
                    page-break-before: auto;
                }}
                
                h2 {{
                    page-break-after: avoid;
                }}
            }}
        </style>
    </head>
    <body>
    """
    
    # Convert markdown to HTML
    md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists', 'tables'])
    html_from_md = md_converter.convert(markdown_text)
    
    # Add converted markdown and close HTML
    html_content += html_from_md
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def generate_podcast_pdf(md_file):
    """Generate PDF from podcast markdown file"""
    
    output_file = md_file.with_suffix('.pdf')
    
    # Skip if PDF already exists
    if output_file.exists():
        print(f"  ✓ PDF already exists: {output_file.name}")
        return True
    
    print(f"  Generating PDF: {output_file.name}")
    
    try:
        # Create HTML content
        html_content = create_podcast_html(md_file)
        
        # Generate PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { size: A4; margin: 2cm 1.5cm; }
            ''')]
        )
        
        # Check file size
        file_size = output_file.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"    ✓ Generated ({file_size:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return False

def main():
    """Main function"""
    
    # Find any _ENG podcast directories
    podcast_base = Path('podcast')
    eng_dirs = sorted([d for d in podcast_base.glob('*_ENG') if d.is_dir()])
    
    if not eng_dirs:
        print("❌ No English podcast directories found (looking for podcast/*_ENG)")
        print("Please run 5d_translate_podcast.py first to generate English podcasts")
        sys.exit(1)
    
    # Process the most recent one by default, or specify via command line
    if len(sys.argv) > 1:
        podcast_dir = Path('podcast') / sys.argv[1]
        if not podcast_dir.exists():
            print(f"❌ Directory not found: {podcast_dir}")
            sys.exit(1)
    else:
        podcast_dir = eng_dirs[-1]  # Use most recent
    
    print(f"Using directory: {podcast_dir}")
    
    # Get all markdown files
    md_files = list(podcast_dir.glob('*.md'))
    
    if not md_files:
        print(f"❌ No markdown files found in {podcast_dir}")
        sys.exit(1)
    
    print("=" * 50)
    print("📄 English Podcast PDF Generator")
    print("=" * 50)
    print(f"Processing {len(md_files)} podcast files from {podcast_dir}\n")
    
    success_count = 0
    
    for md_file in md_files:
        print(f"\n{md_file.name}:")
        if generate_podcast_pdf(md_file):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Successfully generated {success_count}/{len(md_files)} PDFs")
    print(f"📁 Location: {podcast_dir}")
    
    if success_count < len(md_files):
        sys.exit(1)

if __name__ == "__main__":
    main()