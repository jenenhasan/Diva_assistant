import platform
import subprocess
import shutil
import time


class LauncherHandler:
    def __init__(self, dialog, launcher_service):
        self.dialog = dialog
        self.launcher = launcher_service
    
    def register(self, router):
        """Register all launcher intents with the router."""
        router.register(r"open (the )?app|launch (the )?app|start (the )?app", self.handle_launch_app)
        router.register(r"open (the )?website|go to (the )?website", self.handle_launch_website)
        router.register(r"set up workspace|save workspace|create workspace", self.handle_setup_workspace)
        router.register(r"load workspace|launch workspace|start workspace|open my workspace", self.handle_launch_workspace)
        return self
    
    def handle_launch_app(self):
        """Launch an application by name."""
        app_name = self.dialog.listen_with_retry(
            "Which application would you like to open?",
            "Please say the application name again."
        )
        if not app_name:
            self.dialog.speak("Launch cancelled.")
            return
        
        self.dialog.show_thinking()
        
        # Try to launch
        success = self.launcher.launch_target(app_name)
        
        self.dialog.hide_thinking()
        
        if success:
            self.dialog.speak(f"Opening {app_name}.")
        else:
            self.dialog.speak(f"Sorry, I couldn't find {app_name}. Please check the name and try again.")
    
    def handle_launch_website(self):
        """Launch a website by name."""
        site_name = self.dialog.listen_with_retry(
            "Which website would you like to open?",
            "Please say the website name again."
        )
        if not site_name:
            self.dialog.speak("Launch cancelled.")
            return
        
        self.dialog.show_thinking()
        success = self.launcher.launch_target(site_name)
        self.dialog.hide_thinking()
        
        if success:
            self.dialog.speak(f"Opening {site_name}.")
        else:
            self.dialog.speak(f"Sorry, I couldn't find {site_name}. Please check the name and try again.")
    
    def handle_setup_workspace(self):
        """Setup a workspace by detecting open applications."""
        self.dialog.speak("Please open all the applications you want in your workspace.")
        self.dialog.speak("I'll wait for 10 seconds. Press any key when you're ready...")
        
        # Wait for user to open apps
        time.sleep(10)
        
        self.dialog.show_thinking()
        
        # Detect open windows (Linux only currently)
        detected_apps = self._detect_open_apps()
        
        if detected_apps:
            self.launcher.save_workspace("default", detected_apps)
            self.dialog.speak(f"Workspace saved with {len(detected_apps)} applications: {', '.join(detected_apps[:5])}")
            if len(detected_apps) > 5:
                self.dialog.speak(f"And {len(detected_apps) - 5} more.")
        else:
            self.dialog.speak("No applications detected. You can manually save a workspace by saying 'save workspace with chrome and vscode'")
        
        self.dialog.hide_thinking()
    
    def handle_launch_workspace(self):
        """Launch a saved workspace."""
        workspace_name = "default"  # Could ask user which workspace
        
        self.dialog.show_thinking()
        targets = self.launcher.load_workspace(workspace_name)
        
        if not targets:
            self.dialog.hide_thinking()
            self.dialog.speak("No workspace found. Please set up a workspace first by saying 'set up workspace'.")
            return
        
        self.dialog.speak(f"Launching your workspace with {len(targets)} applications.")
        
        success = self.launcher.launch_workspace(workspace_name)
        
        self.dialog.hide_thinking()
        
        if success:
            self.dialog.speak("Workspace launched successfully.")
        else:
            self.dialog.speak("Some applications failed to launch. Please check your workspace configuration.")
    
    def _detect_open_apps(self) -> list:
        """Detect currently open applications (Linux only)."""
        detected = []
        
        if platform.system() != "Linux":
            self.dialog.speak("Workspace detection is only available on Linux.")
            return []
        
        try:
            # Get list of open windows
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            windows = result.stdout.splitlines()
            
            app_names = []
            for window in windows:
                try:
                    window_id = window.split()[0]
                    proc = subprocess.run(
                        ['xprop', '-id', window_id, 'WM_CLASS'],
                        capture_output=True, text=True
                    )
                    # Extract app name from xprop output
                    if '"' in proc.stdout:
                        proc_name = proc.stdout.split('"')[1].lower()
                        app_names.append(proc_name)
                except (IndexError, subprocess.SubprocessError):
                    continue
            
            # Normalize and deduplicate
            for app in set(app_names):
                normalized = self.launcher.normalize_app_name(app)
                if normalized and normalized not in detected:
                    # Check if it's a known app or executable
                    if (normalized in self.launcher.app_mappings.values() or
                        normalized in self.launcher.web_services or
                        shutil.which(normalized)):
                        detected.append(normalized)
        
        except FileNotFoundError:
            self.dialog.speak("Please install wmctrl first: sudo apt install wmctrl")
        except Exception as e:
            print(f"Workspace detection error: {e}")
        
        return detected


if __name__ == "__main__":
    from unittest.mock import MagicMock
    
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
        
        def confirm(self, question):
            print(f"[CONFIRM] {question}")
            return True
    
    # Mock LauncherService
    class MockLauncherService:
        def launch_target(self, target):
            print(f"[LAUNCH] {target}")
            return True
        
        def save_workspace(self, name, targets):
            print(f"[SAVE WORKSPACE] {name}: {targets}")
        
        def load_workspace(self, name):
            return ["chrome", "vscode", "terminal"]
        
        def launch_workspace(self, name):
            print(f"[LAUNCH WORKSPACE] {name}")
            return True
        
        def normalize_app_name(self, name):
            return name
        
        app_mappings = {"chrome": "chrome", "vscode": "code"}
        web_services = {"github": "https://github.com"}
    
    # Test
    print("\n🧪 TESTING LauncherHandler\n")
    method = input("Which method? (app / website / setup / launch): ").strip().lower()
    
    mock_dialog = MockDialog()
    mock_launcher = MockLauncherService()
    handler = LauncherHandler(mock_dialog, mock_launcher)
    
    if method == "app":
        mock_dialog.responses = ["chrome"]
        handler.handle_launch_app()
    elif method == "website":
        mock_dialog.responses = ["github"]
        handler.handle_launch_website()
    elif method == "setup":
        handler.handle_setup_workspace()
    elif method == "launch":
        handler.handle_launch_workspace()
    else:
        print("Unknown method. Use 'app', 'website', 'setup', or 'launch'.")