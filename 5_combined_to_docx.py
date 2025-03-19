# combine the summary and detailed news into a docx file
# %%
from docx import Document
doc = Document('monthly_news_template.docx')
doc.add_heading('News Summary for Week - Mar 19', level=1)
doc.add_page_break()

doc.add_heading('Detailed News', level=1)
doc.add_paragraph('这是新添加的段落文本')
doc.save('modified_example.docx')
