from fastapi import APIRouter, HTTPException
from db.schemas import IdeaCreate, Idea, RejectionPayload, Content, ProcessorLog
from agents.scratchpad_agent import ScratchpadAgent
from agents.processor_agent import ProcessorAgent
from agents.reviewer_agent import ReviewerAgent
from typing import List
from datetime import datetime

# Create an API router for all our endpoints
api_router = APIRouter()
# Initialize the Agents
scratchpad_agent = ScratchpadAgent()
processor_agent = ProcessorAgent()
reviewer_agent = ReviewerAgent()


@api_router.post("/scratchpad/add", response_model=Idea)
async def add_idea(idea: IdeaCreate):
    """
    Adds a new idea to the scratchpad queue.
    """
    idea_id = scratchpad_agent.add_new_idea(idea.idea_text, idea.context_urls)
    if not idea_id:
        raise HTTPException(status_code=500, detail="Failed to add idea to scratchpad.")
    
    # Retrieve and return the full idea object to confirm success
    idea_data = scratchpad_agent.get_idea(idea_id)
    if not idea_data:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly added idea.")
        
    return Idea(**idea_data)

@api_router.get("/scratchpad/all", response_model=List[Idea])
async def get_all_ideas():
    """
    Retrieves all ideas from the scratchpad queue.
    """
    ideas_data = scratchpad_agent.get_all_ideas()
    return [Idea(**idea) for idea in ideas_data]

@api_router.delete("/scratchpad/delete/{idea_id}")
async def delete_idea(idea_id: str):
    """
    Deletes an idea from the scratchpad by its unique ID.
    """
    if scratchpad_agent.delete_idea_by_id(idea_id):
        return {"message": f"Idea with ID '{idea_id}' deleted successfully."}
    raise HTTPException(status_code=404, detail=f"Idea with ID '{idea_id}' not found.")

@api_router.get("/processor/status")
async def get_processor_status():
    """
    Retrieves the current status of the Idea Processor dashboard.
    """
    return processor_agent.get_processor_status()


@api_router.get("/processor/logs", response_model=List[ProcessorLog])
async def get_processor_logs():
    """
    Retrieves the latest processor log entries.
    """
    logs = processor_agent.log_manager.get_all_logs()
    return [ProcessorLog(**log) for log in logs]


@api_router.get("/reviewer/all", response_model=List[Content])
async def get_all_content_for_review():
    """
    Retrieves all processed content awaiting review.
    """
    content_data = reviewer_agent.get_all_content_for_review()
    return [Content(**item) for item in content_data]

@api_router.post("/reviewer/approve/{content_id}")
async def approve_content(content_id: str):
    """
    Approves a content item, posts to Notion, and purges it from the content DB.
    """
    if reviewer_agent.approve_and_post_to_notion(content_id):
        return {"message": f"Content '{content_id}' approved and purged successfully."}
    raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found.")

@api_router.post("/reviewer/reject/{content_id}")
async def reject_content(content_id: str, payload: RejectionPayload):
    """
    Rejects a content item, re-queues it with corrections, and purges it from the content DB.
    """
    if reviewer_agent.reject_and_requeue(content_id, payload.correction_text, payload.correction_urls):
        return {"message": f"Content '{content_id}' rejected and re-queued with corrections."}
    raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found.")
