import re
from rapidfuzz import fuzz
from typing import List, Dict, Optional

class EmailService:
    def __init__(self, gmail_client, contacts_service=None):
        self.gmail = gmail_client
        self.contacts_service = contacts_service  # if you want Google People API

    # ---------- contact resolution (pure logic) ----------
    def find_email_by_name(self, spoken_name: str, threshold: int = 70, contacts: Dict = None) -> Optional[str]:
        if contacts is None:
            contacts = self._get_all_contacts()
        best_match = None
        highest_score = 0
        for name, email in contacts.items():
            name_score = fuzz.token_sort_ratio(spoken_name.lower(), name)
            email_score = fuzz.token_sort_ratio(spoken_name.lower(), email)
            current_score = max(name_score, email_score)
            if current_score > highest_score and current_score >= threshold:
                highest_score = current_score
                best_match = email
        return best_match

    def _get_all_contacts(self) -> Dict[str, str]:
        # simplified: read from recent emails and Google Contacts
        contacts = {}
        # from recent emails
        messages = self.gmail.list_messages(max_results=50)
        for msg in messages:
            full = self.gmail.get_message(msg['id'])
            headers = full['payload']['headers']
            for h in headers:
                if h['name'] in ['From', 'To']:
                    name, email = self._extract_name_email(h['value'])
                    if email:
                        contacts[name] = email
        # TODO: add Google People API if available
        return contacts

    def _extract_name_email(self, contact_str: str):
        pattern = r'(?:"?([^"<]*)"?\s*<([^>]+)>|([^<\s]+))'
        match = re.match(pattern, contact_str)
        if not match:
            return contact_str.strip().lower(), contact_str.strip().lower()
        name = (match.group(1) or match.group(3) or '').strip().lower()
        email = (match.group(2) or match.group(3) or '').strip().lower()
        return name, email

    # ---------- email operations ----------
    def send_email(self, to: str, subject: str, body: str) -> dict:
        try:
            result = self.gmail.send_message(to, subject, body)
            return {"success": True, "message_id": result['id']}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_emails_headlines(self, max_results=5) -> List[dict]:
        messages = self.gmail.list_messages(max_results=max_results, query="")
        emails = []
        for msg in messages:
            full = self.gmail.get_message(msg['id'])
            headers = {h['name']: h['value'] for h in full['payload']['headers'] if h['name'] in ['From', 'Subject']}
            emails.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject'),
                'unread': 'UNREAD' in full.get('labelIds', [])
            })
        return emails

    def search_email_by_subject(self, query: str) -> List[dict]:
        messages = self.gmail.list_messages(query=f"subject:{query}", max_results=20)
        emails = []
        for msg in messages:
            full = self.gmail.get_message(msg['id'])
            headers = {h['name']: h['value'] for h in full['payload']['headers'] if h['name'] in ['From', 'Subject']}
            emails.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject'),
            })
        return emails
