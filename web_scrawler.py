'''
before run,plz set up the chrome driver, with instructions in ./crawler
'''
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from bs4 import BeautifulSoup
import os
from parameters import friday_date
from time import sleep
import re

chrome_options = Options()

test=True

if test:
    driver = webdriver.Remote(
        command_executor='http://localhost:4444',
        options=chrome_options
    )
else:
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--ignore-certificate-errors')
    service = Service(f'/home/caoliu/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)


def scrape_url_to_md(url,output_path):    
    # Check if the file already exists and contains error message
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "完成验证后即可继续访问" in content:
                    print(f"File contains error message, deleting: {output_path}")
                    os.remove(output_path)
        except Exception as e:
            print(f"Error checking existing file {output_path}: {str(e)}")

    # Skip if file already exists
    if os.path.exists(output_path):
        print(f"File already exists: {output_path}, skipping...")
        return
    
    try:
        # Visit the webpage
        driver.get(url)
        
        page_source = driver.page_source        
        soup = BeautifulSoup(page_source, 'html.parser')
        text_content = soup.get_text()
        
        if "完成验证后即可继续访问" in text_content:
            sleep(3) 
            button = driver.find_element(By.ID, 'js_verify')
            button.click()
            sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        text_content = soup.get_text()
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        if "完成验证后即可继续访问" in text_content:
            print(f"Error message found in {url}, skipping...")
            return
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        sleep(10)        
        print(f"Successfully saved {url} to {output_path}")
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")

if __name__ == "__main__":
    scrape_url_to_md('https://mp.weixin.qq.com/s?__biz=Mzg2NzUxNTU1OA==&mid=2247662414&idx=4&sn=001a5ff87f3aae7e23b110a776928904&subscene=0,rss', 'test.md')