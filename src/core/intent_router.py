import re

class IntentRouter:
    def __init__(self):
        self.intents = []  # list of (regex_pattern, handler_method)

    def register(self, pattern: str, handler):
        self.intents.append((re.compile(pattern, re.IGNORECASE), handler))

    def route(self, text: str):
        for pattern, handler in self.intents:
            if pattern.search(text):
                return handler
        return None