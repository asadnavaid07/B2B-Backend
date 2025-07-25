import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def test_sendgrid():
    try:
        message = Mail(
            from_email="asadnavaid34@gmail.com",
            to_emails="asadnavaid11@gmail.com",
            subject="Test Email",
            plain_text_content="This is a test email."
        )
        sendgrid_client = SendGridAPIClient("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")
        response = sendgrid_client.send(message)
        print(f"Status Code: {response.status_code}")
        print(f"Body: {response.body}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_sendgrid()