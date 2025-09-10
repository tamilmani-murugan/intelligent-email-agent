import os
import base64
import logging
import json
import re # Import the regular expression module
from email.mime.text import MIMEText

import google.generativeai as genai
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-1.5-flash")

if not GEMINI_API_KEY:
    logging.error("FATAL: Gemini API key not found. Please set GEMINI_API_KEY in the .env file.")
    exit()

# Load prompt templates from external files
try:
    with open('classify_prompt.txt', 'r') as f:
        AI_CLASSIFY_PROMPT_TEMPLATE = f.read()
    with open('reply_prompt.txt', 'r') as f:
        AI_REPLY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError as e:
    logging.error(f"FATAL: Prompt file not found: {e.filename}. Please ensure both 'classify_prompt.txt' and 'reply_prompt.txt' exist.")
    exit()
# --- END OF CONFIGURATION ---


def get_gmail_service():
    """Authenticates with the Gmail API and returns a service object."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def classify_email(clean_text):
    """Uses AI to classify the email's intent and returns a classification dict."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GENAI_MODEL)
        prompt = AI_CLASSIFY_PROMPT_TEMPLATE.format(email_text=clean_text[:4000])
        logging.info("Classifying email intent...")
        response = model.generate_content(prompt)
        # --- NEW ROBUST JSON PARSING ---
        # Use regex to find the JSON block, even if there's other text
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            return json.loads(json_string)
        else:
            logging.error("No valid JSON object found in the AI's classification response.")
            return {"category": "UNKNOWN", "confidence": 0.0}
        # --- END OF NEW CODE ---

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from AI response: {e}. Response was: {response.text}")
        return {"category": "UNKNOWN", "confidence": 0.0}
    except Exception as e:
        logging.error(f"An unexpected error occurred during classification: {e}")
        return {"category": "UNKNOWN", "confidence": 0.0}


def decide_action(classification):
    """Decides on an action based on the email's classification (Utility Model)."""
    category = classification.get("category", "UNKNOWN").upper()
    confidence = classification.get("confidence", 0.0)
    
    # This is our simple "Utility Model"
    if category == 'URGENT' and confidence > 0.7:
        return 'REPLY'
    elif category == 'NORMAL' and confidence > 0.6:
        return 'REPLY'
    elif category == 'SPAM' and confidence > 0.8:
        return 'ARCHIVE'
    else:
        return 'IGNORE'


def get_email_body(payload):
    """Recursively searches for the email body (text or html)."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data: return base64.urlsafe_b64decode(data).decode('utf-8')
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data: return base64.urlsafe_b64decode(data).decode('utf-8')
        return get_email_body(payload['parts'][0])
    elif 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return ""


def generate_ai_reply(html_body):
    """Generates a reply using the Gemini AI model."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GENAI_MODEL)
        prompt = AI_REPLY_PROMPT_TEMPLATE.format(html_body=html_body[:4000])
        logging.info("Generating AI reply...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error generating AI reply: {e}")
        return None


def send_email(service, sender_email, subject, ai_reply_html):
    """Creates and sends an HTML email message."""
    try:
        to_email = sender_email.split('<')[-1].strip('>')
        message = MIMEText(ai_reply_html, 'html')
        message['to'] = to_email
        message['from'] = 'me'
        message['subject'] = "Re: " + subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        logging.info(f"Email sent successfully! Message ID: {send_message['id']}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending email: {e}")


def archive_email(service, msg_id):
    """Archives an email by removing it from the inbox and marking as read."""
    try:
        # Removes from INBOX and marks as read
        service.users().messages().modify(
            userId='me', 
            id=msg_id, 
            body={'removeLabelIds': ['INBOX', 'UNREAD']}
        ).execute()
        logging.info(f"Archived email with ID: {msg_id}.")
    except Exception as e:
        logging.error(f"An error occurred while archiving email: {e}")


def mark_as_read(service, msg_id):
    """Marks a specific email as read."""
    try:
        service.users().messages().modify(
            userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
        ).execute()
        logging.info(f"Marked email with ID: {msg_id} as read.")
    except Exception as e:
        logging.error(f"An error occurred while marking email as read: {e}")


def main():
    """Main function to run the intelligent email processing agent."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages', [])

        if not messages:
            logging.info("No unread messages found. Exiting.")
            return

        logging.info(f"Found {len(messages)} unread messages. Processing all...")
        
        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            payload = msg['payload']
            headers = payload['headers']
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            logging.info(f"--- Processing Email from: {sender} ---")

            body = get_email_body(payload)
            clean_text = " ".join(BeautifulSoup(body, "lxml").get_text(separator=" ").split())
            
            classification = classify_email(clean_text)
            logging.info(f"Classification result: {classification}")

            action = decide_action(classification)
            logging.info(f"Decided Action: {action}")

            if action == 'REPLY':
                ai_reply_html = generate_ai_reply(body)
                if ai_reply_html:
                    send_email(service, sender, subject, ai_reply_html)
                    mark_as_read(service, msg_id)
                else:
                    logging.warning("AI failed to generate a reply. Marking as read to avoid retrying.")
                    mark_as_read(service, msg_id)
            elif action == 'ARCHIVE':
                archive_email(service, msg_id)
            elif action == 'IGNORE':
                logging.info("Ignoring email but marking as read to avoid reprocessing.")
                mark_as_read(service, msg_id)
            
            logging.info(f"--- Finished Processing Email ID: {msg_id} ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred in the main process: {e}")

if __name__ == '__main__':
    main()

