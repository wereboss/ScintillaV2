import requests
import json
import time

# Base URL for our API
BASE_URL = "http://localhost:8000"

def add_test_idea(idea_text: str, context_urls: str) -> str:
    """Helper function to add an idea for testing."""
    data = {"idea_text": idea_text, "context_urls": context_urls}
    response = requests.post(f"{BASE_URL}/scratchpad/add", json=data)
    response.raise_for_status()
    return response.json()['id']

def get_processed_content_id() -> str:
    """Helper function to retrieve a processed content item."""
    response = requests.get(f"{BASE_URL}/reviewer/all")
    response.raise_for_status()
    content_list = response.json()
    if content_list:
        return content_list[0]['id']
    return None

def get_scratchpad_ideas() -> list:
    """Helper function to get all ideas from the scratchpad."""
    response = requests.get(f"{BASE_URL}/scratchpad/all")
    response.raise_for_status()
    return response.json()

def test_ollama_build_pipeline():
    """Tests the full pipeline for a 'build' project type with Ollama integration."""
    
    print("--- STEP 1: Adding a new 'build' idea to the scratchpad ---")
    initial_idea_text = "Create a robust backend for a real-time multiplayer game."
    initial_context_urls = "https://gamedev.com/backend-intro"
    try:
        initial_idea_id = add_test_idea(initial_idea_text, initial_context_urls)
        print(f"Added idea with ID: {initial_idea_id}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to add initial idea. Is the backend server running? Error: {e}")
        return

    print("\n--- STEP 2: Manually run the processor script `process_ideas.py` ---")
    print("Please run `python process_ideas.py` in a separate terminal now.")
    input("Press Enter after the script has finished...")
    
    print("\n--- STEP 3: Check for processed content in the reviewer queue ---")
    try:
        processed_content_id = get_processed_content_id()
        if processed_content_id:
            print(f"Found processed content with ID: {processed_content_id}")
            print("\nProcessor pipeline for 'build' type succeeded.")
        else:
            print("No processed content found. The processor might have failed or the idea was not processed.")
            return
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve content. Is the backend server running? Error: {e}")
        return

    print("\n--- STEP 4: Simulating a rejection with correction notes ---")
    rejection_payload = {
        "correction_text": "The infrastructure plan needs to be more specific for a cloud-based solution.",
        "correction_urls": "https://aws.amazon.com/solutions"
    }
    try:
        response = requests.post(f"{BASE_URL}/reviewer/reject/{processed_content_id}", json=rejection_payload)
        response.raise_for_status()
        print(response.json()['message'])
    except requests.exceptions.RequestException as e:
        print(f"Failed to reject content. Error: {e}")
        return

    print("\n--- STEP 5: Verifying the rejected idea is back in the scratchpad with corrections ---")
    scratchpad_ideas = get_scratchpad_ideas()
    found_requeued = False
    for idea in scratchpad_ideas:
        if "The infrastructure plan needs to be more specific" in idea['idea_text']:
            print("Found re-queued idea in scratchpad with corrections.")
            found_requeued = True
            break
    if not found_requeued:
        print("Re-queued idea not found in scratchpad.")

    print("\n--- STEP 6: Manually run the processor again for the re-queued idea ---")
    print("Please run `python process_ideas.py` in a separate terminal again.")
    input("Press Enter after the script has finished...")

    print("\n--- STEP 7: Check for the reprocessed content ---")
    try:
        reprocessed_content_id = get_processed_content_id()
        if reprocessed_content_id and reprocessed_content_id != processed_content_id:
            print(f"Successfully re-processed the idea. New content ID: {reprocessed_content_id}")
            print("Full processor pipeline with rejection and reprocessing succeeded!")
        else:
            print("Failed to find new processed content. Reprocessing may have failed.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve reprocessed content. Error: {e}")

if __name__ == "__main__":
    # Give the server a moment to start
    print("Attempting to connect to the backend...")
    time.sleep(2)
    
    test_ollama_build_pipeline()