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
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    leads = []
    
    # DuckDuckGo is more automation friendly than Google
    search_url = "https://duckduckgo.com/?q=site:linkedin.com+%22looking+for+website+developer%22+OR+%22school+website+requirement%22&ia=web"
    
    try:
        print(f"DEBUG: Opening DuckDuckGo...")
        driver.get(search_url)
        time.sleep(10) # Results load hone ka intezar

        # DuckDuckGo ke search results 'article' ya 'div.result' mein hote hain
        results = driver.find_elements(By.CSS_SELECTOR, "li[data-layout='organic']")
        
        print(f"DEBUG: Found {len(results)} potential leads on DuckDuckGo")

        for res in results[:20]:
            try:
                # Title aur Link nikalna
                anchor = res.find_element(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                title = anchor.text
                link = anchor.get_attribute("href")
                
                if "linkedin.com" in link:
                    leads.append({
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title,
                        "Link": link,
                        "Source": "DuckDuckGo/LinkedIn"
                    })
            except Exception as e:
                continue
                
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
    msg['From'] = f"Lead Bot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"🚀 {count} New Service Leads Found - {datetime.now().date()}"
    
    with open(file_path, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={file_path}")
        msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            print("DEBUG: Final Leads Email Sent!")
    except Exception as e:
        print(f"DEBUG: Email sending failed: {e}")

if __name__ == "__main__":
    leads_data = get_leads()
    
    if leads_data:
        df = pd.DataFrame(leads_data)
        file_name = f"Leads_Report_{datetime.now().strftime('%d_%b')}.xlsx"
        df.to_excel(file_name, index=False)
        send_email(file_name, len(leads_data))
    else:
        print("DEBUG: No new leads found. Try changing keywords in search_url.")
