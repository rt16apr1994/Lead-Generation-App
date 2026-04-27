import os
import pandas as pd
from apify_client import ApifyClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# --- Configuration ---
APIFY_TOKEN = os.getenv('APIFY_TOKEN')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

client = ApifyClient(APIFY_TOKEN)

# Search Keywords ki list
KEYWORDS = [
    "Private Schools in Bhopal", 
    "Gyms in Bhopal", 
    "Restaurants in Bhopal", 
    "Clinics in Bhopal", 
    "Bakers in Bhopal"
]

def get_next_keyword():
    # Din ke hisaab se keyword select karega (0=Mon, 1=Tue...)
    day_of_week = datetime.now().weekday()
    return KEYWORDS[day_of_week % len(KEYWORDS)]

def run_scraper(query):
    print(f"Searching for: {query}")
    run_input = {
        "queries": [query],
        "maxPagesPerQuery": 1,
        "resultsPerPage": 20,
        "language": "en",
    }
    # Google Maps Scraper Actor
    run = client.actor("apify/google-maps-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())

def filter_and_save_leads(raw_data):
    history_file = 'leads_history.csv'
    
    # History load karein
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
        processed_ids = set(history_df['placeId'].astype(str).tolist())
    else:
        processed_ids = set()
        history_df = pd.DataFrame(columns=['placeId', 'title', 'date'])

    new_leads = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for item in raw_data:
        place_id = str(item.get('placeId'))
        website = item.get('website')
        phone = item.get('phone')

        # Filter: Website nahi honi chahiye, Phone hona chahiye, aur Duplicate nahi hona chahiye
        if not website and phone and place_id not in processed_ids:
            lead = {
                "Business Title": item.get('title'),
                "Contact/WhatsApp": phone,
                "Location": item.get('address'),
                "Category": item.get('categoryName'),
                "placeId": place_id,
                "Date Found": current_date
            }
            new_leads.append(lead)
            processed_ids.add(place_id)

    if new_leads:
        # Update History File
        new_history_entry = pd.DataFrame(new_leads)[['placeId', 'Business Title', 'Date Found']]
        new_history_entry.columns = ['placeId', 'title', 'date']
        pd.concat([history_df, new_history_entry]).to_csv(history_file, index=False)
        
        # Create Excel for Email
        final_df = pd.DataFrame(new_leads).drop(columns=['placeId'])
        filename = f"Leads_{current_date}.xlsx"
        final_df.to_excel(filename, index=False)
        return filename
    
    return None

def send_email(filename, query):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"Daily Leads: {query} ({datetime.now().strftime('%d %b')})"

    body = f"Hi,\n\nPlease find attached the list of businesses in Bhopal that don't have a website.\n\nSearch Category: {query}"
    # Attach body and file... (Existing Email Logic)
    # [Shortened for brevity - reuse your existing attachment code here]
    print(f"Email sent with {filename}")

# Execution
if __name__ == "__main__":
    current_query = get_next_keyword()
    data = run_scraper(current_query)
    file = filter_and_save_leads(data)
    
    if file:
        # send_email(file, current_query)
        print(f"Success: {file} generated.")
    else:
        print("No new leads found today.")
