from db.db_manager import DatabaseManager
from config.settings import settings
from typing import List, Dict, Optional
from datetime import datetime

class ScratchpadAgent:
    """
    Agent responsible for managing the Idea Scratchpad.
    This acts as a controller for the database logic.
    """
    def __init__(self):
        self.db_manager = DatabaseManager(settings.scratchpad_db_path)

    def add_new_idea(self, idea_text: str, context_urls: str) -> str:
        """Adds a new idea to the database."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Adding new idea to scratchpad.")
        return self.db_manager.add_idea(idea_text, context_urls)

    def get_all_ideas(self) -> List[Dict]:
        """Retrieves all ideas in the queue."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Fetching all ideas from scratchpad.")
        return self.db_manager.get_all_ideas()

    def get_pending_ideas(self) -> List[Dict]:
        """Retrieves ideas in the queue that have not been processed."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Fetching pending ideas from scratchpad.")
        return self.db_manager.get_pending_ideas()
        
    def delete_idea_by_id(self, idea_id: str) -> bool:
        """Deletes an idea from the database."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Deleting idea with ID: {idea_id}")
        return self.db_manager.delete_idea(idea_id)

    def update_status(self, idea_id: str, status: str) -> bool:
        """Updates the status of an idea."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Updating status of idea {idea_id} to '{status}'")
        return self.db_manager.update_idea_status(idea_id, status)

    def get_idea(self, idea_id: str) -> Optional[Dict]:
        """Retrieves a single idea by its ID."""
        return self.db_manager.get_idea(idea_id)

