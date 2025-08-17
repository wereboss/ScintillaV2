import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import api_router
from config.settings import settings
from db.db_manager import DatabaseManager
from contextlib import asynccontextmanager
import json
from pathlib import Path
from datetime import datetime

# Define the lifespan event handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    """
    print(f"[{datetime.now().isoformat()}] Application startup event triggered.")
    # Initialize the scratchpad database
    scratchpad_db = DatabaseManager(settings.scratchpad_db_path)
    scratchpad_db.create_tables()

    # Initialize the content database
    content_db = DatabaseManager(settings.content_db_path, schema_name="content")
    content_db.create_tables()
    
    # Initialize the prompts file if it doesn't exist
    prompts_path = Path("config/prompts.json")
    prompts_content = {
        "research": {
            "full_prompt": "You are a world-class researcher. Your task is to generate a detailed research document based on the following idea and context, formatted as a JSON object. The research document should be approximately 3000 words. The response must be a single JSON object with the following structure:\n{{\n  \"title\": \"A concise title for the research project\",\n  \"content\": \"The full research document, including a detailed introduction, clearly-marked chapters, and a conclusion. Each chapter must end with a relevant case study.\",\n  \"category_tags\": [\"Tag1\", \"Tag2\", \"Tag3\"],\n  \"next_actions\": [{\"name\": \"A descriptive string for a research task\", \"priority\": \"high\"}, {\"name\": \"Another task for future research\", \"priority\": \"medium\"}, {\"name\": \"A final related topic to explore\", \"priority\": \"low\"}],\n  \"next_reading\": [\"A relevant academic paper\", \"A link to a detailed blog post\", \"A book recommendation\"]\n}}\n\nIdea: {idea_text}\n\nContext URLs: {context_urls}\n"
        },
        "build": {
            "full_prompt": "You are a senior project manager. Your task is to create a top-level approach, infrastructure plan, and resource list for a build project, formatted as a JSON object. The plan should be approximately 1000 words. \n\nIdea: {idea_text}\n\nContext URLs: {context_urls}\n\nThe response must be a single JSON object with the following structure:\n{{\n  \"title\": \"A concise title for the build project plan\",\n  \"content\": \"The full 1000-word build plan, outlining the approach, infrastructure, and resources.\",\n  \"category_tags\": [\"Tag1\", \"Tag2\", \"Tag3\"],\n  \"next_actions\": [{{\"name\": \"A descriptive string for the priority resource\", \"priority\": \"high\"}}, {{\"name\": \"A concise description of the prep work\", \"priority\": \"medium\"}}, {{\"name\": \"Another description of the prep work\", \"priority\": \"low\"}}]\n}}\n"
        },
        "article": {
            "full_prompt": "You are a professional content creator and master storyteller. Your task is to write a captivating story-like article based on the following idea and context, formatted as a JSON object. The article should be approximately 2000 words with a clear beginning, middle, and end. The beginning should inspire curiosity and possibilities. The middle should elaborate on the topic. The end should bring the overall theme to a satisfying conclusion, linking it back to the beginning. If the topic could have any real-life case studies, include that as well in the next_reading section of the JSON. \n\nIdea: {idea_text}\n\nContext URLs: {context_urls}\n\nThe response must be a single JSON object, which must mandatorily include next_reading array, with the following structure:\n{{\n  \"title\": \"A catchy title for the article\",\n  \"content\": \"The full 2000-word article with a clear beginning, middle, and end.\",\n  \"category_tags\": [\"Tag1\", \"Tag2\", \"Tag3\"],\n  \"next_reading\": [\"A concise suggestion for additional media or a related resource\", \"A link to supporting information or another article\", \"Ideas on relevant real-life case studies\"]\n}}\n"
        }
    }
    
    if not prompts_path.exists():
        prompts_path.parent.mkdir(parents=True, exist_ok=True)
        with open(prompts_path, "w") as f:
            json.dump(prompts_content, f, indent=4)
        print(f"[{datetime.now().isoformat()}] Created initial prompts file at {prompts_path}")

    yield
    print(f"[{datetime.now().isoformat()}] Application shutdown event triggered.")

# Initialize the FastAPI application with the lifespan handler
app = FastAPI(title="Scintilla Backend API", lifespan=lifespan)

# Configure CORS middleware to allow requests from the front-end
origins = [
    "*", # Allow all origins for development. In production, this should be the front-end URL.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router with all our endpoints
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)