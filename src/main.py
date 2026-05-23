import sys
sys.path.insert(0, '.')
from audio.tts_engine import TTSEngine
from audio.stt_engine import STTEngine
from audio.recorder import MicrophoneRecorder
from core.dialog_manager import DialogManager
from core.intent_router import IntentRouter
from core.orchestrator import Orchestrator
from integrations.google_calendar_client import GoogleCalendarClient
from integrations.gmail_client import GmailClient
from src.services.calendar import CalendarService
from src.services.email import EmailService
from src.services.launcher import LauncherService
from handlers.calendar_handler import CalendarHandler
from src.handlers.email_handler import EmailHandler
from src.handlers.launcher import LauncherHandler
from services.gemini import GeminiService
def main():
    # engines
    tts = TTSEngine()
    stt = STTEngine()
    recorder = MicrophoneRecorder()
    dialog = DialogManager(tts, stt, recorder)
    

    # clients
    calendar_client = GoogleCalendarClient()
    gmail_client = GmailClient()

    # services
    calendar_svc = CalendarService(calendar_client)
    email_svc = EmailService(gmail_client)
    launcher_svc = LauncherService()
    gemini_svc = GeminiService()

    # handlers
    calendar_hdl = CalendarHandler(dialog, calendar_svc)
    email_hdl = EmailHandler(dialog, email_svc)
    launcher_hdl = LauncherHandler(dialog, launcher_svc)

    # router
    router = IntentRouter()
    router.register(r"create (an? )?event|schedule (a )?meeting", calendar_hdl.create_event)
    router.register(r"create (a )?task|add (a )?task", calendar_hdl.create_task)
    router.register(r"show (upcoming )?events", calendar_hdl.show_upcoming_events)
    router.register(r"send (an? )?email|compose (an? )?email", email_hdl.send_email)
    router.register(r"check inbox|show emails", email_hdl.check_inbox)
    router.register(r"search email", email_hdl.search_email)
    router.register(r"open (the )?app|launch", launcher_hdl.launch_app)
    router.register(r"set up workspace", launcher_hdl.setup_workspace)
    router.register(r"load workspace|launch workspace", launcher_hdl.launch_workspace)


    # start
    orch = Orchestrator(dialog, router, {}, gemini_service=None)  # optionally add Gemini
    orch.run()

if __name__ == "__main__":
    main()