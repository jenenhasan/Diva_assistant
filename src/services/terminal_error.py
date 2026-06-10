import subprocess
import hashlib
import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class TerminalService:
    """Pure service for terminal command execution and error logging."""
    
    def __init__(self, gemini_service=None):
        """
        Args:
            gemini_service: Optional Gemini service for error explanations
        """
        self.gemini = gemini_service
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.parent_page_id = os.getenv("NOTION_PAGE_ID")
        self.db_id_file = "db_id.txt"
        self.logged_hashes = set()
        
        if self.notion_token and self.parent_page_id:
            self.db_id = self._load_or_create_database()
        else:
            self.db_id = None

    # ========== Public methods ==========
    
    def run_command(self, command: str) -> dict:
        """
        Execute a shell command and return result.
        
        Returns:
            {"success": bool, "output": str, "error": str, "return_code": int}
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 30 seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_and_log(self, command: str) -> dict:
        """
        Execute command and log any error to Notion with Gemini explanation.
        
        Returns:
            {"success": bool, "output": str, "error": str, "explanation": str, "logged": bool}
        """
        result = self.run_command(command)
        
        if result["success"]:
            return {
                "success": True,
                "output": result["output"],
                "error": "",
                "explanation": "",
                "logged": False
            }
        
        # Get Gemini explanation if available
        explanation = ""
        if self.gemini:
            try:
                prompt = f"Command: {command}\nError: {result['error'][:1500]}\nExplain the error and suggest a fix in 2-3 sentences."
                explanation = self.gemini.get_answer(prompt)
            except Exception as e:
                explanation = f"Gemini error: {str(e)[:100]}"
        
        # Log to Notion
        logged = self._log_to_notion(
            error_message=result["error"] or result["output"],
            command=command,
            gemini_explanation=explanation
        )
        
        return {
            "success": False,
            "output": result["output"],
            "error": result["error"],
            "explanation": explanation,
            "logged": logged
        }

    # ========== Private methods ==========
    
    def _log_to_notion(self, error_message: str, command: str, gemini_explanation: str) -> bool:
        """Log error to Notion database. Returns True if successful."""
        if not self.db_id or not self.notion_token:
            return False

        # Deduplication
        error_hash = hashlib.md5(error_message.encode()).hexdigest()
        if error_hash in self.logged_hashes:
            return False
        self.logged_hashes.add(error_hash)

        url = "https://api.notion.com/v1/pages"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        data = {
            "parent": {"database_id": self.db_id},
            "properties": {
                "Error Message": {"title": [{"text": {"content": error_message[:100]}}]},
                "Command": {"rich_text": [{"text": {"content": command[:200]}}]},
                "Stack Trace": {"rich_text": [{"text": {"content": error_message[:2000]}}]},
                "Time": {"date": {"start": timestamp}},
                "Gemini Explanation": {"rich_text": [{"text": {"content": gemini_explanation[:2000]}}]}
            }
        }

        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def _load_or_create_database(self):
        """Load existing database ID or create new."""
        if os.path.exists(self.db_id_file):
            with open(self.db_id_file, "r") as f:
                return f.read().strip()
        return self._create_database()

    def _create_database(self):
        """Create a new Notion database for errors."""
        url = "https://api.notion.com/v1/databases"
        data = {
            "parent": {"type": "page_id", "page_id": self.parent_page_id},
            "title": [{"type": "text", "text": {"content": "Terminal Error Logs"}}],
            "properties": {
                "Error Message": {"title": {}},
                "Command": {"rich_text": {}},
                "Stack Trace": {"rich_text": {}},
                "Time": {"date": {}},
                "Gemini Explanation": {"rich_text": {}}
            }
        }
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        db_id = response.json()["id"]
        with open(self.db_id_file, "w") as f:
            f.write(db_id)
        return db_id