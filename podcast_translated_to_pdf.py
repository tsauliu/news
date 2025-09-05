#!/usr/bin/env python3
"""
Unified podcast processor: Translate and generate PDFs for podcast markdown files
Combines functionality of translation and PDF generation for both Chinese and English

Usage:
    # Process everything (translate + generate PDFs)
    python 5d_podcast_processor.py
    
    # Translate only
    python 5d_podcast_processor.py --translate-only
    
    # Generate PDFs only (English)
    python 5d_podcast_processor.py --pdf-only-en
    
    # Specify custom date
    python 5d_podcast_processor.py --date 2025-09-05
"""

import re
import sys
import shutil
import argparse
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from parameters import friday_date
from models import gemini_model_stream


# ============================================================================
# Translation Functions (from original 5d)
# ============================================================================

def clean_content(text):
    """Remove timestamp links and dividers to save tokens"""
    # Remove [(HH:MM:SS)] or [(MM:SS)] or [(HH:MM)] followed by URL
    pattern = r'\[\([0-9]+(?::[0-9]+){1,2}\)\]\([^)]+\)'
    text = re.sub(pattern, '', text)
    
    # Remove "---" dividers (standalone on a line)
    text = re.sub(r'^---$', '', text, flags=re.MULTILINE)
    
    # Clean up multiple blank lines
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Clean up double spaces
    text = re.sub(r'  +', ' ', text)
    
    return text.strip()

def translate_podcast_file(input_file, output_file):
    """Translate a single podcast file from Chinese to English"""
    print(f"  Translating: {input_file.name}")
    
    # Skip if already translated
    if output_file.exists():
        print(f"    ✓ Already exists: {output_file.name}")
        return True
    
    # Read and clean content
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Clean each line
    cleaned_lines = []
    for line in lines:
        cleaned = clean_content(line)
        if cleaned or line.strip() == '':  # Keep empty lines for formatting
            cleaned_lines.append(line if line.strip() == '' else cleaned + '\n')
    
    # Create temp folder
    temp_dir = Path('temp_translation')
    temp_dir.mkdir(exist_ok=True)
    
    # Split into chunks (max 300 lines each)
    chunk_size = 300
    chunks = [cleaned_lines[i:i+chunk_size] for i in range(0, len(cleaned_lines), chunk_size)]
    
    print(f"    Split into {len(chunks)} chunks ({len(cleaned_lines)} lines total)")
    
    prompt = """You are a professional translator specializing in automotive industry content.
Translate the following Chinese text to natural, accurate English.

CRITICAL REQUIREMENTS:
1. Maintain ALL markdown formatting (headers #, ##, ###, bullet points -, etc.)
2. Keep company names, brand names, and proper nouns accurate
3. Use natural English expressions with professional automotive terminology
4. Output must be ENGLISH ONLY - no Chinese characters allowed
5. Preserve all line breaks and paragraph structure
6. If text is already in English, keep it unchanged

IMPORTANT: You MUST translate EVERY SINGLE Chinese character to English, including:
- Metadata fields like "播客" (Podcast), "节目" (Episode)
- Section headers and titles
- Any Chinese punctuation (，。！？) should be replaced with English equivalents (,.!?)
- Chinese quotes "「」" should become English quotes ""
- ALL Chinese text MUST be translated - do not leave ANY Chinese characters

Common translations:
- 播客 → Podcast
- 节目/集 → Episode
- 主持人 → Host
- 嘉宾 → Guest
- 时间 → Time/Duration
- 简介 → Summary/Introduction
- 内容 → Content
- 讨论 → Discussion
- 观点 → Viewpoint/Opinion

Translate the following text:"""
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_file = temp_dir / f"chunk_{i}.md"
        chunk_content = ''.join(chunk)
        
        print(f"    Chunk {i+1}/{len(chunks)} ({len(chunk)} lines)", end='')
        
        try:
            gemini_model_stream(prompt, chunk_content, str(chunk_file), model="gemini-2.5-flash")
            
            # Read translated chunk
            with open(chunk_file, 'r', encoding='utf-8') as f:
                translated_chunks.append(f.read())
            
            print(f" ✓")
        except Exception as e:
            print(f" ✗ Failed: {str(e)[:50]}")
            # Keep original if translation fails
            translated_chunks.append(chunk_content)
    
    # Combine all chunks
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in translated_chunks:
            f.write(chunk)
            if not chunk.endswith('\n'):
                f.write('\n')
    
    # Clean up temp folder
    shutil.rmtree(temp_dir)
    
    print(f"    ✓ Saved to: {output_file}")
    return True


