#!/usr/bin/env python3
"""
Translate podcast markdown files from Chinese to English
"""

import os
import re
from pathlib import Path
from models import gemini_model

def remove_timestamp_links(text):
    """Remove timestamp links like [(00:01)](https://...) to save tokens"""
    # Remove [(HH:MM:SS)] or [(MM:SS)] or [(HH:MM)] followed by URL
    pattern = r'\[\([0-9]+(?::[0-9]+){1,2}\)\]\([^)]+\)'
    text = re.sub(pattern, '', text)
    # Clean up double spaces
    text = re.sub(r'  +', ' ', text)
    return text

def translate_section(header, content):
    """Translate a section with Gemini"""
    if not content.strip():
        return content
    
    prompt = """You are a professional translator specializing in automotive industry content.
Translate the following Chinese text to natural, accurate English.
Requirements:
1. Maintain professional automotive terminology
2. Keep company names, brand names accurate
3. Use natural English expressions
4. Only return the translated text, no explanations
5. IMPORTANT: Output must be ENGLISH ONLY - no Chinese characters
6. If text is already in English, keep it unchanged
7. Preserve markdown formatting (headers, bullet points, links)

Translate the following text:"""
    
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            translated = gemini_model(prompt, content)
            return translated.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"    Retry {attempt+1}/{max_retries} after error: {str(e)[:100]}")
                print(f"    Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"    Failed after {max_retries} attempts: {str(e)[:100]}")
                return content  # Return original if translation fails

def translate_podcast(input_file, output_file):
    """Translate a podcast markdown file section by section"""
    print(f"Translating: {input_file.name}")
    
    # Check if partial translation exists
    partial_file = output_file.with_suffix('.partial')
    translated_parts = []
    start_index = 0
    
    if partial_file.exists():
        print(f"  Found partial translation, resuming...")
        with open(partial_file, 'r', encoding='utf-8') as f:
            translated_parts = f.read().split('\n---SECTION_BREAK---\n')
        start_index = len(translated_parts)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove timestamp links first
    content = remove_timestamp_links(content)
    
    # Split by headers and translate each section
    sections = re.split(r'^(#+\s+.+)$', content, flags=re.MULTILINE)
    
    current_header = ""
    
    for i, part in enumerate(sections):
        if i < start_index:
            continue  # Skip already translated sections
            
        if part.startswith('#'):
            # This is a header, translate it
            header_level = len(part) - len(part.lstrip('#'))
            header_text = part[header_level:].strip()
            if header_text:
                translated_header = translate_section("header", header_text)
                translated_parts.append('#' * header_level + ' ' + translated_header)
            current_header = header_text
        elif part.strip():
            # This is content, translate it
            print(f"  Section {i+1}/{len(sections)}: {current_header[:30]}...")
            translated_content = translate_section(current_header, part)
            translated_parts.append(translated_content)
        else:
            # Empty section, keep as is
            translated_parts.append(part)
        
        # Save partial progress
        with open(partial_file, 'w', encoding='utf-8') as f:
            f.write('\n---SECTION_BREAK---\n'.join(translated_parts))
    
    # Write final translated content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(translated_parts))
    
    # Remove partial file
    if partial_file.exists():
        partial_file.unlink()
    
    print(f"  ✓ Saved to: {output_file}")

def main():
    source_dir = Path('podcast/2025-08-29')
    target_dir = Path('podcast/2025-08-29_ENG')
    
    if not source_dir.exists():
        print(f"Source directory {source_dir} not found")
        return
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all markdown files
    md_files = list(source_dir.glob('*.md'))
    
    print(f"Found {len(md_files)} markdown files to translate\n")
    
    for md_file in md_files:
        output_file = target_dir / md_file.name
        
        # Skip if already translated
        if output_file.exists():
            print(f"✓ Already exists: {output_file.name}")
            continue
        
        translate_podcast(md_file, output_file)
    
    print(f"\n✓ Translation complete. Files saved to: {target_dir}")

if __name__ == "__main__":
    main()