import os
import random
import asyncio
from dotenv import load_dotenv
from qiskit import QuantumCircuit
from qiskit_aer.primitives import Sampler as AerSampler
from openai import AsyncOpenAI

load_dotenv()

# Available moods and domains
MOODS = [
    "dreamy", "intense", "philosophical", "electric", "playful", "melancholic", "cosmic", "limitless", "fluid",
    "hypnotic", "glitchy", "immersive", "rebellious", "jaded", "focused", "flowing", "curious", "frustrated", 
    "bold", "chaotic", "lucid", "wired", "anxious", "euphoric", "obsessed", "meditative", "restless", "haunted", "empowered"
]

DOMAINS = [
    "code interfaces", "AI tools", "neurotech", "emotion-based programming", "generative AI", "future UX", 
    "web metaphors", "holographic design", "voice interaction", "gesture systems", "dream-state compilers", 
    "generative art", "semantic search engines", "self-aware IDEs", "invisible UI", "time-based version control", 
    "biofeedback systems", "synthetic empathy algorithms", "quantum programming education", "mental model visualizers", 
    "AI companions for debugging", "ambient coding environments", "zero-click UI", "neural input editors", 
    "real-time mood-aware apps", "creative developer tools", "interactive thought mapping", "AI orchestration", 
    "multi-sensory coding", "emergent system design", "AR/VR for coders", "non-linear project timelines", "introspective IDEs"
]


class CreativityService:
    """Pure service for generating creative tech ideas using quantum seeds and GPT."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=self.api_key)

    @staticmethod
    def get_moods() -> list:
        """Return available moods."""
        return MOODS.copy()

    @staticmethod
    def get_domains() -> list:
        """Return available tech domains."""
        return DOMAINS.copy()

    @staticmethod
    def _generate_quantum_seed() -> str:
        """Generate a random seed using quantum circuit simulation."""
        num_qubits = 6
        circuit = QuantumCircuit(num_qubits)
        for i in range(num_qubits):
            circuit.h(i)
        circuit.measure_all()

        sampler = AerSampler()
        job = sampler.run([circuit], shots=1000)
        result = job.result()
        probs = result.quasi_dists[0]

        processed_probs = {
            format(state, f'0{num_qubits}b'): prob
            for state, prob in probs.items()
        }

        binary_seed = random.choices(
            population=list(processed_probs.keys()),
            weights=list(processed_probs.values()),
            k=1
        )[0]

        return f"Creativity Seed {binary_seed}"

    @staticmethod
    def _mutate_prompt_by_seed(prompt: str, seed_str: str) -> str:
        """Enhance prompt with seed-based constraints."""
        seed = seed_str.replace("Creativity Seed ", "").split(" ")[0].zfill(6)

        # Segment 1: Mood / Theme
        if seed[0:2] == "00":
            prompt += " The idea must work offline and use no mouse."
        elif seed[0:2] == "01":
            prompt += " The idea should challenge perceptions of time and sequence."
        elif seed[0:2] == "10":
            prompt += " Infuse speculative tech like brain-machine interfaces."
        else:
            prompt += " Enable the idea to run in alternate realities (AR/VR)."

        # Segment 2: Aesthetic Twist
        if seed[2:4] == "00":
            prompt += " Give it a minimalist interface with a single input field."
        elif seed[2:4] == "01":
            prompt += " Add a retro twist, inspired by 80s arcade machines."
        elif seed[2:4] == "10":
            prompt += " Make it feel like a dream, using subconscious metaphors."
        else:
            prompt += " Involve sound-based interactions or sonification."

        # Segment 3: Perspective / Usage
        if seed[4:6] == "00":
            prompt += " Imagine this idea is for children or teenagers."
        elif seed[4:6] == "01":
            prompt += " It should be used by AI agents, not just humans."
        elif seed[4:6] == "10":
            prompt += " Focus on nonverbal communication or body language."
        else:
            prompt += " Make it useful in remote, off-grid environments."

        return prompt

    @staticmethod
    def _calculate_temperature(seed_str: str) -> float:
        """Calculate GPT temperature based on seed entropy."""
        binary = seed_str.replace("Creativity Seed ", "").split(" ")[0]
        entropy = sum(int(b) for b in binary)
        return 0.7 + (entropy / 6) * 0.1

    def _generate_prompt(self, mood: str, domain: str, seed: str, custom_thought: str = None) -> str:
        """Build the prompt for GPT."""
        prompt = (
            f"Act as a inventive software architect who proposes groundbreaking, creative, extraordinary "
            f"and technically feasible coding project ideas. "
            f"The user feels {mood} and is curious about {domain}. "
            f"The random creativity seed is: '{seed}'. "
        )
        if custom_thought:
            prompt += f"They are also thinking: {custom_thought}. "

        prompt = self._mutate_prompt_by_seed(prompt, seed)

        prompt += (
            " Your generated idea MUST satisfy ALL of the above constraints from the seed exactly and fully. "
            "Do NOT ignore or loosely interpret any of the constraints. "
            "Generate a project idea that feels revolutionary or futuristic, possibly blending unusual fields or techniques. "
            "Explain the idea in clear, concise, and programmer-friendly terms. Avoid poetic or overly metaphorical language. "
            "Include details such as the user interface, how it works, what technologies or libraries might be used, and why it matters. "
            "The idea can be imaginative, something not very common in the market, but the explanation should be grounded and buildable."
        )
        return prompt

    async def generate_idea(self, mood: str = None, domain: str = None, custom_thought: str = None) -> dict:
        """
        Generate a creative tech idea.
        
        Args:
            mood: User's current mood (optional, random if not provided)
            domain: Tech domain (optional, random if not provided)
            custom_thought: Additional user input
            
        Returns:
            dict with keys: idea, mood, domain, seed, prompt (or error)
        """
        mood = mood or random.choice(MOODS)
        domain = domain or random.choice(DOMAINS)
        seed = self._generate_quantum_seed()
        prompt = self._generate_prompt(mood, domain, seed, custom_thought)
        temperature = self._calculate_temperature(seed)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=400
            )
            idea = response.choices[0].message.content.strip()
            return {
                "idea": idea,
                "mood": mood,
                "domain": domain,
                "seed": seed,
                "prompt": prompt,
                "success": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_generate_idea(self, mood: str = None, domain: str = None, custom_thought: str = None) -> dict:
        """Synchronous wrapper for generate_idea."""
        return asyncio.run(self.generate_idea(mood, domain, custom_thought))