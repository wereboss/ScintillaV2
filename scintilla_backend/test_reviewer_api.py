import requests
import json
import time

# Base URL for our API
BASE_URL = "http://localhost:8000"

def add_test_idea(idea_text: str, context_urls: str) -> str:
    """Helper function to add an idea for testing."""
    data = {"idea_text": idea_text, "context_urls": context_urls}
    response = requests.post(f"{BASE_URL}/scratchpad/add", json=data)
    if response.status_code == 200:
        return response.json()['id']
    return None

def run_processor():
    """Helper function to trigger the processor script manually."""
    # Note: This simulates a scheduled task. You need to run this manually in a separate terminal.
    print("\n--- Manually running the processor script... ---")
    # This assumes `process_ideas.py` is in the same directory.
    # In a real test, you might use subprocess.run()
    # For now, this is a print-only helper to remind the user.
    print("Please run `python process_ideas.py` in a separate terminal.")
    input("Press Enter after the script has finished...")


def test_get_all_content():
    """Test retrieving all content for review."""
    print("\n--- Testing GET /reviewer/all ---")
    response = requests.get(f"{BASE_URL}/reviewer/all")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 200 and response.json():
        return response.json()[0]['id']
    return None

def test_approve_content(content_id: str):
    """Test approving a content item."""
    print(f"\n--- Testing POST /reviewer/approve/{content_id} ---")
    response = requests.post(f"{BASE_URL}/reviewer/approve/{content_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_reject_content(content_id: str):
    """Test rejecting a content item with corrections."""
    print(f"\n--- Testing POST /reviewer/reject/{content_id} ---")
    payload = {
        "correction_text": "The content needs to be more focused on technical details.",
        "correction_urls": "https://new-resource.com/tech-details"
    }
    response = requests.post(f"{BASE_URL}/reviewer/reject/{content_id}", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Give the server a moment to start
    print("Attempting to connect to the backend...")
    time.sleep(2)
    
    # 1. Add a test idea and process it
    idea_id = add_test_idea("Develop a new backend service for a mobile app. This is a build project.", "https://example.com/api")
    if not idea_id:
        print("Failed to add idea. Exiting.")
    
    run_processor()
    
    # 2. Get the processed content ID
    content_id = test_get_all_content()
    if not content_id:
        print("No processed content found. Exiting.")
    
    # 3. Test rejecting the content and checking the queue
    test_reject_content(content_id)
    print("\n--- Verifying the rejected idea is back in the scratchpad... ---")
    get_all_ideas_response = requests.get(f"{BASE_URL}/scratchpad/all")
    print(f"Scratchpad content: {json.dumps(get_all_ideas_response.json(), indent=2)}")
    
    # 4. Cleanup and test the approve flow
    add_test_idea("Write an article about the future of AI in research.", "https://research-paper.com")
    run_processor()
    content_id_to_approve = test_get_all_content()
    if content_id_to_approve:
        test_approve_content(content_id_to_approve)
        print("\n--- Verifying the content was purged after approval... ---")
        test_get_all_content()