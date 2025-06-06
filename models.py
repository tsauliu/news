#%%
import os
import tiktoken

def count_tokens(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

from openai import OpenAI
from apikey import api_key_deepseek,model_id_deepseek

def deepseek_model(prompt,content):
    client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key=api_key_deepseek
    )
    def summary(content):
        completion = client.chat.completions.create(
            model=model_id_deepseek,
            messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        )
        return completion.choices[0].message.content
    return summary(content)

from google import genai
from apikey import gemini_key

def gemini_model(prompt,content):
    client = genai.Client(api_key=gemini_key)
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-06-05", contents=prompt+'\n -- \n'+content
    )
    return response.text