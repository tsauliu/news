#!/usr/bin/env python3
"""
Translate podcast markdown files from Chinese to English
"""

import re
import shutil
from pathlib import Path
from models import gemini_model_stream

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

def translate_podcast(input_file, output_file):
    """Translate podcast file by chunks"""
    print(f"Translating: {input_file.name}")
    
    # Skip if already translated
    if output_file.exists():
        print(f"  ✓ Already exists: {output_file}")
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
    
    print(f"  Split into {len(chunks)} chunks ({len(cleaned_lines)} lines total)")
    
    prompt = """You are a professional translator specializing in automotive industry content.
Translate the following Chinese text to natural, accurate English.

CRITICAL REQUIREMENTS:
1. Maintain ALL markdown formatting (headers #, ##, ###, bullet points -, etc.)
2. Keep company names, brand names, and proper nouns accurate
3. Use natural English expressions with professional automotive terminology
4. Output must be ENGLISH ONLY - no Chinese characters allowed
5. Preserve all line breaks and paragraph structure
6. If text is already in English, keep it unchanged

Translate the following text:"""
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_file = temp_dir / f"chunk_{i}.md"
        chunk_content = ''.join(chunk)
        
        print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} lines)", end='')
        
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
    
    print(f"  ✓ Saved to: {output_file}")
    return True

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