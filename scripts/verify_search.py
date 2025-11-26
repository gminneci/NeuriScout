import requests
import json

BASE_URL = "http://localhost:8000"

def test_filters():
    print("Testing /filters...")
    try:
        response = requests.get(f"{BASE_URL}/filters")
        if response.status_code == 200:
            filters = response.json()
            print(f"Filters keys: {filters.keys()}")
            print(f"Authors count: {len(filters.get('authors', []))}")
            print(f"Affiliations count: {len(filters.get('affiliations', []))}")
        else:
            print(f"Error /filters: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception /filters: {e}")

def test_search():
    print("\nTesting /search...")
    try:
        payload = {
            "query": "language models",
            "limit": 5
        }
        response = requests.post(f"{BASE_URL}/search", json=payload)
        if response.status_code == 200:
            results = response.json()
            print(f"Search results count: {len(results)}")
            if len(results) > 0:
                print(f"First result title: {results[0].get('title')}")
        else:
            print(f"Error /search: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception /search: {e}")

if __name__ == "__main__":
    test_filters()
    test_search()
