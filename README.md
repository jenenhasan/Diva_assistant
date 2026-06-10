# 🎙️ Diva — AI Voice Assistant for Developers

> *Your hands-free co-pilot for the entire dev workflow.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-1.5_Pro-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Gesture-00897B?logo=google&logoColor=white)](https://mediapipe.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 What Is Diva?

**Diva** is a fully voice-controlled AI assistant built for developers. It listens, understands your intent, and acts — reading emails, managing your calendar, interacting with GitHub, scaffolding new projects, controlling your screen with hand gestures, and falling back to **Gemini 1.5 Pro** for anything it doesn't recognise out of the box.

Built with a **Flask-inspired app factory pattern**, each feature is an independent, fault-tolerant module — if one integration fails to load, the rest of the assistant keeps running.

---

## 🔄 From Monolith to Architecture — The Story Behind This Project

Diva is a complete ground-up rewrite of [dev-assistant](https://github.com/jenenhasan/dev-assistant), my earlier voice assistant project. Same vision. Completely different engineering.

The original version worked — but everything lived in one giant class. Adding a feature meant editing the core file, nothing was testable, and one broken import could crash the whole assistant. I decided to rebuild it from scratch and ask: *"what would this look like if I built it properly?"*

| | dev-assistant (v1) | Diva (v2) |
|---|---|---|
| Structure | Single `main.py` monolith | Layered: `audio` → `core` → `handlers` → `services` → `integrations` |
| Adding a feature | Edit the core class | Add one `_register_*()` function, nothing else changes |
| Fault tolerance | One error crashes everything | Each module fails independently, rest keeps running |
| Speech-to-text | Google Speech Recognition only | Dual engine: Silero + Whisper with confidence-based fallback |
| AI fallback | Always calls Gemini | Gemini only fires when regex routing fails — minimal API cost |
| Conversation memory | None | Short-term + persistent long-term + follow-up pronoun resolution |
| Tests | None | 6 test files with pytest |
| Design patterns | None | App factory + dependency injection + intent router |

> *"I originally built this as a monolith — everything in one class. It worked, but adding features was painful and nothing was testable. I rearchitected it from scratch applying separation of concerns, dependency injection, and a factory pattern. The new version has a test suite, and you can add a new capability without touching any existing code."*

---

## ✨ Feature Highlights

| Feature | What it does |
|---|---|
| 🎤 **Dual STT Engine** | Runs Silero first for speed; falls back to OpenAI Whisper for accuracy |
| 🧠 **Gemini 1.5 Pro fallback** | Any command not matched by regex is answered by Gemini AI |
| 📅 **Google Calendar** | Create, query, and manage calendar events by voice |
| 📧 **Gmail** | Read, send, and manage emails hands-free |
| 🐙 **GitHub** | Query repos, issues, and PRs via voice |
| 🏗️ **Project Scaffolding** | Scaffold Flask / Django / FastAPI projects with a spoken command |
| 🖐️ **Hand Gesture Control** | MediaPipe-powered gestures for scroll and tab — no keyboard needed |
| 🧠 **Conversation Memory** | Short-term + persistent long-term memory; resolves follow-up pronouns like "cancel *it*" |
| 🖥️ **App Launcher** | Open any dev tool instantly by voice |
| 🐛 **Terminal Error Handler** | Reads terminal errors and gets AI-powered fix suggestions |

---

## 🏗️ Architecture

Diva follows a clean **layered architecture** inspired by Flask's `create_app()` factory pattern:

```
src/
├── main.py                  # Entry point
├── app.py                   # App factory — wires all components
│
├── core/                    # Framework layer
│   ├── orchestrator.py      # Main run loop (listen → route → respond)
│   ├── intent_router.py     # Regex-based intent matching
│   ├── dialog_manager.py    # speak / listen interface
│   ├── memory.py            # Short-term + persistent memory
│   └── context_manager.py
│
├── audio/                   # Speech layer
│   ├── stt_engine.py        # Silero + Whisper dual STT
│   ├── tts_engine.py        # Text-to-speech
│   ├── recorder.py          # Microphone recording
│   └── wakeword.py          # Wake word detection
│
├── handlers/                # Intent handlers (one per feature)
│   ├── calendar_handler.py
│   ├── email_handler.py
│   ├── github_handler.py
│   ├── launcher_handler.py
│   ├── gesture_handler.py
│   ├── terminal_error_handler.py
│   ├── creativity_handler.py
│   ├── presentation_gesture_handler.py
│   └── schaffolding_handler.py
│
├── services/                # Business logic (pure, no speech)
│   ├── gemini.py
│   ├── calendar_service.py
│   ├── email.py
│   ├── github.py
│   ├── gesture.py           # MediaPipe hand tracking
│   ├── launcher.py
│   ├── schaffolding.py      # Project template engine
│   ├── creativity.py
│   ├── terminal_error.py
│   ├── smartsearch.py
│   └── TestGenerator.py
│
integrations/                # Third-party API clients
│   ├── gmail_client.py
│   ├── google_calendar_client.py
│   └── github_client.py
│
tests/                       # Test suite
    ├── test_audio.py
    ├── test_email_handler.py
    ├── test_email_service.py
    ├── test_github_client.py
    └── test_launcher.py
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| AI / LLM | Google Gemini 1.5 Pro |
| Speech-to-Text | OpenAI Whisper + Silero STT |
| Text-to-Speech | pyttsx3 / TTS engine |
| Gesture Control | MediaPipe + OpenCV |
| Google APIs | Gmail API, Google Calendar API |
| Version Control API | PyGitHub |
| Testing | pytest |

---

## ⚡ Getting Started

### Prerequisites

- Python 3.10+
- A working microphone
- Google Cloud credentials (`credentials.json`) for Gmail & Calendar
- GitHub personal access token
- Gemini API key

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/jenenhasan/Diva_assistant.git
cd Diva_assistant

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your environment variables
cp .env.example .env
# Fill in API_KEY (Gemini), GitHub token, etc.

# 5. Run Diva
python src/main.py
```

### Example Voice Commands

```
"Hey Diva, open VS Code"
"Schedule a meeting tomorrow at 3pm"
"Read my latest emails"
"Create a Flask project called my-app"
"What are my open GitHub issues?"
"Start gesture control"
"Fix this terminal error"
```

---

## 🧩 How to Add a New Feature

Diva's modular design makes extending it straightforward — adding a feature never touches the core:

1. Create `src/services/your_service.py` — pure business logic, no speech
2. Create `src/handlers/your_handler.py` — voice interface, calls the service
3. Add one line in `src/app.py`: `_register_your_feature(router, dialog)`

That's it. If it fails to load, the rest of Diva keeps running.

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 💡 Design Decisions

**Why dual STT (Silero + Whisper)?**
Silero is fast and lightweight — great for short, clear commands. When confidence is low, Diva automatically falls back to Whisper for better accuracy. This keeps latency minimal for common commands while staying robust for unclear speech.

**Why Gemini as a fallback?**
Regex routing handles known intents cheaply and instantly. Gemini only fires when nothing matches — keeping API costs minimal while making Diva handle open-ended questions naturally.

**Why Flask-style app factory?**
Each feature registers independently. A missing API key or broken integration won't crash the whole assistant — it just skips that module and logs a warning.



---

## 👩‍💻 Author

**Jenen Hasan** — Software engineer

[![GitHub](https://img.shields.io/badge/GitHub-jenenhasan-181717?logo=github)](https://github.com/jenenhasan)

---

## 📄 License

This project is open source under the [MIT License](LICENSE).
