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
    # Real user jaisa dikhne ke liye User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    leads = []
    
    # Bing Search URL - Ismein blocking kam hoti hai
    # Query: site:linkedin.com "looking for website" OR "school website development"
    search_url = "https://www.bing.com/search?q=site%3Alinkedin.com+%22looking+for+website+development%22+OR+%22need+school+website%22"
    
    try:
        print(f"DEBUG: Opening Bing...")
        driver.get(search_url)
        time.sleep(10) # Results load hone ka wait

        # Bing ke search results 'li.b_algo' class mein hote hain
        results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo")
        print(f"DEBUG: Found {len(results)} raw results on Bing")

        for res in results[:15]:
            try:
                # Title aur Link nikalna
                title_element = res.find_element(By.TAG_NAME, "h2")
                title = title_element.text
                link = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                leads.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Title": title,
                    "Link": link,
                    "Source": "Bing/LinkedIn"
                })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"DEBUG: Scraping Error: {e}")
    finally:
        driver.quit()
    
    return leads

def send_email(file_path, count):
    # GitHub Secrets se information uthana
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('RECEIVER_EMAIL')

    print(f"DEBUG: Attempting to send email to {receiver}...")

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"🚀 {count} New Service Leads Found - {datetime.now().date()}"
    
    try:
        with open(file_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={file_path}")
            msg.attach(part)

        # Gmail SMTP Server connect karna
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("DEBUG: Email sent successfully!")
    except Exception as e:
        print(f"DEBUG: Email failed: {e}")

if __name__ == "__main__":
    # 1. Leads nikalna
    leads_data = get_leads()
    
    # 2. Agar leads mili toh Excel bana kar email bhejna
    if leads_data:
        print(f"DEBUG: Total {len(leads_data)} leads found. Creating Excel...")
        df = pd.DataFrame(leads_data)
        file_name = "Daily_Leads_Report.xlsx"
        df.to_excel(file_name, index=False)
        
        # Email function call karna
        send_email(file_name, len(leads_data))
    else:
        print("DEBUG: No leads found. Skipping email to avoid spam.")
