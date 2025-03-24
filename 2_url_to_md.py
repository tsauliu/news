'''
before run,plz set up the chrome driver, with instructions in ./crawler
'''
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
import pandas as pd
from bs4 import BeautifulSoup

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--ignore-certificate-errors')
service = Service(f'/home/ubuntu/chromedriver-linux64/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# 访问一个网页
driver.get(f"https://mp.weixin.qq.com/s/wZYdNqc0MZjsEq9G57ORNQ")
# Get the page source
page_source = driver.page_source

# Parse with BeautifulSoup
soup = BeautifulSoup(page_source, 'html.parser')

# Print the text content
print(soup.get_text())
