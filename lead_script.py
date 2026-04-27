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
    "Private Schools in Bhopal"
]

def get_next_keyword():
    # Din ke hisaab se keyword select karega (0=Mon, 1=Tue...)
    day_of_week = datetime.now().weekday()
    return KEYWORDS[day_of_week % len(KEYWORDS)]

def run_scraper(query):
    print(f"Searching for: {query}")
    
    # Ye input parameters naye Google Maps Scraper ke hisaab se hain
    run_input = {
        "searchStringsArray": [query],
        "maxCrawledPlacesPerSearch": 100,
        "language": "en",
        "exportPlaceUrls": False
    }
    
    try:
        # Hum generic ID ya stable compass actor use kar rahe hain
        print("Starting Apify Actor...")
        run = client.actor("compass/google-maps-scraper").call(run_input=run_input)
        
        print("Fetching results from dataset...")
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
    except Exception as e:
        print(f"Detailed Error: {e}")
        # Agar compass wala bhi na chale, toh try generic search
        return []

def filter_and_save_leads(raw_data):
    history_file = 'leads_history.csv'
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. History load karein ya nayi file ka structure banayein
    if os.path.exists(history_file):
        try:
            history_df = pd.read_csv(history_file)
            # Ensure placeId is string for proper comparison
            processed_ids = set(history_df['placeId'].astype(str).tolist())
        except Exception as e:
            print(f"History file read error: {e}. Creating new.")
            processed_ids = set()
            history_df = pd.DataFrame(columns=['placeId', 'title', 'date'])
    else:
        processed_ids = set()
        history_df = pd.DataFrame(columns=['placeId', 'title', 'date'])

    new_leads_for_excel = []
    new_history_entries = []

    # 2. Apify se aaye data ko filter karein
    for item in raw_data:
        # Apify ke naye scraper mein 'placeId' ya 'id' use hota hai
        place_id = str(item.get('placeId') or item.get('id') or "")
        website = item.get('website')
        phone = item.get('phone')
        title = item.get('title')

        if not place_id or not title:
            continue

        # Logic: Website nahi honi chahiye AUR ye lead pehle nahi aayi honi chahiye
        if not website and place_id not in processed_ids:
            # Excel file ke liye details
            lead_detail = {
                "Business Title": title,
                "Contact/WhatsApp": phone if phone else "Not Available",
                "Location": item.get('address', 'Bhopal'),
                "Category": item.get('categoryName', 'N/A'),
                "Date Found": current_date
            }
            new_leads_for_excel.append(lead_detail)
            
            # History file update karne ke liye details
            new_history_entries.append({
                'placeId': place_id,
                'title': title,
                'date': current_date
            })
            # Current run mein dobara duplicate na aaye isliye set mein add karein
            processed_ids.add(place_id)

    # 3. Agar nayi leads mili hain toh files update karein
    if new_leads_for_excel:
        # Update leads_history.csv
        new_hist_df = pd.DataFrame(new_history_entries)
        updated_history = pd.concat([history_df, new_hist_df], ignore_index=True)
        updated_history.to_csv(history_file, index=False)
        print(f"Added {len(new_leads_for_excel)} new leads to history.")

        # Create Excel file for Email
        filename = f"Leads_Bhopal_{current_date}.xlsx"
        final_df = pd.DataFrame(new_leads_for_excel)
        final_df.to_excel(filename, index=False)
        return filename
    
    print("No new 'No-Website' leads found in this run.")
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
