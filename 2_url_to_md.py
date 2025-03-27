'''
before run,plz set up the chrome driver, with instructions in ./crawler
'''
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
    
    # Skip if file already exists
    if os.path.exists(output_path):
        print(f"File already exists: {output_path}, skipping...")
        return
    
    try:
        # Visit the webpage
        driver.get(url)
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Get text content and clean up multiple line breaks
        text_content = soup.get_text()
        # Replace 3 or more newlines with 2 newlines
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        
        # Save the text content to a markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"Successfully saved {url} to {output_path}")
        sleep(1)
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