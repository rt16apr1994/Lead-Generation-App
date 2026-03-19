import os
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def send_test_email(file_path):
    sender = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    receiver = os.environ.get('RECEIVER_EMAIL')

    print(f"DEBUG: Attempting to send from {sender} to {receiver}")

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Test Lead Report - {datetime.now()}"
    
    try:
        with open(file_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={file_path}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("DEBUG: Email sent successfully!")
    except Exception as e:
        print(f"DEBUG: Email Error: {e}")

if __name__ == "__main__":
    # Hum dummy data bhej kar check karenge ki email setup sahi hai ya nahi
    print("DEBUG: Creating dummy data for testing...")
    dummy_data = [{"Title": "Test Lead", "Link": "https://example.com"}]
    df = pd.DataFrame(dummy_data)
    file_name = "test_leads.xlsx"
    df.to_excel(file_name, index=False)
    
    send_test_email(file_name)
