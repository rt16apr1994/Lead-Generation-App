import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time

def get_leads():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Bina window ke chalega
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    leads = []
    
    # Google Search Dorking
    query = 'site:linkedin.com "need website development" OR "looking for school app"'
    driver.get("https://www.google.com")
    time.sleep(2)
    
    search = driver.find_element(By.NAME, "q")
    search.send_keys(query)
    search.send_keys(Keys.ENTER)
    time.sleep(5)

    results = driver.find_elements(By.CSS_SELECTOR, "div.g")
    for res in results[:10]: # Top 10 results
        try:
            title = res.find_element(By.TAG_NAME, "h3").text
            link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
            leads.append({"Title": title, "Link": link})
        except: continue
    
    driver.quit()
    return leads

# Email Logic (Using GitHub Secrets)
def send_email(file_path):
    sender = os.environ['EMAIL_USER']
    password = os.environ['EMAIL_PASS']
    receiver = os.environ['RECEIVER_EMAIL']

    msg = MIMEMultipart()
    msg['Subject'] = "Daily Free Leads Report"
    
    with open(file_path, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={file_path}")
        msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

if __name__ == "__main__":
    data = get_leads()
    if data:
        df = pd.DataFrame(data)
        file_name = "daily_leads.xlsx"
        df.to_excel(file_name, index=False)
        send_email(file_name)
