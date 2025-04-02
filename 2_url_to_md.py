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

# Read URLs from CSV
urls = pd.read_csv(f'./data/1_urls/{friday_date}_article_urls.csv')

# Set up output folder
folder_path = f'./data/2_raw_mds/{friday_date}'
os.makedirs(folder_path, exist_ok=True)

chrome_options = Options()

test=False

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
    service = Service(f'/home/ubuntu/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)


def scrape_url_to_md(url, output_dir, title):
    # Generate a filename from the title
    # Extract the URL ID from the URL (the part after the last slash)
    url_id = url.split('/')[-1]
    filename = f"{url_id}.md"
    output_path = os.path.join(output_dir, filename)
    
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
            button = driver.find_element(By.ID, 'js_verify')
            button.click()
            sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        text_content = soup.get_text()
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        sleep(5)        
        print(f"Successfully saved {url} to {output_path}")
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")

# Process each URL
for _, row in urls.iterrows():
    url = row['url']  # Adjust column name if different
    title = row['title']  # Make sure 'title' column exists in your CSV
    scrape_url_to_md(url, folder_path, title)

# Clean up
driver.quit()
print(f'{friday_date} articles saved')