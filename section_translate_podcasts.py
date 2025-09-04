#!/usr/bin/env python3
"""
Section-based translation for podcast markdown files
Translates each logical section separately to avoid API timeouts
"""

import re
import os
import time
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

# Import API key
from apikey import gemini_key

# Configure Gemini
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.5-flash')

def preprocess_content(content):
    """Remove timestamp links before translation"""
    # Remove timestamp links like [(00:00)](https://...)
    pattern = r'\[\([0-9]+(?::[0-9]+){1,2}\)\]\([^)]+\)'
    cleaned = re.sub(pattern, '', content)
    
    # Remove standalone timestamps like [(00:00)]
    pattern2 = r'\[\([0-9]+(?::[0-9]+){1,2}\)\]'
    cleaned = re.sub(pattern2, '', cleaned)
    
    # Clean up extra spaces
    cleaned = re.sub(r'  +', ' ', cleaned)
    cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)
    
    return cleaned

def split_by_sections(content):
    """Split markdown content by major sections"""
    sections = {}
    
    # Define the section headers
    section_headers = ['# Info', '# Summary', '# Takeaways', '# Q & A', '# Transcript']
    
    # Find all section positions
    positions = []
    for header in section_headers:
        pos = content.find(header)
        if pos != -1:
            positions.append((pos, header))
    
    # Sort by position
    positions.sort()
    
    # Extract each section
    for i, (pos, header) in enumerate(positions):
        if i < len(positions) - 1:
            # Not the last section
            next_pos = positions[i + 1][0]
            section_content = content[pos:next_pos].strip()
        else:
            # Last section
            section_content = content[pos:].strip()
        
        sections[header] = section_content
    
    return sections

def has_significant_chinese(text):
    """Check if text contains significant Chinese content (more than just names/terms)"""
    import re
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars) > 10  # More than 10 Chinese characters indicates incomplete translation

def translate_section(section_content, section_name, retry_count=3):
    """Translate a single section with retries"""
    prompt = f"""
Translate the following Chinese text to COMPLETE English. 

IMPORTANT INSTRUCTIONS:
1. Translate ALL Chinese text to English, including names, places, and technical terms
2. For Chinese names, provide English transliteration AND keep original in parentheses: e.g., "Yu Chengdong (余承东)" 
3. For Chinese companies/brands, translate to English equivalents where possible
4. Maintain all markdown formatting exactly (# headers, **bold**, etc.)
5. Translate speaker names to English equivalents
6. Do NOT leave any Chinese sentences or paragraphs untranslated
7. This is the {section_name} section of a podcast transcript

Text to translate:
{section_content}
"""
    
    for attempt in range(retry_count):
        try:
            print(f"  Translating {section_name} (attempt {attempt + 1}/{retry_count})...")
            response = model.generate_content(prompt, 
                                               generation_config={'temperature': 0.3})
            translated = response.text
            
            # Improved validation
            if not translated or len(translated) < 50:
                print(f"  ✗ Translation too short ({len(translated) if translated else 0} chars), retrying...")
                continue
                
            # Check for significant untranslated Chinese content
            if has_significant_chinese(translated):
                print(f"  ✗ Translation contains significant Chinese text, retrying...")
                continue
            
            # Check that translation is not just the original
            if translated.strip() == section_content.strip():
                print(f"  ✗ Translation appears unchanged, retrying...")
                continue
                
            print(f"  ✓ {section_name} translated successfully ({len(translated):,} chars)")
            return translated
                
        except Exception as e:
            print(f"  ✗ Error translating {section_name}: {e}")
            if attempt < retry_count - 1:
                print(f"  Waiting 10 seconds before retry...")
                time.sleep(10)  # Longer wait for rate limiting
    
    # If all retries failed, raise an exception instead of continuing
    error_msg = f"Critical Error: Failed to translate {section_name} after {retry_count} attempts"
    print(f"  ✗ {error_msg}")
    raise RuntimeError(error_msg)

