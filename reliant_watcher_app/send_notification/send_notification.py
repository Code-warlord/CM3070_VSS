from pywa import WhatsApp

from twilio.rest import Client

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from pathlib import Path
from email.mime.text import MIMEText
import pickle
import json


def authenticate_gmail(API_name="gmail", API_version="v1"):
    """Authenticates and returns a Gmail API service instance."""
    token = None
    # Token file to store access token
    token_path = Path(__file__).parent.parent / "auth" / f"{API_name}_{API_version}_token.pickle"
    if token_path.exists():
        with open(token_path, "rb") as file:
            token = pickle.load(file)

    # If there are no valid credentials, login with OAuth
    if not token or not token.valid:
        if token and token.expired and token.refresh_token:
            token.refresh(Request())
        else:
            credentials_path = Path(__file__).parent.parent / "auth" / "gmail_credentials.json" # Load credentials.json downloaded from Google Cloud
            scopes = ["https://www.googleapis.com/auth/gmail.send"] # Define Gmail API Scopes
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes
            )
            token = flow.run_local_server(port=0)

        # Save the access token
        with open(token_path, "wb") as file:
            pickle.dump(token, file)
    return build(API_name, API_version, credentials=token)

def send_email(email, subject, message):
    """Send an email using the Gmail API."""
    service = authenticate_gmail()
    message = MIMEText(message)
    message["to"] = email
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    create_message = {"raw": encoded_message}

    # Send the email
    try:
        message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Email sent successfully to {email}!")
    except Exception as error:
        print(f"An error occurred: {error}")

def send_whatsapp_msg(phone, message):
    whatsapp_token_file = Path(__file__).parent.parent / "auth" / "whatsapp_token.json"

    with open(whatsapp_token_file, "r") as file:
        whatsapp_details = json.load(file)
    whatsapp_token = whatsapp_details["token"]
    whatsapp_phone_id = whatsapp_details["phone_id"]
    wa = WhatsApp(
        phone_id=whatsapp_phone_id,
        token= whatsapp_token
    )
    wa.send_message(
        to=phone,
        text= message
    )
    print(f"Whatsapp message sent to {phone}")


def send_sms(phone, message):
    twilio_token_file = Path(__file__).parent.parent / "auth" / "twilio_credentials.json"
    with open(twilio_token_file, "r") as file:
        twilio_details = json.load(file)
    twilio_token = twilio_details["token"]
    twilio_phone = twilio_details["phone"]
    twilio_account_sid = twilio_details["account_sid"]
    client = Client(twilio_account_sid, twilio_token)
    message = client.messages.create(from_=twilio_phone, body=message, to=phone)
    print(f"SMS sent to {phone}")


def send_email_whatsapp_notification(subject, message, phone, email):
    send_email(email, subject, message)
    send_sms(phone, message)
    send_whatsapp_msg(phone, message)

    