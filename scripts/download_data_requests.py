import requests
from bs4 import BeautifulSoup
import os

URL = "https://neurips.cc/Downloads/2025"
OUTPUT_DIR = "data"
OUTPUT_FILE = "neurips_2025_schedule.csv"

def download_csv():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": URL,
        "Origin": "https://neurips.cc"
    })
    
    # 1. Get the page to get CSRF token
    print(f"Fetching {URL}...")
    resp = session.get(URL)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf_token:
        print("Could not find CSRF token.")
        return
    
    token = csrf_token["value"]
    print(f"Found CSRF token: {token}")
    
    # 2. Prepare POST data
    # Based on browser inspection: file_format=0 is CSV
    # We want all event types. The form likely has checkboxes.
    # Usually they are named like 'posters', 'tutorials', etc.
    # Let's inspect the form inputs from the soup to be sure.
    
    data = {
        "csrfmiddlewaretoken": token,
        "file_format": "0", # CSV
        # Add other fields found in the form
    }
    
    # Find all checkboxes and set them to 'on' (or their value)
    checkboxes = soup.find_all("input", {"type": "checkbox"})
    for cb in checkboxes:
        name = cb.get("name")
        if name:
            data[name] = "on" # or cb.get("value", "on")
            print(f"Enabling {name}")
            
    # 3. POST to download
    print("Posting download request...")
    post_resp = session.post(URL, data=data, stream=True)
    post_resp.raise_for_status()
    
    # Check if we got a file
    content_type = post_resp.headers.get("Content-Type", "")
    print(f"Response Content-Type: {content_type}")
    
    if "text/csv" in content_type or "application/csv" in content_type or "attachment" in post_resp.headers.get("Content-Disposition", ""):
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(output_path, "wb") as f:
            for chunk in post_resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {output_path}")
    else:
        print("Did not receive a CSV file. Response might be HTML.")
        # print(post_resp.text[:500])

if __name__ == "__main__":
    download_csv()
