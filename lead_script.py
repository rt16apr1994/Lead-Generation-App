import os
import pandas as pd
from apify_client import ApifyClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def get_leads_from_apify():
    # GitHub Secret se token uthana
    client = ApifyClient(os.environ.get('APIFY_TOKEN'))

    # Google Search Scraper Actor use karna
    # Ye actor residential proxy use karta hai isliye block nahi hota
    run_input = {
        "queries": "site:linkedin.com \"looking for website development\" OR \"school website requirement\"",
        "maxPagesPerQuery": 1,
        "resultsPerPage": 20,
        "countryCode": "in", # India ke liye
        "languageCode": "en",
        "maxResults": 20,
    }

    print("DEBUG: Starting Apify Actor...")
    # Actor run karna (google-search-scraper)
    run = client.actor("apify/google-search-scraper").call(run_input=run_input)

    leads = []
    # Results fetch karna
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # Google search results 'organicResults' mein hote hain
        for result in item.get("organicResults", []):
            leads.append({
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Title": result.get("title"),
                "Link": result.get("url"),
                "Snippet": result.get("description")
            })
    
    return leads

def send_email(file_path, count):
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('RECEIVER_EMAIL')

    msg = MIMEMultipart()
    msg['From'] = f"Lead Bot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"✅ {count} Verified Leads Found - {datetime.now().date()}"
    
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
            print("DEBUG: Email sent successfully with Apify leads!")
    except Exception as e:
        print(f"DEBUG: Email failed: {e}")

if __name__ == "__main__":
    leads_data = get_leads_from_apify()
    
    if leads_data:
        print(f"DEBUG: Found {len(leads_data)} leads via Apify.")
        df = pd.DataFrame(leads_data)
        file_name = "Apify_Leads_Report.xlsx"
        df.to_excel(file_name, index=False)
        send_email(file_name, len(leads_data))
    else:
        print("DEBUG: Apify returned 0 results. Check your query or token.")