# ============================================================================
# PDF Generation Functions (from original 5e, enhanced for both languages)
# ============================================================================

def extract_episode_info(md_file, language='en'):
    """Extract podcast and episode titles from markdown"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    podcast_name = ""
    episode_title = ""
    
    # Pattern detection based on language
    if language == 'cn':
        podcast_pattern = r'- 播客[:：]\s*(.+)'
        episode_pattern = r'- (?:节目|集)[:：]\s*(.+)'
    else:
        podcast_pattern = r'- Podcast[:：]\s*(.+)'
        episode_pattern = r'- Episode[:：]\s*(.+)'
    
    for line in lines[:20]:  # Check first 20 lines for info
        podcast_match = re.search(podcast_pattern, line)
        episode_match = re.search(episode_pattern, line)
        
        if podcast_match:
            podcast_name = podcast_match.group(1).strip()
        elif episode_match:
            episode_title = episode_match.group(1).strip()
            
    return podcast_name, episode_title

def sanitize_filename(title):
    """Sanitize title for use as filename"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    
    # Replace periods and punctuation
    title = title.replace('.', '').replace('!', '').replace('?', '')
    
    # Limit length
    if len(title) > 150:
        title = title[:150]
    
    return title.strip()

def create_podcast_html(md_file, language='en'):
    """Create HTML from podcast markdown file with language-specific styling"""
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Extract episode info
    podcast_name, episode_title = extract_episode_info(md_file, language)
    
    # Create HTML with CSS styling
    page_title = episode_title if episode_title else md_file.stem
    
    # Font selection based on language
    if language == 'cn':
        font_family = "'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif"
        font_size = "10.5pt"
        line_height = "1.6"
    else:
        font_family = "'Inter', 'Arial', 'Helvetica', sans-serif"
        font_size = "11pt"
        line_height = "1.4"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="{'zh-CN' if language == 'cn' else 'en'}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: {font_family};
                font-size: {font_size};
                line-height: {line_height};
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
                line-height: {line_height};
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
                    font-family: {font_family};
                }}
                
                @top-right {{
                    content: "{podcast_name if podcast_name else ('播客记录' if language == 'cn' else 'Podcast Transcript')}";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: {font_family};
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
    
    # Add episode title as a header if available
    if episode_title:
        html_content += f"""
        <div style="text-align: center; margin-bottom: 1.5em; padding: 0.8em; border-bottom: 2px solid #2E7D32;">
            <h1 style="margin: 0; font-size: 22pt; color: #2c3e50; font-weight: 600;">{episode_title}</h1>
            <p style="margin-top: 0.3em; font-size: {font_size}; color: #7f8c8d;">{podcast_name}</p>
        </div>
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

def generate_podcast_pdf(md_file, language='en'):
    """Generate PDF from podcast markdown file"""
    
    # Extract episode info to get proper filename
    _, episode_title = extract_episode_info(md_file, language)
    
    # Use episode title as filename if available
    if episode_title:
        safe_filename = sanitize_filename(episode_title)
        output_file = md_file.parent / f"{safe_filename}.pdf"
    else:
        output_file = md_file.with_suffix('.pdf')
    
    # Skip if PDF already exists
    if output_file.exists():
        print(f"    ✓ PDF already exists: {output_file.name}")
        return True
    
    print(f"    Generating PDF: {output_file.name}")
    
    try:
        # Create HTML content
        html_content = create_podcast_html(md_file, language)
        
        # Generate PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_file,
            stylesheets=[CSS(string='''
                @page { size: A4; margin: 2cm 1.5cm; }
            ''')]
        )
        
        # Check file size
        file_size = output_file.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"      ✓ Generated ({file_size:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"      ✗ Failed: {e}")
        return False


# ============================================================================
# Main Processing Functions
# ============================================================================

def translate_podcasts(source_dir, target_dir):
    """Translate all podcasts in source directory"""
    print(f"\n📝 Translation Process")
    print(f"  Source: {source_dir}")
    print(f"  Target: {target_dir}")
    print("=" * 50)
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all markdown files
    md_files = list(source_dir.glob('*.md'))
    
    if not md_files:
        print(f"❌ No markdown files found in {source_dir}")
        return False
    
    print(f"Found {len(md_files)} markdown files to translate\n")
    
    success_count = 0
    for md_file in md_files:
        output_file = target_dir / md_file.name
        if translate_podcast_file(md_file, output_file):
            success_count += 1
    
    print(f"\n✓ Translation complete: {success_count}/{len(md_files)} files")
    return success_count == len(md_files)

def generate_pdfs(podcast_dir, language='en'):
    """Generate PDFs for all markdown files in directory"""
    lang_name = "Chinese" if language == 'cn' else "English"
    print(f"\n📄 {lang_name} PDF Generation")
    print(f"  Directory: {podcast_dir}")
    print("=" * 50)
    
    if not podcast_dir.exists():
        print(f"❌ Directory not found: {podcast_dir}")
        return False
    
    # Get all markdown files
    md_files = list(podcast_dir.glob('*.md'))
    
    if not md_files:
        print(f"❌ No markdown files found in {podcast_dir}")
        return False
    
    print(f"Found {len(md_files)} markdown files\n")
    
    success_count = 0
    for md_file in md_files:
        print(f"{md_file.name}:")
        if generate_podcast_pdf(md_file, language):
            success_count += 1
    
    print(f"\n✓ PDF generation complete: {success_count}/{len(md_files)} files")
    return success_count == len(md_files)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Podcast processor: translate and generate PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 5d_podcast_processor.py                    # Full processing (translate + PDFs)
  python 5d_podcast_processor.py --translate-only   # Only translate
  python 5d_podcast_processor.py --pdf-only-en      # Only generate English PDFs
  python 5d_podcast_processor.py --date 2025-09-05  # Use specific date
        """
    )
    
    parser.add_argument('--date', type=str, default=friday_date,
                        help=f'Date for podcast directory (default: {friday_date})')
    parser.add_argument('--translate-only', action='store_true',
                        help='Only translate Chinese to English')
    parser.add_argument('--pdf-only-en', action='store_true',
                        help='Only generate PDFs for English podcasts')
    parser.add_argument('--source-dir', type=str,
                        help='Custom source directory (overrides --date)')
    parser.add_argument('--target-dir', type=str,
                        help='Custom target directory for translation')
    
    args = parser.parse_args()
    
    # Determine directories
    podcast_base = Path('podcast')
    
    if args.source_dir:
        source_dir = Path(args.source_dir)
    else:
        source_dir = podcast_base / args.date
    
    if args.target_dir:
        target_dir = Path(args.target_dir)
    else:
        target_dir = podcast_base / f"{args.date}_ENG"
    
    print("\n" + "=" * 60)
    print("🎙️  Unified Podcast Processor")
    print("=" * 60)
    
    # Process based on arguments
    if args.pdf_only_en:
        # Only generate English PDFs
        if not target_dir.exists():
            print(f"❌ English directory not found: {target_dir}")
            print("  Please run translation first or specify --source-dir")
            sys.exit(1)
        success = generate_pdfs(target_dir, language='en')
        
    elif args.translate_only:
        # Only translate
        success = translate_podcasts(source_dir, target_dir)
        
    else:
        # Full processing: translate and generate PDFs for both languages
        print("\n🔄 Full Processing Mode")
        
        # Step 1: Translate Chinese to English
        translate_success = translate_podcasts(source_dir, target_dir)
        
        # Step 2: Generate English PDFs
        en_pdf_success = generate_pdfs(target_dir, language='en')
        
        success = translate_success and en_pdf_success
        
        print("\n" + "=" * 60)
        print("📊 Summary:")
        print(f"  ✓ Translation: {'Success' if translate_success else 'Failed'}")
        print(f"  ✓ English PDFs: {'Success' if en_pdf_success else 'Failed'}")
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All operations completed successfully!")
    else:
        print("⚠️  Some operations failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()