# ai agent to screen urls, return the most relevant ones
# TODO pending 

import os
syspath=os.getcwd().split('Dropbox')[0]

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
chrome_options.add_argument('--proxy-server=http://127.0.0.1:20171')
chrome_options.add_argument('--ignore-certificate-errors')
service = Service(f'{syspath}chromedriver-linux64/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# 访问一个网页
driver.get(f"https://seekingalpha.com/api/v3/earnings_calendar/tickers?filter[selected_date]={trddate}&filter[with_rating]=false&filter[currency]=USD")
soup = BeautifulSoup(driver.page_source, 'lxml')