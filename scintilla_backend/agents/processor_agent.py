import json
from typing import Dict, List, Any, Optional
import requests
import uuid
import time
from datetime import datetime
import ollama

from config.settings import settings
from agents.scratchpad_agent import ScratchpadAgent
from db.db_manager import DatabaseManager

class ProcessorAgent:
    """
    Agent responsible for processing ideas using Ollama.
    This agent is called by the scheduled script.
    """
    def __init__(self):
        self.scratchpad_agent = ScratchpadAgent()
        self.content_db_manager = DatabaseManager(settings.content_db_path, schema_name="content")
        self.prompts = self._load_prompts()
        self.ollama_client = ollama.Client(host=settings.ollama_base_url)
        self.log_manager = DatabaseManager(settings.processor_log_db_path, schema_name="processor_log")
        self.log_manager.create_tables()

    def _load_prompts(self) -> Dict:
        """Loads prompt templates from the prompts.json file."""
        try:
            with open("config/prompts.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[{datetime.now().isoformat()}] Error: prompts.json not found. The file will be created on application startup.")
            return {}

    def _call_ollama(self, prompt_text: str) -> Dict:
        """
        Sends a request to the local Ollama instance and returns the generated JSON.
        """
        try:
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Starting Ollama API call...")
                start_time = time.perf_counter()
                
            response = self.ollama_client.generate(
                model=settings.ollama_model_name,
                prompt=prompt_text,
                format="json",
                stream=False
            )
            
            if settings.is_debug_mode:
                end_time = time.perf_counter()
                print(f"[{datetime.now().isoformat()}] Ollama API call finished in {end_time - start_time:.2f} seconds.")
            
            # The response body contains the generated text
            generated_text = response.get("response", "")
            
            # Ollama might wrap the JSON in other text, so we'll try to find and parse it
            # A simple approach is to find the first '{' and last '}'
            start_index = generated_text.find('{')
            end_index = generated_text.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                json_string = generated_text[start_index:end_index]
                return json.loads(json_string)
            else:
                if settings.is_debug_mode:
                    print(f"[{datetime.now().isoformat()}] Failed to find a JSON object in the Ollama response.")
                return {}

        except ollama.exceptions.OllamaException as e:
            print(f"[{datetime.now().isoformat()}] Error calling Ollama API: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[{datetime.now().isoformat()}] Error parsing JSON from Ollama response: {e}")
            return {}
    
    def process_idea(self, idea_data: Dict) -> Optional[str]:
        """Processes a single idea from the scratchpad and stores the result."""
        idea_id = idea_data["id"]
        idea_text = idea_data["idea_text"]
        context_urls = idea_data["context_urls"]

        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Starting processing for idea ID: {idea_id}")
            print(f"[{datetime.now().isoformat()}] Idea Text: {idea_text}")
            print(f"[{datetime.now().isoformat()}] Context URLs: {context_urls}")

        self.log_manager.add_log_entry(idea_id, f"Processing idea: {idea_id}")

        # Determine project type (default to research if intent is unclear)
        project_type = "research"
        if "build" in idea_text.lower():
            project_type = "build"
        elif "article" in idea_text.lower() or "write" in idea_text.lower():
            project_type = "article"
        
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Detected project type: '{project_type}'")

        # Get the appropriate prompt
        prompts_for_type = self.prompts.get(project_type)
        if not prompts_for_type:
            print(f"[{datetime.now().isoformat()}] No prompts found for project type: {project_type}. Skipping.")
            self.scratchpad_agent.update_status(idea_id, "error")
            return None

        # Generate content with a single Ollama call that returns JSON
        full_prompt = prompts_for_type["full_prompt"].format(idea_text=idea_text, context_urls=context_urls)
        ollama_response = self._call_ollama(full_prompt)
        
        if not ollama_response:
            print(f"[{datetime.now().isoformat()}] Ollama returned an empty response for idea: {idea_id}")
            self.scratchpad_agent.update_status(idea_id, "error")
            self.log_manager.add_log_entry(idea_id, "Ollama returned an empty response.")
            return None

        # Validate the Ollama response
        if not self._validate_ollama_response(ollama_response, project_type):
            print(f"[{datetime.now().isoformat()}] Ollama response for idea {idea_id} failed validation. Re-queuing.")
            self.scratchpad_agent.update_status(idea_id, "reprocess")
            self.log_manager.add_log_entry(idea_id, "Response failed validation. Re-queuing.")
            return None

        # Extract data from the JSON response
        title = ollama_response.get("title", "No Title")
        generated_content = ollama_response.get("content", "No Content")
        category_tags_list = ollama_response.get("category_tags", [])
        
        next_actions_list = []
        next_reading_list = []

        if project_type in ["article", "research"]:
            next_reading_list = ollama_response.get("next_reading", [])
            # Robust conversion: if next_reading is a list of dictionaries, convert it to a list of strings
            if next_reading_list and isinstance(next_reading_list[0], dict):
                 next_reading_list = [str(item) for item in next_reading_list]
        
        if project_type in ["build", "research"]:
            next_actions_list = ollama_response.get("next_actions", [])
            # We must convert next_actions to a list of dicts for storage, if it's not already.
            # This is a robust check to ensure consistency.
            if next_actions_list and isinstance(next_actions_list[0], str):
                next_actions_list = [{"name": action.strip(), "priority": "low"} for action in next_actions_list]

        # Save processed content to the content database
        self.content_db_manager.add_content(
            idea_id, project_type, title, generated_content, category_tags_list, next_actions_list, next_reading_list
        )

        # Update the status of the idea in the scratchpad
        self.scratchpad_agent.update_status(idea_id, "processed")
        self.log_manager.add_log_entry(idea_id, "Successfully processed and awaiting review.")
        print(f"[{datetime.now().isoformat()}] Successfully processed idea: {idea_id}")
        return idea_id

    def get_processor_status(self) -> Dict:
        """Returns the current status of the processor dashboard."""
        pending_ideas = self.scratchpad_agent.get_pending_ideas()
        return {
            "status": "Ready",
            "pending_ideas_count": len(pending_ideas),
            "next_run_in_minutes": "Scheduled by Windows Task Scheduler"
        }
    
    def _validate_ollama_response(self, response: Dict, project_type: str) -> bool:
        """
        Validates the generated content from Ollama against minimum criteria.
        """
        # Debugging: Log the received JSON before validation
        if settings.is_debug_mode:
            print(f"[{datetime.now().isoformat()}] Validating response for project type: '{project_type}'")
            print(f"[{datetime.now().isoformat()}] Next Actions JSON received: {response.get('next_actions', 'N/A')}")
            print(f"[{datetime.now().isoformat()}] Next Reading JSON received: {response.get('next_reading', 'N/A')}")

        # Minimum content length check
        min_content_length_map = {
            "research": 1500, # Assuming roughly 3000 words, so we'll check for at least 1500 characters
            "build": 500,     # for 'build' project type, around 1000 words
            "article": 1000   # for 'article' project type, around 2000 words
        }

        min_content_length = min_content_length_map.get(project_type, 500)
        content = response.get('content', '')
        if len(content) < min_content_length:
            if settings.is_debug_mode:
                print(f"[{datetime.now().isoformat()}] Validation failed for idea {response.get('id')}: Content length is too short ({len(content)} characters). Minimum length required is {min_content_length}.")
            return False

        # Next actions validation based on project type
        if project_type in ["build", "research"]:
            next_actions = response.get('next_actions', [])
            if not isinstance(next_actions, list) or len(next_actions) < 1:
                if settings.is_debug_mode:
                    print(f"[{datetime.now().isoformat()}] Validation failed for idea {response.get('id')}: 'next_actions' is not a valid list or is empty.")
                return False

            for action in next_actions:
                if not isinstance(action, dict) or 'name' not in action or len(action.get('name', '')) < 20:
                    if settings.is_debug_mode:
                        print(f"[{datetime.now().isoformat()}] Validation failed for '{project_type}' type in idea {response.get('id')}: 'next_action' item is not a valid dictionary or name is too short.")
                    return False
        
        # Next reading validation for research and article types
        if project_type in ["article", "research"]:
            next_reading = response.get('next_reading', [])
            if not isinstance(next_reading, list) or len(next_reading) < 1:
                if settings.is_debug_mode:
                    print(f"[{datetime.now().isoformat()}] Validation failed for '{project_type}' type in idea {response.get('id')}: 'next_reading' is not a valid list or is empty.")
                return False
            for item in next_reading:
                if not isinstance(item, str) or len(item.strip()) < 20:
                    if settings.is_debug_mode:
                         print(f"[{datetime.now().isoformat()}] Validation failed for '{project_type}' type in idea {response.get('id')}: 'next_reading' item is not a valid string or is too short.")
                    return False

        return True