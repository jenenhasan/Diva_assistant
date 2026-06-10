"""
Diva — AI Voice Assistant for Developers
App factory inspired by Flask's create_app() pattern.

Each feature is registered independently:
  - If a feature fails to load, the app still starts
  - Add new features by adding a _register_*() function
  - main.py stays clean — it only calls create_app().run()
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.intent_router import IntentRouter
from core.orchestrator import Orchestrator
from core.memory import Memory
from core.dialog_manager import DialogManager
from audio.tts_engine import TTSEngine
from audio.stt_engine import STTEngine
from audio.recorder import MicrophoneRecorder


def create_app() -> Orchestrator:
    """
    Builds and wires all Diva components.
    Returns a ready-to-run Orchestrator.
    """
    print("[Diva] Starting up...\n")

    # ── core (always available) ───────────────────────────────
    recorder = MicrophoneRecorder(device_index=None, rate=44100, channels=1)
    dialog = DialogManager(TTSEngine(), STTEngine(), recorder)
    memory = Memory()
    ai     = _init_ai()
    router = IntentRouter()

    # ── feature registration ──────────────────────────────────
    _register_calendar(router, dialog, ai)
    _register_email(router, dialog, ai)
    _register_github(router, dialog, ai)
    _register_launcher(router, dialog)
    # _register_search(router, dialog)
    _register_scaffolding(router, dialog)
    _register_presentation(router, dialog, ai)
    _register_creativity(router, dialog, ai)
    _register_gesture(router, dialog)
    _register_terminal(router, dialog, ai)
    # _register_quantity(router, dialog, ai)

    print("\n[Diva] Ready.\n")
    return Orchestrator(dialog, router, {}, gemini_service=ai, memory=memory)


# ── AI initialisation ─────────────────────────────────────────


def _init_ai():
    """
    Gemini is optional — app runs without it using regex routing only.
    Only fires when regex routing fails (keeps API costs minimal).
    """
    try:
        from services.gemini import GeminiService
        svc = GeminiService()
        print("[Diva] ✓ Gemini AI")
        return svc
    except Exception as e:
        print(f"[Diva] ✗ Gemini unavailable: {e}")
        return None


# ── feature registration ──────────────────────────────────────
# Each function is self-contained:
#   - imports its own dependencies
#   - handles its own errors
#   - registers its own intents
# Adding a new feature = add one _register_*() function + call it above.


def _register_calendar(router, dialog, ai):
    try:
        from integrations.google_calendar_client import GoogleCalendarClient
        from services.calendar_service import CalendarService
        from handlers.calendar_handler import Calendarhandler
        Calendarhandler(dialog, CalendarService(GoogleCalendarClient()), ai).register(router)
        print("[Diva] ✓ Calendar")
    except Exception as e:
        print(f"[Diva] ✗ Calendar unavailable: {e}")


def _register_email(router, dialog, ai):
    try:
        from integrations.gmail_client import GmailClient
        from services.email import EmailService
        from handlers.email_handler import Emailhandler
        Emailhandler(dialog, EmailService(GmailClient()), ai).register(router)
        print("[Diva] ✓ Email")
    except Exception as e:
        print(f"[Diva] ✗ Email unavailable: {e}")


def _register_github(router, dialog, ai):
    try:
        from integrations.github_client import GitHubClient
        from services.github import GitHubService
        from handlers.github_handler import GitHubHandler      
        github_client = GitHubClient()
        github_service = GitHubService(github_client)
        handler = GitHubHandler(dialog, github_service, ai)
        handler.register(router)
        print("[Diva] ✓ GitHub")
    except Exception as e:
        print(f"[Diva] ✗ GitHub unavailable: {e}")


def _register_launcher(router, dialog):
    try:
        from services.launcher import LauncherService
        from handlers.launcher_handler import LauncherHandler
        LauncherHandler(dialog, LauncherService()).register(router)
        print("[Diva] ✓ Launcher")
    except Exception as e:
        print(f"[Diva] ✗ Launcher unavailable: {e}")


# def _register_search(router, dialog):
#     try:
#         from services.search import SearchService
#         from handlers.search_handler import SearchHandler
#         SearchHandler(dialog, SearchService()).register(router)
#         print("[Diva] ✓ Search")
#     except Exception as e:
#         print(f"[Diva] ✗ Search unavailable: {e}")


def _register_scaffolding(router, dialog):
    try:
        from services.schaffolding import ScaffoldingManager
        from handlers.schaffolding_handler import ScaffoldingHandler
        ScaffoldingHandler(dialog, ScaffoldingManager()).register(router)
        print("[Diva] ✓ Scaffolding")
    except Exception as e:
        print(f"[Diva] ✗ Scaffolding unavailable: {e}")


def _register_presentation(router, dialog, ai):
    try:
        from handlers.presentation_gesture_handler import PresentationGestureHandler
        PresentationGestureHandler(dialog, ai).register(router)
        print("[Diva] ✓ Presentation")
    except Exception as e:
        print(f"[Diva] ✗ Presentation unavailable: {e}")


def _register_creativity(router, dialog, ai):
    if not ai:
        print("[Diva] ✗ Creativity skipped (no AI)")
        return
    try:
        from services.creativity import CreativityService
        from handlers.creativity_handler import CreativityHandler
        CreativityHandler(dialog, CreativityService(ai)).register(router)
        print("[Diva] ✓ Creativity")
    except Exception as e:
        print(f"[Diva] ✗ Creativity unavailable: {e}")


def _register_gesture(router, dialog):
    try:
        from services.gesture import GestureService
        from handlers.gesture_handler import GestureHandler
        gesture_service = GestureService(show_camera=False)
        GestureHandler(dialog, gesture_service).register(router) 
        print("[Diva] ✓ Gesture")
    except Exception as e:
        print(f"[Diva] ✗ Gesture unavailable: {e}")


def _register_terminal(router, dialog, ai):
    try:
        from handlers.terminal_error_handler import TerminalHandler 
        TerminalHandler(dialog, ai).register(router)
        print("[Diva] ✓ Terminal")
    except Exception as e:
        print(f"[Diva] ✗ Terminal unavailable: {e}")


# def _register_quantity(router, dialog, ai):
#     try:
#         from handlers.quantity_handler import QuantityHandler             # rename to match your file
#         QuantityHandler(dialog, ai).register(router)
#         print("[Diva] ✓ Quantity")
#     except Exception as e:
#         print(f"[Diva] ✗ Quantity unavailable: {e}")