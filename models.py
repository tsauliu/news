#%%
import os
import time
from typing import Optional

import requests
from openai import OpenAI

# OneAPI Configuration - hardcoded
ONE_API_BASE_URL = 'http://localhost:3001/v1'
ONE_API_KEY = 'sk-xrb5yN283dC9ytWNEaE207B3B2De4079B5D1C09cE988DdE9'

# Feishu webhook configuration
DEFAULT_FEISHU_WEBHOOK_URL = (
    "https://open.feishu.cn/open-apis/bot/v2/hook/869f9457-6d3d-4f88-8bee-d21c41b11625"
)


# Initialize OpenAI client
_openai_client = OpenAI(
    api_key=ONE_API_KEY,
    base_url=ONE_API_BASE_URL
)

def send_feishu_notification(
    message: str,
    *,
    webhook_url: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """Post a simple text notification to the configured Feishu webhook."""
    url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL") or DEFAULT_FEISHU_WEBHOOK_URL
    if not url:
        print("Feishu webhook URL not configured; skip notification.")
        return False

    payload = {"msg_type": "text", "content": {"text": message}}

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            return True
        print(
            "Feishu notification failed: "
            f"{response.status_code} {response.text.strip()}"
        )
    except requests.RequestException as exc:
        print(f"Feishu notification error: {exc}")
    return False

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
