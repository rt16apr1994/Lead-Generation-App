import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
from datetime import datetime

def get_leads():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Real browser jaisa dikhne ke liye strong headers
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    leads = []
    
    # Google News se leads nikalna (Kam blocking hoti hai)
    # Query: Website development requirements for schools/businesses
    search_url = "https://www.google.com/search?q=hiring+website+developer+for+school+business&tbm=nws"
    
    try:
        print(f"DEBUG: Opening Google News...")
        driver.get(search_url)
        time.sleep(8) 

        # Google News ke results nikalne ke liye selectors
        results = driver.find_elements(By.CSS_SELECTOR, "div.SoE9A") # Google News card selector
        
        print(f"DEBUG: Found {len(results)} raw news/post results")

        for res in results[:10]:
            try:
                title = res.find_element(By.CSS_SELECTOR, "div.n0W69d").text
                link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
                leads.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Title": title,
                    "Link": link
                })
            except: continue
                
    except Exception as e:
        print(f"DEBUG: Error: {e}")
    finally:
        driver.quit()
    
    return leads

# Email function remains the same as before...
