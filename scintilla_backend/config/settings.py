from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings for Scintilla.
    These can be loaded from environment variables or a .env file.
    """
    # Database paths
    scratchpad_db_path: str = "scintilla_scratchpad.db"
    content_db_path: str = "scintilla_content.db"

    # Notion integration (optional for now)
    notion_api_key: Optional[str] = None
    notion_database_id: Optional[str] = None

    # Ollama model
    ollama_model_name: str = "llama3-groq-tool-use"
    
    # Ollama API URL
    ollama_base_url: str = "http://localhost:11434"

    # Processor scheduling (placeholders for now)
    processing_batch_size: int = 5
    processing_interval_minutes: int = 30

    # Debugging flag
    is_debug_mode: bool = True
    
    class Config:
        env_file = '.env'
        
settings = Settings()