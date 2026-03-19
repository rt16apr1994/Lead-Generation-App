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
from datetime import datetime

def get_leads():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # User-Agent badalne se Google ko lagta hai ki ye real browser hai
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    leads = []
    
    # Simple Query taaki block na ho
    query = 'site:linkedin.com "hiring website developer" OR "school website requirement"'
    
    try:
        driver.get("https://www.google.com")
        time.sleep(5) # Thoda zyada wait
        
        search = driver.find_element(By.NAME, "q")
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        time.sleep(7) # Results load hone ka intezar

        results = driver.find_elements(By.CSS_SELECTOR, "div.g")
        print(f"DEBUG: Found {len(results)} raw results on Google")

        for res in results[:15]:
            try:
                title = res.find_element(By.TAG_NAME, "h3").text
                link = res.find_element(By.TAG_NAME, "a").get_attribute("href")
                if "linkedin.com" in link: # Sirf kaam ke links
                    leads.append({"Date": datetime.now().date(), "Title": title, "Link": link})
            except: continue
    except Exception as e:
        print(f"DEBUG: Scraping Error: {e}")
    finally:
        driver.quit()
    
    return leads

def send_email(file_path, count):
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('RECEIVER_EMAIL')

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Found {count} New Leads - {datetime.now().date()}"
    
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
        print("DEBUG: Final Leads Email Sent!")

if __name__ == "__main__":
    leads_data = get_leads()
    
    if leads_data:
        df = pd.DataFrame(leads_data)
        file_name = "Social_Leads.xlsx"
        df.to_excel(file_name, index=False)
        send_email(file_name, len(leads_data))
    else:
        print("DEBUG: No new leads found today. Skipping email.")
