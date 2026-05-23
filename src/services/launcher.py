import subprocess
import webbrowser
import platform
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List
import time

class LauncherService:
    def __init__(self):
        self.system = platform.system()
        self.config_path = Path.home() / ".voice_assistant_config.json"
        self.app_mappings = {
            "chrome": "chrome",
            "google chrome": "google-chrome" if self.system == "Linux" else "chrome",
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
            "terminal": "gnome-terminal" if self.system == "Linux" else "cmd",
            "notion": "notion-desktop" if self.system == "Linux" else "notion",
            "telegram": "telegram-desktop" if self.system == "Linux" else "telegram",
        }
        self.web_services = {
            "github": "https://github.com",
            "notion": "https://www.notion.so",
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            # ... add all the ones you had
        }

    def normalize_app_name(self, raw_name: str) -> str:
        if not raw_name:
            return ""
        raw = raw_name.lower()
        if raw in self.app_mappings:
            return self.app_mappings[raw]
        for name, canonical in self.app_mappings.items():
            if name.lower() == raw:
                return canonical
        if '.' in raw:
            base = raw.split('.')[0]
            return self.app_mappings.get(base, base)
        return raw

    def find_application(self, app_name: str) -> str:
        app_name = self.normalize_app_name(app_name)
        if self.system == "Linux":
            if path := shutil.which(app_name):
                return path
            possible_paths = [
                f"/usr/bin/{app_name}",
                f"/usr/local/bin/{app_name}",
                f"/snap/bin/{app_name}",
                f"/usr/share/applications/{app_name}.desktop",
                Path.home() / f".local/share/applications/{app_name}.desktop"
            ]
            for p in possible_paths:
                if Path(p).exists():
                    return str(p)
            # search .desktop files
            for d in ["/usr/share/applications", Path.home()/".local/share/applications"]:
                if Path(d).exists():
                    for f in Path(d).glob("*.desktop"):
                        if app_name in f.name.lower():
                            return str(f)
            return ""
        elif self.system == "Darwin":
            result = subprocess.run(["mdfind", "-name", f"{app_name}.app"], capture_output=True, text=True)
            return result.stdout.strip().split('\n')[0] if result.stdout else ""
        elif self.system == "Windows":
            # simplified: search ProgramFiles
            for root in [os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", "")]:
                if root:
                    for exe in Path(root).rglob(f"{app_name}*.exe"):
                        return str(exe)
            return ""
        return ""

    def launch_target(self, target: str) -> bool:
        if not target:
            return False
        normalized = self.normalize_app_name(target.strip().lower())
        if normalized in self.web_services:
            webbrowser.open(self.web_services[normalized])
            return True
        app_path = self.find_application(normalized)
        if app_path:
            if self.system == "Linux" and app_path.endswith(".desktop"):
                subprocess.Popen(["gtk-launch", Path(app_path).stem], shell=True)
            else:
                subprocess.Popen([app_path], shell=(self.system == "Linux"))
            return True
        return False

    # workspace persistence
    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {"targets": [], "workspace": {}}
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except:
            return {"targets": [], "workspace": {}}

    def _save_config(self, config: dict):
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    def save_workspace(self, name: str, targets: List[str]):
        config = self._load_config()
        valid = []
        for t in targets:
            if isinstance(t, str) and t.strip() and not t.isdigit():
                norm = self.normalize_app_name(t.strip())
                if norm:
                    valid.append(norm)
        config.setdefault("workspace", {})[name] = valid
        self._save_config(config)

    def load_workspace(self, name: str) -> List[str]:
        config = self._load_config()
        return config.get("workspace", {}).get(name, [])

    def launch_workspace(self, name: str) -> bool:
        targets = self.load_workspace(name)
        if not targets:
            return False
        success_count = 0
        for t in targets:
            if self.launch_target(t):
                success_count += 1
            time.sleep(0.5)
        return success_count > 0