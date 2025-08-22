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
    import time
    client = genai.Client(api_key=gemini_key)
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro", contents=prompt+'\n -- \n'+content
            )
            return response.text
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                wait_time = 60 * (2 ** attempt)  # 60, 120, 240 seconds
                print(f"Gemini API failed (attempt {attempt + 1}/3): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Gemini API failed after 3 attempts: {e}")
                raise