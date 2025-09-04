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
model = genai.GenerativeModel('gemini-1.5-flash-latest')

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

def translate_section(section_content, section_name, retry_count=3):
    """Translate a single section with retries"""
    prompt = f"""
Translate the following Chinese text to English. 
Maintain the markdown formatting.
Keep all markdown headers (# symbols).
Translate naturally and accurately.
This is the {section_name} section of a podcast transcript.

Text to translate:
{section_content}
"""
    
    for attempt in range(retry_count):
        try:
            print(f"  Translating {section_name} (attempt {attempt + 1}/{retry_count})...")
            response = model.generate_content(prompt, 
                                               generation_config={'temperature': 0.3})
            translated = response.text
            
            # Basic validation
            if translated and len(translated) > 50:
                print(f"  ✓ {section_name} translated successfully")
                return translated
            else:
                print(f"  ✗ Translation seems too short, retrying...")
                
        except Exception as e:
            print(f"  ✗ Error translating {section_name}: {e}")
            if attempt < retry_count - 1:
                time.sleep(5)
    
    # If all retries failed, return original with a note
    print(f"  ✗ Failed to translate {section_name} after {retry_count} attempts")
    return f"[Translation failed]\n{section_content}"

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
        if section_name == '# Transcript' and len(section_content) > 30000:
            print("    Transcript section is large, splitting into chunks...")
            
            # Split transcript by paragraphs
            paragraphs = section_content.split('\n\n')
            header = paragraphs[0]  # Keep the "# Transcript" header
            
            # Process in chunks of ~10KB
            chunks = []
            current_chunk = []
            current_size = 0
            max_chunk_size = 10000
            
            for para in paragraphs[1:]:  # Skip header
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
            
            print(f"    Split into {len(chunks)} chunks")
            
            # Translate each chunk
            translated_chunks = [header]  # Start with header
            for i, chunk in enumerate(chunks):
                print(f"    Translating chunk {i+1}/{len(chunks)} ({len(chunk):,} bytes)...")
                translated_chunk = translate_section(chunk, f"Transcript chunk {i+1}")
                translated_chunks.append(translated_chunk)
                time.sleep(2)  # Rate limiting
            
            translated_sections[section_name] = '\n\n'.join(translated_chunks)
            
        else:
            # Translate normally for smaller sections
            translated_sections[section_name] = translate_section(
                section_content, section_name
            )
            time.sleep(2)  # Rate limiting
    
    # Reassemble the document
    print("\n  Reassembling translated document...")
    section_order = ['# Info', '# Summary', '# Takeaways', '# Q & A', '# Transcript']
    
    final_content = []
    for header in section_order:
        if header in translated_sections:
            final_content.append(translated_sections[header])
    
    full_translation = '\n\n'.join(final_content)
    
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
    friday_date = '2025-08-29'
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