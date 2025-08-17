# This file remains unchanged from the previous version, but is included for completeness.
import requests
import json
import time

# Base URL for our API
BASE_URL = "http://localhost:8000"

def test_add_idea():
    """Test adding a new idea to the scratchpad."""
    print("--- Testing POST /scratchpad/add ---")
    data = {
        "idea_text": "Develop a new front-end for a website. This is a build project.",
        "context_urls": "https://example.com/api, https://docs.service.com"
    }
    response = requests.post(f"{BASE_URL}/scratchpad/add", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json()['id']
    return None

def test_get_all_ideas():
    """Test retrieving all ideas from the scratchpad."""
    print("\n--- Testing GET /scratchpad/all ---")
    response = requests.get(f"{BASE_URL}/scratchpad/all")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return [idea['id'] for idea in response.json()]
    return []
    
def test_delete_idea(idea_id):
    """Test deleting a specific idea by ID."""
    print(f"\n--- Testing DELETE /scratchpad/delete/{idea_id} ---")
    response = requests.delete(f"{BASE_URL}/scratchpad/delete/{idea_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_processor_status():
    """Test retrieving the processor status."""
    print("\n--- Testing GET /processor/status ---")
    response = requests.get(f"{BASE_URL}/processor/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    # Give the server a moment to start
    print("Attempting to connect to the backend...")
    time.sleep(2)
    
    # Test adding two ideas
    new_idea_id1 = test_add_idea()
    test_add_idea()

    # Test the processor status endpoint
    test_get_processor_status()

    # Test retrieving all ideas
    test_get_all_ideas()

    # Test deleting one of the ideas
    if new_idea_id1:
        test_delete_idea(new_idea_id1)
        test_get_all_ideas()

    # You can now manually run the `process_ideas.py` script to see it process the remaining idea.
    print("\nTo continue testing, run `python process_ideas.py` in your terminal.")

