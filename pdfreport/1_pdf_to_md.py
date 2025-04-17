#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from markitdown import MarkItDown
from parameters import friday_date
import os
raw_path=f'./01 raw/{friday_date}'
output_path=f'./02 markdown/{friday_date}'
os.makedirs(raw_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

md = MarkItDown(enable_plugins=False) # Set to True to enable plugins

for file in os.listdir(raw_path):
    print(file)
    result = md.convert(os.path.join(raw_path, file))
    with open(os.path.join(output_path, file.replace('.pdf', '.md')), 'w') as f:
        f.write(file+'\n\n')
        f.write(result.text_content)