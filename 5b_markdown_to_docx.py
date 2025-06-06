# Step 3: Generate Word document from reviewed markdown file
# This script reads the markdown file and applies Word formatting based on annotations

from docx import Document
from parameters import friday_date
import re

# friday_date = '2025-05-30'

# Load the reviewed markdown file
input_md = f'data/6_final_mds/{friday_date}_for_review.md'

# Create new Word document using template
doc = Document('news_template.docx')

# Read the markdown file
with open(input_md, 'r', encoding='utf-8') as f:
    content = f.read()

# Split content by lines and process
lines = content.split('\n')
i = 0

while i < len(lines):
    line = lines[i].strip()
    
    # Skip empty lines
    if not line:
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
                
                # Apply formatting based on style
                if style == 'heading_level_1':
                    # Remove markdown # symbols and add as Word heading
                    heading_text = content_line.replace('#', '').strip()
                    doc.add_heading(heading_text, level=1)
                
                elif style == 'heading_level_2':
                    # Remove markdown ## symbols and add as Word heading
                    heading_text = content_line.replace('#', '').strip()
                    doc.add_heading(heading_text, level=2)
                
                elif style == 'heading_level_3':
                    # Remove markdown ### symbols and add as Word heading
                    heading_text = content_line.replace('#', '').strip()
                    doc.add_heading(heading_text, level=3)
                
                elif style == 'summarytitle':
                    doc.add_paragraph('')
                    doc.add_paragraph(content_line, style='summarytitle')
                
                elif style == 'bullet':
                    doc.add_paragraph(content_line, style='bullet')
                
                elif style == 'link':
                    doc.add_paragraph(content_line, style='link')
                
                elif style == 'author':
                    doc.add_paragraph(content_line, style='author')
                
                elif style == 'normal_paragraph':
                    doc.add_paragraph(content_line)
                    doc.add_paragraph('')  # Add empty paragraph after content
                
                elif style == 'page_break':
                    doc.add_page_break()
                    i += 1  # Skip the content line for page breaks
                    continue
                
                else:
                    # Unknown style, treat as normal paragraph
                    doc.add_paragraph(content_line)
        
        i += 1
    else:
        # Line without style annotation - treat as normal paragraph if not empty
        if line:
            doc.add_paragraph(line)
        i += 1

# Save the document
output_file = f'data/7_docx/{friday_date}_weekly_news.docx'
doc.save(output_file)

print(f"Word document generated: {output_file}")
print("Document creation completed!") 