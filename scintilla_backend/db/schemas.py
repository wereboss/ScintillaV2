from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

# Pydantic schema for an Idea entry in the Scratchpad database
class IdeaBase(BaseModel):
    idea_text: str
    context_urls: str

class IdeaCreate(IdeaBase):
    pass

class Idea(BaseModel):
    id: str
    idea_text: Optional[str] = ""
    context_urls: Optional[str] = ""
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Pydantic schemas for the Content database
class ContentBase(BaseModel):
    idea_id: str
    project_type: str
    title: str
    content: str
    category_tags: List[str]
    next_actions: Optional[List[Dict]] = []
    next_reading: Optional[List[str]] = []

class ContentCreate(ContentBase):
    pass

class Content(ContentBase):
    id: str
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ProcessorLog(BaseModel):
    id: str
    idea_id: str
    message: str
    timestamp: datetime

# Schema for the rejection payload from the frontend
class RejectionPayload(BaseModel):
    correction_text: str
    correction_urls: str
