import random
from services.creativity import CreativityService, MOODS, DOMAINS


class CreativityHandler:
    def __init__(self, dialog, creativity_service: CreativityService):
        self.dialog = dialog
        self.creativity = creativity_service

    def register(self, router):
        """Register all creativity intents with the router."""
        router.register(r"generate (an? )?idea|creative idea|quantum idea|wild idea", self.generate_idea)
        router.register(r"tech idea|project idea|brainstorm idea", self.generate_idea)
        return self

    def generate_idea(self):
        """Interactive idea generation with user choices."""
        # Step 1: Choose mood
        self.dialog.speak("Let's generate a creative tech idea.")
        
        # Show moods (speak first few, or rely on visual)
        self.dialog.speak("Available moods include: " + ", ".join(MOODS[:10]) + " and more.")
        mood = self.dialog.listen_with_retry(
            "What is your current mood? You can say a mood from the list or say 'random'.",
            "Please tell me your mood or say 'random'."
        )
        
        if not mood:
            return
        
        if mood.lower() == "random":
            mood = random.choice(MOODS)
            self.dialog.speak(f"Randomly selected mood: {mood}")
        
        # Step 2: Choose domain
        self.dialog.speak("Tech domains include: " + ", ".join(DOMAINS[:10]) + " and more.")
        domain = self.dialog.listen_with_retry(
            "What tech domain are you curious about? Or say 'random'.",
            "Please tell me a tech domain or say 'random'."
        )
        
        if not domain:
            return
        
        if domain.lower() == "random":
            domain = random.choice(DOMAINS)
            self.dialog.speak(f"Randomly selected domain: {domain}")
        
        # Step 3: Optional custom thought
        self.dialog.speak("Do you have any specific thought or interest you'd like to include?")
        custom_thought = self.dialog.listen_with_retry(
            "You can say your thought, or say 'no' to skip.",
            "Please share your thought or say 'no'."
        )
        
        if custom_thought and custom_thought.lower() in ["no", "none", "skip"]:
            custom_thought = None
        
        # Step 4: Generate idea
        self.dialog.speak("Firing quantum seed and entangling creative fields. Please wait.")
        self.dialog.show_thinking()
        
        result = self.creativity.sync_generate_idea(
            mood=mood if mood != "random" else None,
            domain=domain if domain != "random" else None,
            custom_thought=custom_thought
        )
        
        self.dialog.hide_thinking()
        
        # Step 5: Present result
        if result.get("success"):
            self.dialog.speak("Quantum idea generated!")
            self.dialog.speak(f"Mood: {result['mood']}")
            self.dialog.speak(f"Domain: {result['domain']}")
            self.dialog.speak(f"Quantum Seed: {result['seed']}")
            self.dialog.speak("Here is the idea:")
            self.dialog.speak(result["idea"][:500])  # Limit length
        else:
            self.dialog.speak(f"Sorry, I couldn't generate an idea. Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    from unittest.mock import MagicMock, AsyncMock
    
    # Mock DialogManager
    class MockDialog:
        def __init__(self):
            self.responses = []
            self.response_index = 0
        
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
    
    # Mock CreativityService
    class MockCreativityService:
        def sync_generate_idea(self, mood=None, domain=None, custom_thought=None):
            return {
                "success": True,
                "idea": "A revolutionary AI-powered code assistant that uses quantum seeds to generate creative solutions.",
                "mood": mood or "dreamy",
                "domain": domain or "AI tools",
                "seed": "Creativity Seed 101010"
            }
    
    # Test
    print("\n🧪 TESTING CreativityHandler\n")
    mock_dialog = MockDialog()
    mock_dialog.responses = ["dreamy", "AI tools", "no"]
    
    mock_service = MockCreativityService()
    handler = CreativityHandler(mock_dialog, mock_service)
    handler.generate_idea()