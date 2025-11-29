import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
INPUT_CSV = "data/neurips_2025_schedule.csv"
OUTPUT_CSV = "data/neurips_2025_enriched_events.csv"
BASE_URL = "https://neurips.cc"

# Headers for scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def normalize_title(title):
    if not isinstance(title, str):
        return ""
    return re.sub(r'\s+', ' ', title).strip().lower()

def parse_neurips_page(url):
    """
    Scrapes location and time from an event page.
    """
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return "", ""
        
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return "", ""
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        location = ""
        datetime_raw = ""
        
        # Strategy: Look for the time string first
        # It usually contains PST/PDT and a dash
        # It's often in a text node or h5/h6/div
        
        # Find all text elements
        for tag in soup.find_all(["h5", "h6", "div", "p", "span"]):
            txt = tag.get_text(" ", strip=True)
            if not txt:
                continue
            
            # Check for time pattern
            if "PST" in txt or "PDT" in txt:
                if "—" in txt or "-" in txt:
                    # Check length to avoid capturing full page
                    if len(txt) < 100:
                        datetime_raw = txt
                        
                        # Location is often the previous sibling or close by
                        # If it's an h5, the location might be the previous h5
                        prev = tag.find_previous(["h5", "h6"])
                        if prev:
                            loc_txt = prev.get_text(" ", strip=True)
                            if len(loc_txt) < 100 and "Workshop" not in loc_txt and "Tutorial" not in loc_txt:
                                location = loc_txt
                        break
        
        # Fallback for location if not found via sibling
        if not location:
            for tag in soup.find_all("h5"):
                txt = tag.get_text(" ", strip=True)
                if len(txt) < 50 and "Workshop" not in txt and "Tutorial" not in txt and "PST" not in txt:
                    location = txt
                    break

        return location, datetime_raw
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return "", ""

def process_row(row):
    """
    Process a single row from the input dataframe.
    Returns a dictionary with mapped columns.
    """
    # Map columns
    # Input: type, name, virtualsite_url, speakers/authors, abstract
    
    title = row.get("name", "")
    event_type = row.get("type", "")
    url = row.get("virtualsite_url", "")
    authors = row.get("speakers/authors", "")
    abstract = row.get("abstract", "")
    
    # Extract ID
    neurips_id = ""
    if url and isinstance(url, str):
        match = re.search(r'/(\d+)$', url)
        if match:
            neurips_id = match.group(1)
            
    # Scrape time and location
    # Only if url is valid
    location, starttime_raw = parse_neurips_page(url)
    
    iso_starttime = ""
    if starttime_raw:
        try:
            # Example: "Mon 1 Dec 6 a.m. PST — 3 p.m. PST"
            # Remove timezone
            parts = starttime_raw.split("—")[0].split("-")[0].strip()
            parts = parts.replace("PST", "").replace("PDT", "").strip()
            
            # Extract day: "1"
            day_match = re.search(r'\b(\d{1,2})\b', parts)
            day = day_match.group(1) if day_match else ""
            
            # Extract time: "6 a.m." or "6:00 a.m."
            # Regex for time: (\d{1,2})(:(\d{2}))?\s*([ap]\.?m\.?)
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)', parts, re.IGNORECASE)
            
            if day and time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3).lower().replace(".", "")
                
                if ampm == "pm" and hour < 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
                
                iso_starttime = f"2025-12-{int(day):02d}T{hour:02d}:{minute:02d}:00"
            else:
                iso_starttime = starttime_raw # Fallback
                
        except Exception as e:
            # print(f"Date parse error: {e}")
            iso_starttime = starttime_raw

    return {
        "title": title,
        "session_area": event_type, # Use type as area
        "authors": authors,
        "affiliation": "", # Not easily available
        "status": "Accepted",
        "rating": "",
        "avg_rating": "",
        "openreview_urls": "",
        "neurips_urls": url,
        "all_urls": url,
        "openreview_id": "",
        "neurips_id": neurips_id,
        "name": title,
        "norm_title_nj": normalize_title(title),
        "neurips_abstract": abstract,
        "neurips_event_type": event_type,
        "neurips_session": event_type,
        "neurips_location": location,
        "neurips_starttime": iso_starttime,
        "neurips_endtime": "", # Could parse from raw
        "neurips_virtualsite_url": url,
        "neurips_paper_url": url,
        "neurips_decision": "",
        "neurips_poster_position": ""
    }

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Input file {INPUT_CSV} not found.")
        return

    print(f"Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    print(f"Found {len(df)} events.")
    
    # Filter out Posters if we only want non-papers?
    # The user said "incorporate non-paper items".
    # The existing pipeline handles papers (Posters).
    # If we include Posters here, we might duplicate them or overwrite them.
    # The existing `papercopilot` CSV has Posters.
    # So we should probably EXCLUDE "Poster" type from here to avoid duplication/conflicts,
    # OR we merge carefully.
    # Let's exclude "Poster" for now, assuming the other pipeline handles them better (with OpenReview data).
    
    df_filtered = df[df['type'] != 'Poster']
    print(f"Processing {len(df_filtered)} non-poster events...")
    
    enriched_rows = []
    
    # Use ThreadPoolExecutor for faster scraping
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_row = {executor.submit(process_row, row): row for _, row in df_filtered.iterrows()}
        
        count = 0
        total = len(df_filtered)
        
        for future in as_completed(future_to_row):
            try:
                data = future.result()
                enriched_rows.append(data)
                count += 1
                if count % 10 == 0:
                    print(f"Processed {count}/{total}")
            except Exception as exc:
                print(f"Row generated an exception: {exc}")

    # Create DataFrame
    out_df = pd.DataFrame(enriched_rows)
    
    # Save
    print(f"Saving to {OUTPUT_CSV}...")
    out_df.to_csv(OUTPUT_CSV, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
