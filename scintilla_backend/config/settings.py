from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings for Scintilla.
    These can be loaded from environment variables or a .env file.
    """
    # Database paths
    scratchpad_db_path: str = "scintilla_scratchpad.db"
    content_db_path: str = "scintilla_content.db"
    processor_log_db_path: str = "scintilla_processor_log.db"

    # Notion integration
    notion_api_key: Optional[str] = os.getenv("NOTION_API_KEY")
    notion_database_id: Optional[str] = os.getenv("NOTION_DATABASE_ID")

    # Ollama model
    ollama_model_name: str = "llama3-groq-tool-use"
    
    # Ollama API URL
    ollama_base_url: str = "http://localhost:11434"

    # Processor scheduling (placeholders for now)
    processing_batch_size: int = 5
    processing_interval_minutes: int = 3
    processing_batch_max_rerun: int = 3

    # Debugging flag
    is_debug_mode: bool = True
    
    class Config:
        env_file = '.env'
        
settings = Settings()