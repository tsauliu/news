#%%
# Step 3c: Generate English Word document from reviewed markdown file (Multi-threaded version)
# This script reads the markdown file, translates non-link content to English using multiple threads, and applies Word formatting

from docx import Document
from parameters import friday_date
from models import deepseek_model
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm

friday_date = '2025-05-30'

# Translation prompt for DeepSeek model
translation_prompt = """You are a professional translator specializing in automotive industry content. 
Translate the following Chinese text to natural, accurate English. 
Context: This is automotive industry news, research reports, and market analysis.
Requirements:
1. Maintain professional automotive terminology
2. Keep the original meaning and tone
3. Use natural, native English expressions
4. Keep company names, brand names, or proper nouns accurate
5. Keep technical terms accurate
6. Only return the translated text, no explanations or additional content
7. IMPORTANT: Your output must be ENGLISH ONLY - no Chinese characters allowed in the response
8. If the input is already in English, return it unchanged
9. Never include any Chinese text in your response under any circumstances"""

# Thread lock for print statements
print_lock = threading.Lock()

def safe_print(message):
    """Thread-safe print function"""
    with print_lock:
        print(message)

def translate_to_english(text):
    """Translate Chinese text to English using DeepSeek model"""
    if not text or len(text.strip()) < 3:
        return text
    
    try:
        translated = deepseek_model(translation_prompt, text)
        return translated.strip()
    except Exception as e:
        safe_print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def translate_row(row):
    """Translate a single row from the dataframe"""
    index, style, text = row['index'], row['style'], row['text']
    
    # Determine if we should translate this content
    should_translate = style not in ['link', 'page_break']
    
    if should_translate and text and len(text.strip()) >= 3:
        safe_print(f"Translating row {index}: {text[:50]}...")
        translated_text = translate_to_english(text)
        return {'index': index, 'style': style, 'text': text, 'translated_text': translated_text}
    else:
        return {'index': index, 'style': style, 'text': text, 'translated_text': text}

def parse_markdown_to_dataframe(content):
    """Parse markdown content and return a dataframe with index, style, and text"""
    lines = content.split('\n')
    data = []
    index = 0
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines but keep track of them for proper spacing
        if not line:
            data.append({'index': index, 'style': 'empty', 'text': ''})
            index += 1
            i += 1
            continue
        
        # Check for Word style annotations
        if line.startswith('<!-- WORD_STYLE:'):
            # Extract the style
            style_match = re.search(r'<!-- WORD_STYLE: (.+?) -->', line)
            if style_match:
                style = style_match.group(1).strip()
                i += 1  # Move to next line for content
                
                # Get the content line(s)
                if i < len(lines):
                    content_line = lines[i].strip()
                    data.append({'index': index, 'style': style, 'text': content_line})
                    index += 1
                else:
                    # Style annotation without content
                    data.append({'index': index, 'style': style, 'text': ''})
                    index += 1
            i += 1
        else:
            # Line without style annotation - treat as normal paragraph
            data.append({'index': index, 'style': 'normal_paragraph', 'text': line})
            index += 1
            i += 1
    
    return pd.DataFrame(data)

def assemble_word_document(df, output_file):
    """Assemble Word document from translated dataframe"""
    # Create new Word document using template
    doc = Document('news_template.docx')
    
    for _, row in df.iterrows():
        style = row['style']
        translated_text = row['translated_text']
        
        # Skip empty lines
        if style == 'empty':
            continue
            
        # Apply formatting based on style
        if style == 'heading_level_1':
            # Remove markdown # symbols and add as Word heading
            heading_text = translated_text.replace('#', '').strip()
            doc.add_heading(heading_text, level=1)
        
        elif style == 'heading_level_2':
            # Remove markdown ## symbols and add as Word heading
            heading_text = translated_text.replace('#', '').strip()
            doc.add_heading(heading_text, level=2)
        
        elif style == 'heading_level_3':
            # Remove markdown ### symbols and add as Word heading
            heading_text = translated_text.replace('#', '').strip()
            doc.add_heading(heading_text, level=3)
        
        elif style == 'summarytitle':
            doc.add_paragraph('')
            doc.add_paragraph(translated_text, style='summarytitle')
        
        elif style == 'bullet':
            doc.add_paragraph(translated_text, style='bullet')
        
        elif style == 'link':
            # Don't translate links, keep original
            doc.add_paragraph(translated_text, style='link')
        
        elif style == 'author':
            doc.add_paragraph(translated_text, style='author')
        
        elif style == 'normal_paragraph':
            if translated_text:  # Only add non-empty paragraphs
                doc.add_paragraph(translated_text)
                doc.add_paragraph('')  # Add empty paragraph after content
        
        elif style == 'page_break':
            doc.add_page_break()
        
        else:
            # Unknown style, treat as normal paragraph
            if translated_text:  # Only add non-empty paragraphs
                doc.add_paragraph(translated_text)
    
    # Save the document
    doc.save(output_file)

def main():
    global df, rows_to_translate
    # Step 1: Parse markdown file to dataframe
    input_md = f'data/{friday_date}_for_review.md'
    
    print("Step 1: Parsing markdown file...")
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    df = parse_markdown_to_dataframe(content)
    print(f"Parsed {len(df)} items from markdown file")
    
    # Step 2: Multi-threaded translation
    print("Step 2: Starting multi-threaded translation...")
    
    # Filter rows that need translation
    rows_to_translate = df[
        (df['style'] != 'link') & 
        (df['style'] != 'page_break') & 
        (df['style'] != 'empty') & 
        (df['text'].str.len() >= 3)
    ]
    
    print(f"Found {len(rows_to_translate)} items to translate")
    
    # Use ThreadPoolExecutor for multi-threading
    max_workers = 100  # Adjust based on your system and API limits
    translated_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_row = {
            executor.submit(translate_row, row): idx 
            for idx, row in rows_to_translate.iterrows()
        }
        
        # Process completed translations with progress bar
        with tqdm(total=len(future_to_row), desc="Translating") as pbar:
            for future in as_completed(future_to_row):
                try:
                    result = future.result()
                    translated_results.append(result)
                    pbar.update(1)
                except Exception as e:
                    safe_print(f"Translation task failed: {e}")
                    pbar.update(1)
    
    # Create translated dataframe
    translated_df = pd.DataFrame(translated_results)
    
    # Merge with original dataframe
    df = df.merge(
        translated_df[['index', 'translated_text']], 
        on='index', 
        how='left'
    )
    
    # Fill missing translations with original text
    df['translated_text'] = df['translated_text'].fillna(df['text'])
    
    print(f"Translation completed. Processed {len(translated_results)} items")
    
    # Step 3: Assemble Word document
    print("Step 3: Assembling Word document...")
    output_file = f'data/{friday_date}_weekly_news_english.docx'
    df.to_excel(f'data/{friday_date}_weekly_news_english.xlsx', index=False)
    assemble_word_document(df, output_file)
    
    print(f"English Word document generated: {output_file}")
    print("Document creation completed!")

if __name__ == "__main__":
    main() 