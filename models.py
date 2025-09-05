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
from apikey import gemini_key, gemini_key2, gemini_key3

def gemini_model(prompt,content,model="gemini-2.5-pro"):
    import time
    
    # List of API keys to cycle through on retries
    api_keys = [gemini_key, gemini_key2, gemini_key3]
    key_names = ['gemini_key', 'gemini_key2', 'gemini_key3']
    
    for attempt in range(3):
        try:
            # Use different API key for each attempt
            current_key = api_keys[attempt]
            key_name = key_names[attempt]
            
            client = genai.Client(api_key=current_key)
            response = client.models.generate_content(
                model=model, contents=prompt+'\n -- \n'+content
            )
            return response.text
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"Gemini API failed with {key_names[attempt]} (attempt {attempt + 1}/3): {e}")
                print(f"Retrying with {key_names[attempt + 1]} in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Gemini API failed after 3 attempts with all keys: {e}")
                raise

def gemini_model_stream(prompt, content, output_file, model="gemini-2.5-pro"):
    """Stream Gemini response directly to a markdown file"""
    import time
    
    # List of API keys to cycle through on retries
    api_keys = [gemini_key, gemini_key2, gemini_key3]
    key_names = ['gemini_key', 'gemini_key2', 'gemini_key3']
    
    for attempt in range(3):
        try:
            # Use different API key for each attempt
            current_key = api_keys[attempt]
            key_name = key_names[attempt]
            
            client = genai.Client(api_key=current_key)
            
            # Open file for writing
            with open(output_file, 'w', encoding='utf-8') as f:
                # Generate with streaming
                response = client.models.generate_content_stream(
                    model=model, contents=prompt+'\n\n'+content
                )
                
                # Write chunks as they arrive
                full_text = ""
                for chunk in response:
                    if chunk.text:
                        f.write(chunk.text)
                        f.flush()  # Ensure immediate write
                        full_text += chunk.text
                        print('.', end='', flush=True)  # Progress indicator
                
                print()  # New line after progress dots
                return full_text
                
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"\nGemini streaming failed with {key_names[attempt]} (attempt {attempt + 1}/3): {e}")
                print(f"Retrying with {key_names[attempt + 1]} in 5 seconds...")
                time.sleep(5)
            else:
                print(f"\nGemini streaming failed after 3 attempts with all keys: {e}")
                raise