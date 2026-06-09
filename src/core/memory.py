# core/memory.py
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class Memory:
    """Memory management for conversation context and preferences."""
    
    def __init__(self, storage_file: str = "memory.json"):
        self.storage_file = storage_file
        self.short_term = {}      # Current conversation context
        self.long_term = {}       # Persistent across sessions
        
        self._load()
    
    # ========== Short-term memory ==========
    
    def remember(self, key: str, value: Any):
        self.short_term[key] = value
    
    def recall(self, key: str) -> Optional[Any]:
        return self.short_term.get(key)
    
    def forget(self, key: str):
        if key in self.short_term:
            del self.short_term[key]
    
    def clear_context(self):
        self.short_term = {}
    
    # ========== Long-term memory ==========
    
    def save_preference(self, key: str, value: Any):
        self.long_term[key] = value
        self._save()
    
    def get_preference(self, key: str, default=None) -> Any:
        return self.long_term.get(key, default)
    
    def delete_preference(self, key: str):
        if key in self.long_term:
            del self.long_term[key]
            self._save()
    
    # ========== Conversation context ==========
    
    def set_last_command(self, command: str, handler: str, parameters: dict = None):
        self.remember("last_command", {
            "text": command,
            "handler": handler,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def get_last_command(self) -> Optional[dict]:
        return self.recall("last_command")
    
    def set_last_result(self, result: Any):
        self.remember("last_result", result)
    
    def get_last_result(self) -> Optional[Any]:
        return self.recall("last_result")
    
    def set_context(self, key: str, value: Any):
        self.remember(key, value)
    
    def get_context(self, key: str) -> Optional[Any]:
        return self.recall(key)
    
    # ========== Follow-up question resolution ==========
    
    def resolve_follow_up(self, question: str) -> Optional[str]:
        """Resolve ambiguous follow-up questions like 'cancel it'."""
        last_command = self.get_last_command()
        last_result = self.get_last_result()
        
        # Handle pronouns
        if "it" in question.lower() or "that" in question.lower():
            if last_result:
                return f"{question.replace('it', last_result).replace('that', last_result)}"
            elif last_command:
                return f"{question.replace('it', last_command.get('text', 'it')).replace('that', last_command.get('text', 'that'))}"
        
        return None
    
    # ========== Persistence ==========
    
    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.long_term = data.get("long_term", {})
            except (json.JSONDecodeError, IOError):
                self.long_term = {}
    
    def _save(self):
        try:
            with open(self.storage_file, 'w') as f:
                json.dump({"long_term": self.long_term}, f, indent=2)
        except IOError:
            pass
    
    def __repr__(self):
        return f"<Memory short={len(self.short_term)} long={len(self.long_term)}>"