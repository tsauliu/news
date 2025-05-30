#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from parameters import friday_date
import os

def clean_markdown(friday_date):
    raw_path=f'pdfreport/02 markdown/{friday_date}'
    output_path=f'pdfreport/03 cleaned_markdown/{friday_date}'
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(raw_path, exist_ok=True)

    for file in os.listdir(raw_path):
        output_file = os.path.join(output_path, file)
        if os.path.exists(output_file):
            continue

        with open(os.path.join(raw_path, file), 'r') as f:
            content = f.read()
        # Find lines with "Disclosures" but not "see"
        lines = content.split('\n')
        print(file)
        with open(output_file, 'w') as f:
            for line in lines:
                if "disclosures" in line.lower() and "see" not in line.lower():
                    f.write(line + '\n')
                    break
                elif "免责声明" in line.lower() and "阅读" not in line.lower():
                    f.write(line + '\n')
                    break
                else:
                    f.write(line + '\n')