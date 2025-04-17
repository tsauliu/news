#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from parameters import friday_date
import os
from models import deepseek_model,count_tokens

raw_path=f'./03 cleaned_markdown/{friday_date}'
output_path=f'./04 summary/{friday_date}'

os.makedirs(output_path, exist_ok=True)
os.makedirs(raw_path, exist_ok=True)

for file in os.listdir(raw_path):
    print(file)
    with open(os.path.join(raw_path, file), 'r') as f:
        content = f.read()
    prompt = open('prompt.txt','r').read()
    print('total tokens:',count_tokens(prompt+'\n -- \n'+content))
    summary = deepseek_model(prompt,content)
    with open(os.path.join(output_path, file), 'w') as f:
        f.write(summary)