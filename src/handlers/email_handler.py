class Emailhandler():
    def __init__(self , dialog ,email_service ,  geminiservice=None ):
        self.dialog = dialog
        self.gemini = geminiservice
        self.email = email_service

    def handle_send_email(self):

        # first get the recipient
        recipient = self.dialog.speak("who do you want to send email to. ")
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



   




