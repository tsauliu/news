#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from markitdown import MarkItDown
from parameters import friday_date
import os
import shutil

def pdf_to_md(friday_date):
    source_path=os.path.expanduser(f'~/Dropbox/MyServerFiles/AutoWeekly/{friday_date}')
    raw_path=f'pdfreport/01 raw/{friday_date}'

    if os.path.exists(source_path):
        if not os.path.exists(raw_path):
            shutil.move(source_path, raw_path)
    else:
        pass

    output_path=f'pdfreport/02 markdown/{friday_date}'

    if os.path.exists(raw_path):
        os.makedirs(output_path, exist_ok=True)
        md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
        for file in os.listdir(raw_path):
            output_file = os.path.join(output_path, file.replace('.pdf', '.md'))
            if os.path.exists(output_file):
                continue
            print(file)
            result = md.convert(os.path.join(raw_path, file))
            with open(output_file, 'w') as f:
                f.write(file+'\n\n')
                f.write(result.text_content)
    else:
        raise FileNotFoundError(f"Raw path {raw_path} does not exist")

#%%
