import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    try:
        # SMTP configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        email_from = os.getenv("EMAIL_FROM", "asadnavaid34@gmail.com")
        email_to = "asadnavaid11@gmail.com"
        
        if not smtp_username or not smtp_password:
            print("Error: Missing SMTP credentials. Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = "Test Email - SMTP"
        
        # Email body
        body = """
        Hello,
        
        This is a test email sent via SMTP instead of SendGrid.
        
        If you receive this email, the SMTP configuration is working correctly.
        
        Best regards,
        Project Overflow Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(email_from, email_to, text)
        server.quit()
        
        print("Email sent successfully via SMTP!")
        print(f"From: {email_from}")
        print(f"To: {email_to}")
        print(f"Server: {smtp_server}:{smtp_port}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_smtp()