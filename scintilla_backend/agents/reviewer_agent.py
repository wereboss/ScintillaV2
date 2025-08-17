from typing import List, Dict, Optional, Any
from db.db_manager import DatabaseManager
from agents.scratchpad_agent import ScratchpadAgent
from config.settings import settings
from datetime import datetime
import json
import requests

class ReviewerAgent:
    """
    Agent responsible for managing the Review process.
    """
    def __init__(self):
        self.content_db_manager = DatabaseManager(settings.content_db_path, schema_name="content")
        self.scratchpad_agent = ScratchpadAgent()
        self.notion_api_url = "https://api.notion.com/v1/pages"

    def _post_to_notion(self, content_data: Dict) -> bool:
        """
        Posts the content to Notion using the API.
        """
        if not settings.notion_api_key or not settings.notion_database_id:
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Notion API key or database ID not set. Skipping post.")
            return False

        headers = {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        # Helper function to convert text to Notion rich text
        def to_rich_text(text: str) -> List[Dict]:
            return [{"text": {"content": text}}]
        
        # Helper function to convert list of tags to Notion multi-select format
        def to_multi_select(tags: List[str]) -> List[Dict]:
            return [{"name": tag.strip()} for tag in tags]

        # Convert next_actions and next_reading to a formatted Rich Text string
        def format_next_items(items: List[Any], item_type: str) -> str:
            if not items:
                return "No items provided."
            formatted_text = ""
            for item in items:
                if item_type == "actions":
                    formatted_text += f"- **{item.get('name', 'N/A')}** (Priority: {item.get('priority', 'N/A').capitalize()})\n"
                else: # item_type == "reading"
                    formatted_text += f"- {item}\n"
            return formatted_text.strip()
        
        properties = {
            "Title": {"title": to_rich_text(content_data.get('title', ''))},
            "Project Type": {"select": {"name": content_data.get('project_type', '').capitalize()}},
            "Status": {"status": {"name": "Approved"}}, # Corrected Status property
            "Category Tags": {"multi_select": to_multi_select(content_data.get('category_tags', []))},
            "Content": {"rich_text": to_rich_text(content_data.get('content', ''))},
            "Source URLs": {"url": content_data.get('context_urls', '') if content_data.get('context_urls', '') else None},
            "Created Date": {"date": {"start": content_data.get('timestamp', '')}},
            "Approved Date": {"date": {"start": datetime.now().isoformat()}}
        }

        # Conditionally add Next Actions or Next Reading
        if content_data.get('project_type') in ["build", "research"]:
            formatted_actions = format_next_items(content_data.get('next_actions', []), "actions")
            properties["Next Actions"] = {"rich_text": to_rich_text(formatted_actions)}
        
        if content_data.get('project_type') in ["article", "research"]:
            formatted_reading = format_next_items(content_data.get('next_reading', []), "reading")
            properties["Next Reading"] = {"rich_text": to_rich_text(formatted_reading)}


        payload = {
            "parent": {"database_id": settings.notion_database_id},
            "properties": properties
        }
        
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Sending payload to Notion API: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(self.notion_api_url, headers=headers, json=payload)
            response.raise_for_status()
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Successfully posted to Notion. Response: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().isoformat()}] Error posting to Notion: {e}")
            print(f"[{datetime.now().isoformat()}] Notion response content: {response.text}")
            return False

    def get_all_content_for_review(self) -> List[Dict]:
        """Retrieves all processed content items from the database."""
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Fetching all processed content for review.")
        
        # get_all_content now returns lists, no need to deserialize here
        return self.content_db_manager.get_all_content()

    def approve_and_post_to_notion(self, content_id: str) -> bool:
        """
        Approves a content item, posts to Notion, and purges it.
        """
        content_data = self.content_db_manager.get_content_by_id(content_id)
        if not content_data:
            print(f"[{datetime.now().isoformat()}] Content with ID {content_id} not found.")
            return False
            
        success = self._post_to_notion(content_data)

        if success:
            # After successful posting to Notion, we delete the content from our local db.
            delete_success = self.content_db_manager.delete_content(content_id)
            if delete_success:
                if settings.is_debug_mode:
                    print(f"[{datetime.now().isoformat()}] Successfully posted and purged content with ID: {content_id}")
                # Also update the status of the original idea in the scratchpad to 'approved'
                self.scratchpad_agent.update_status(content_data['idea_id'], 'approved')
                return True
            else:
                 if settings.is_debug_mode:
                    print(f"[{datetime.now().isoformat()}] Successfully posted to Notion, but failed to delete from local DB.")
                 return False

        return False

    def reject_and_requeue(self, content_id: str, correction_text: str, correction_urls: str) -> bool:
        """
        Rejects a content item, creates a new entry in the scratchpad,
        and purges the old content.
        """
        content_data = self.content_db_manager.get_content_by_id(content_id)
        if not content_data:
            print(f"[{datetime.now().isoformat()}] Content with ID {content_id} not found.")
            return False

        # Get original idea text and context
        original_idea = self.scratchpad_agent.get_idea(content_data['idea_id'])
        if not original_idea:
            print(f"[{datetime.now().isoformat()}] Original idea with ID {content_data['idea_id']} not found.")
            return False

        # Append corrections to original idea text and URLs
        new_idea_text = f"{original_idea['idea_text']}\n\n[Correction Notes]: {correction_text}"
        new_context_urls = f"{original_idea['context_urls']},{correction_urls}" if original_idea['context_urls'] else correction_urls
        
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Re-queuing rejected idea with ID: {content_data['idea_id']}")
            print(f"[{datetime.now().isoformat()}] New idea text: {new_idea_text}")

        # Add the corrected idea back to the scratchpad queue
        new_idea_id = self.scratchpad_agent.add_new_idea(new_idea_text, new_context_urls)
        
        if new_idea_id:
            # Mark the original idea as 'rejected'
            self.scratchpad_agent.update_status(content_data['idea_id'], 'rejected')
            # Purge the processed content from the content database
            self.content_db_manager.delete_content(content_id)
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Rejected content: {content_id}, re-queued with new ID: {new_idea_id}")
            return True
        
        return False
