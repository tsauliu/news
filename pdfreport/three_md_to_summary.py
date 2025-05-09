#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from parameters import friday_date
import os
from models import deepseek_model,count_tokens,gemini_model

def md_to_summary(friday_date):
    raw_path=f'./03 cleaned_markdown/{friday_date}'
    output_path_ds=f'./04 summary/{friday_date}_ds'
    output_path_gemini=f'./04 summary/{friday_date}_gemini'
    os.makedirs(output_path_ds, exist_ok=True)
    os.makedirs(output_path_gemini, exist_ok=True)
    os.makedirs(raw_path, exist_ok=True)

    for file in os.listdir(raw_path):
        output_file = os.path.join(output_path_gemini, file)
        if os.path.exists(output_file):
            continue

        print(file)
        with open(os.path.join(raw_path, file), 'r') as f:
            content = f.read()
            
        prompt = open('prompt.txt','r').read()
        print('total tokens:',count_tokens(prompt+'\n -- \n'+content))
        
        summary_ds = deepseek_model(prompt,content)
        with open(os.path.join(output_path_ds, file), 'w') as f:
            f.write(summary_ds)
        
        summary_gemini = gemini_model(prompt,content)
        with open(os.path.join(output_path_gemini, file), 'w') as f:
            f.write(summary_gemini)