# src/services/gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    """Pure service that calls Gemini API – no speech, no dialog."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def get_answer(self, prompt: str, max_tokens: int = 200) -> str:
        """Send prompt to Gemini, return response text."""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Gemini error: {str(e)}"