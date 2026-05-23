import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pathlib

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]
creds_path = pathlib.Path(__file__).parent / "credentials.json"
class GmailClient:
    def __init__(self, creds_file: str = "credentials.json", token_file: str = "gmail_token.json"):
        self.creds_file = creds_file
        self.token_file = token_file
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def send_message(self, to: str, subject: str, body: str) -> dict:
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = self.service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return result

    def list_messages(self, query: str = "", max_results: int = 10) -> list:
        response = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return response.get("messages", [])

    def get_message(self, msg_id: str) -> dict:
        return self.service.users().messages().get(userId="me", id=msg_id).execute()
    
if __name__ == '__main__':
    client = GmailClient(creds_file=creds_path)
  
    messages = client.list_messages(max_results=3)
    print(f"success Found {len(messages)} in inbox")
