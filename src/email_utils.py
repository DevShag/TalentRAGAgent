import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email using the SMTP configuration in environment variables.
    Requires SMTP_EMAIL and SMTP_APP_PASSWORD
    """

    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_APP_PASSWORD')

    if not smtp_email or not smtp_password:
        print("Warning: SMTP_EMAIL or SMTP_APP_PASSWORD not set. Email not sent")
        return False
    
    if not to_email:
        print('Warning: Candidate email is missing. Email not sent.')
        return False
    
    try:
        # Construct the email
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach body
        msg.attach(MIMEText(body, 'plain'))

        # Setup server
        # Explicitly using Gmail's SMTP server on port 587
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Login
        server.login(smtp_email, smtp_password)

        # Send
        server.send_message(msg)
        server.quit()

        print(f"Successfully sent email to {to_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
    
    
