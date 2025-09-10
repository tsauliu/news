#%%
import os, time
from openai import OpenAI

# OneAPI Configuration - hardcoded
ONE_API_BASE_URL = 'http://localhost:3001/v1'
ONE_API_KEY = 'sk-xrb5yN283dC9ytWNEaE207B3B2De4079B5D1C09cE988DdE9'

# Initialize OpenAI client
_openai_client = OpenAI(
    api_key=ONE_API_KEY,
    base_url=ONE_API_BASE_URL
)

def OneAPI_request(prompt, context="",model="gemini-2.5-pro"):
    """
    Make a request to Gemini API with retry logic
    
    Args:
        prompt: system context/role description
        context: user input
        model: model name to use (default: "gemini-2.5-pro")
        
    Returns:
        str: The response content or empty string on failure
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            messages = []
            if context:
                messages.append({"role": "system", "content": prompt})
            messages.append({"role": "user", "content": context})
            
            response = _openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5
            )
            
            if response and response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                print(f"Warning: Empty response on attempt {attempt + 1}")
                
        except Exception as e:
            print(f"Gemini request attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"All {max_retries} attempts failed")
                
    return ""