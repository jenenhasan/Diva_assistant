#Done
class Emailhandler():
    def __init__(self , dialog ,email_service ,  geminiservice=None ):
        self.dialog = dialog
        self.gemini = geminiservice
        self.email = email_service

    def register(self, router):
        router.register(r"send (an? )?email|compose (an? )?email", self.handle_send_email)
        router.register(r"check inbox|show emails", self.handle_check_inbox)
        router.register(r"search email", self.handle_search_email)
        return self

    def handle_send_email(self):

        # first get the recipient
        recipient = self.dialog.listen_with_retry("who do you want to send email to. ")
        if not recipient : 
            return 
    
        contacts = self.email.get_all_contacts()
        resolved = self.find_email_by_name(recipient ,contacts=contacts )
        if not resolved: 
            self.dialog.speak(f"I couldnt find {recipient} in your contacts. ")
        
        # get email subject
        subject = self.dialog.listen_with_retry("what is the email subject")
        if not subject : 
            return 
        
        #get email content 
        if self.gemini: 
            topic = self.dialog.listen_with_retry("what is the email about")
            if not topic : 
                return 
            self.dialog.show_thinking()
            prompt = f"write a professional email about: {topic}. recipent: {resolved}. Keep it brief and formal"
            body = self.gemini.get_answer(prompt)
            self.dialog.hide_thinking()
            self.dialog.speak("Here is the email I prepared:")
            self.dialog.speak(body[:300])
            if not self.dialog.confirm("should I send this email?"):
                self.dialog.speak("cancelled")
                return 
            
        else : 
            body = self.dialog.listen_with_retry("what should you like to say?", retry_prompt = "please speak the message")
            if not body : 
                return 
            
        self.dialog.show_thinking()
        result = self.email.send_email(resolved , subject , body)
        self.dialog.hide_thinking()
        if result["success"]:
            self.dialog.speak(f"Email sent to {resolved}.")
        else : 
            self.dialog.speak(f"failed: {result['error']}")

                
        
        



    def handle_search_email(self):
        query = self.dialog.listen_with_retry("what would you like to listen for ")
        if not query: 
            return 
        self.dialog.show_thinking()
        results = self.email.search_email_by_subject(query)
        self.dialog.hide_thinking()
        if not results: 
            self.dialog.speak(f"No emails found about '{query}'.")
            return 
        self.dialog.speak(f"I found {len(results)} emails.")
        for i, email in enumerate(results[:3] , 1 ) : 
            self.dialog.speak(f"{i}. From {email['from']}: {email['subject']}")
            
        
        


    def handle_check_inbox(self):
        self.dialog.show_thinking()
        emails= self.email.read_emails_headlines(max_results=5)
        # print (emails)
        self.dialog.hide_thinking()
        if not emails: 
            self.dialog.speak("your inbox is empty")

        unread = sum(1 for e in emails if e.get('unread' , False) )
        self.dialog.speak(f"you have {len(emails)} recent emails, {unread} unread")

        self.dialog.show_thinking()
        for email in emails:
            self.dialog.speak(f"From {email['from']}: {email['subject']}")
        self.dialog.hide_thinking()





   

if __name__ == "__main__":
    from unittest.mock import MagicMock

    # ---------- Mock DialogManager ----------
    class MockDialog:
        def __init__(self):
            self.responses = []          # predefined answers for listen()
            self.response_index = 0
            self.thinking = False

        def speak(self, text):
            print(f"[ASSISTANT] {text}")

        def listen_with_retry(self, prompt=None, retry_prompt=None):
            if self.response_index < len(self.responses):
                ans = self.responses[self.response_index]
                self.response_index += 1
                return ans
            return ""

        def show_thinking(self):
            print("[THINKING...]")

        def hide_thinking(self):
            print("[DONE]")

        def confirm(self, question):
            print(f"[CONFIRM] {question} (y/n)")
            return input().strip().lower() in ("y", "yes")

    # ---------- Mock EmailService ----------
    class MockEmailService:
        def get_all_contacts(self):
            return {"john doe": "john@example.com", "jane smith": "jane@example.com"}

        def find_email_by_name(self, name, contacts=None):
            return contacts.get(name.lower())

        def send_email(self, to, subject, body):
            print(f"\n📧 SENDING EMAIL\nTo: {to}\nSubject: {subject}\nBody: {body[:200]}...\n")
            return {"success": True}

        def search_email_by_subject(self, query):
            return [
                {"from": "alice@work.com", "subject": f"Re: {query} - meeting"},
                {"from": "bob@work.com", "subject": f"{query} status"}
            ]

        def read_emails_headlines(self, max_results=5):
            return [
                {"from": "team@company.com", "subject": "Daily standup", "unread": True},
                {"from": "github@notify.com", "subject": "PR #42 merged", "unread": False}
            ]

    # ---------- Mock Gemini (optional) ----------
    class MockGemini:
        def get_answer(self, prompt):
            return "This is a mock AI‑generated email body."

    # ---------- Run tests ----------
    print("\n🧪 TESTING EmailHandler (mock mode)\n")
    method = input("Which method? (send / search / inbox): ").strip().lower()

    mock_dialog = MockDialog()
    mock_email = MockEmailService()
    mock_gemini = MockGemini()

    handler = Emailhandler(mock_dialog, mock_email, geminiservice=mock_gemini)

    if method == "send":
        # Pre‑define answers for the conversation
        mock_dialog.responses = [
            "john doe",           # recipient name
            "Weekly report",      # subject
            "Progress on project" # email topic (Gemini will generate body)
        ]
        handler.handle_send_email()

    elif method == "search":
        mock_dialog.responses = ["standup"]
        handler.handle_search_email()

    elif method == "inbox":
        handler.handle_check_inbox()

    else:
        print("Unknown method. Use 'send', 'search', or 'inbox'.")