def translate_podcast_by_sections(input_file, output_file):
    """Translate podcast file section by section"""
    print(f"\nProcessing: {input_file.name}")
    
    # Read the file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        return False
    
    print(f"  File size: {len(content):,} bytes")
    
    # Preprocess to remove timestamps
    print("  Removing timestamp links...")
    content = preprocess_content(content)
    print(f"  Cleaned size: {len(content):,} bytes")
    
    # Split into sections
    print("  Splitting into sections...")
    sections = split_by_sections(content)
    print(f"  Found {len(sections)} sections: {list(sections.keys())}")
    
    # Translate each section
    translated_sections = {}
    
    for section_name, section_content in sections.items():
        print(f"\n  Processing section: {section_name}")
        print(f"    Section size: {len(section_content):,} bytes")
        
        # Special handling for large sections
        if section_name == '# Transcript' and len(section_content) > 25000:
            print("    Transcript section is large, splitting into chunks...")
            
            # Split transcript by paragraphs or sections
            paragraphs = section_content.split('\n\n')
            header = paragraphs[0] if paragraphs[0].startswith('#') else '# Transcript'
            content_paras = paragraphs[1:] if paragraphs[0].startswith('#') else paragraphs
            
            # Process in smaller chunks (~8KB) to be safer with API limits
            chunks = []
            current_chunk = []
            current_size = 0
            max_chunk_size = 8000
            
            for para in content_paras:
                para_size = len(para)
                if current_size + para_size > max_chunk_size and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk.append(para)
                    current_size += para_size
            
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            print(f"    Split into {len(chunks)} chunks (avg size: {sum(len(c) for c in chunks)//len(chunks):,} chars)")
            
            # Translate each chunk with better error handling
            translated_chunks = []
            try:
                # Translate header first
                translated_header = translate_section(header, "Transcript header")
                translated_chunks.append(translated_header)
                
                # Translate each content chunk
                for i, chunk in enumerate(chunks):
                    print(f"    Processing chunk {i+1}/{len(chunks)} ({len(chunk):,} chars)...")
                    translated_chunk = translate_section(chunk, f"Transcript chunk {i+1}")
                    translated_chunks.append(translated_chunk)
                    time.sleep(3)  # Longer rate limiting between chunks
                
                translated_sections[section_name] = '\n\n'.join(translated_chunks)
                
            except RuntimeError as e:
                print(f"  ✗ Failed to translate transcript chunks: {e}")
                raise  # Re-raise to stop the entire process
            
        else:
            # Translate normally for smaller sections
            try:
                translated_sections[section_name] = translate_section(
                    section_content, section_name
                )
                time.sleep(3)  # Rate limiting
            except RuntimeError as e:
                print(f"  ✗ Critical error translating {section_name}: {e}")
                return False
    
    # Reassemble the document
    print("\n  Reassembling translated document...")
    section_order = ['# Info', '# Summary', '# Takeaways', '# Q & A', '# Transcript']
    
    final_content = []
    for header in section_order:
        if header in translated_sections:
            final_content.append(translated_sections[header])
        else:
            print(f"  ⚠ Warning: Section {header} was not found in translated content")
    
    if not final_content:
        print("  ✗ No sections were successfully translated")
        return False
    
    full_translation = '\n\n'.join(final_content)
    
    # Final validation
    if has_significant_chinese(full_translation):
        print("  ⚠ Warning: Final document still contains significant Chinese text")
        # Don't fail, but warn user
    
    # Save the translation
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_translation)
        print(f"  ✓ Translation saved to: {output_file}")
        print(f"  Output size: {len(full_translation):,} bytes")
        return True
    except Exception as e:
        print(f"  ✗ Error saving translation: {e}")
        return False

def main():
    """Main function to translate all podcasts"""
    from parameters import friday_date
    podcast_dir = Path('podcast') / friday_date
    podcast_eng_dir = Path('podcast') / f'{friday_date}_ENG'
    
    print(f"Section-based Podcast Translation")
    print(f"{'='*50}")
    print(f"Source: {podcast_dir}")
    print(f"Target: {podcast_eng_dir}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    if not podcast_dir.exists():
        print(f"\n✗ Source directory not found: {podcast_dir}")
        return
    
    # Find all markdown files
    md_files = list(podcast_dir.glob('*.md'))
    print(f"\nFound {len(md_files)} markdown files to translate")
    
    if not md_files:
        print("No files to process")
        return
    
    # Process each file
    successful = 0
    failed = 0
    
    for md_file in md_files:
        output_file = podcast_eng_dir / md_file.name
        
        if translate_podcast_by_sections(md_file, output_file):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Translation Complete")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()