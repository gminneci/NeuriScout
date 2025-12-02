"""
Scrape expo events from NeurIPS 2025 virtual schedule
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

def parse_neurips_datetime(date_str):
    """Parse NeurIPS date format like 'Tue 2 Dec 8:30 a.m. PST' to ISO format"""
    if not date_str:
        return None, None, None
    
    try:
        # Extract the date part: "Tue 2 Dec" and time part "8:30 a.m."
        # Format: "Tue 2 Dec 8:30 a.m. PST — 9:30 a.m. PST"
        match = re.search(r'(\w+\s+\d+\s+\w+)\s+(\d+):(\d+)\s+(a\.m\.|p\.m\.)', date_str)
        if not match:
            return None, None, None
        
        date_part = match.group(1)  # "Tue 2 Dec"
        hour = int(match.group(2))
        minute = match.group(3)
        ampm = match.group(4)
        
        # Convert to 24-hour format
        if 'p.m.' in ampm and hour != 12:
            hour += 12
        elif 'a.m.' in ampm and hour == 12:
            hour = 0
        
        # Parse date - add year 2025
        date_with_year = f"{date_part} 2025"
        dt = datetime.strptime(date_with_year, "%a %d %b %Y")
        
        # Create full datetime with timezone (PST is -08:00)
        iso_datetime = f"{dt.year}-{dt.month:02d}-{dt.day:02d}T{hour:02d}:{minute}:00-08:00"
        day = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
        ampm_val = "AM" if hour < 12 else "PM"
        
        return iso_datetime, day, ampm_val
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None, None, None

def scrape_event_details(event_id, base_url="https://neurips.cc"):
    """Scrape details for a single event"""
    event_url = f"{base_url}/virtual/2025/{event_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(event_url, headers=headers)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract description/abstract
        abstract = ""
        abstract_div = soup.find('div', class_=lambda x: x and 'abstract' in str(x).lower())
        if not abstract_div:
            abstract_div = soup.find('div', class_=lambda x: x and 'description' in str(x).lower())
        if not abstract_div:
            # Try to find any text content that looks like a description
            content_div = soup.find('div', class_=lambda x: x and 'content' in str(x).lower())
            if content_div:
                abstract = content_div.get_text(strip=True)
        else:
            abstract = abstract_div.get_text(strip=True)
        
        # Extract time/date info - look for datetime elements
        start_time_raw = ""
        location = ""
        
        # Look for date/time text (e.g., "Tue 2 Dec 8:30 a.m. PST")
        date_matches = soup.find_all(string=re.compile(r'\d+\s+Dec.*?[ap]\.m\..*?PST', re.I))
        if date_matches:
            # Get the first match and extract just the relevant part
            full_text = date_matches[0].strip()
            # Extract up to the em dash or take whole thing
            start_time_raw = full_text.split('—')[0].strip() if '—' in full_text else full_text
        
        # Extract location
        location_elem = soup.find(['div', 'span'], class_=lambda x: x and 'location' in str(x).lower())
        if location_elem:
            location = location_elem.get_text(strip=True)
        
        # Extract authors/presenters
        authors = ""
        authors_div = soup.find('div', class_=lambda x: x and ('author' in str(x).lower() or 'presenter' in str(x).lower() or 'speaker' in str(x).lower()))
        if authors_div:
            authors = authors_div.get_text(strip=True)
        
        # Parse the datetime
        iso_time, day, ampm = parse_neurips_datetime(start_time_raw)
        
        return {
            'abstract': abstract,
            'location': location,
            'start_time': iso_time,
            'start_time_raw': start_time_raw,
            'day': day,
            'ampm': ampm,
            'authors': authors,
            'virtualsite_url': event_url
        }
    except Exception as e:
        print(f"Error scraping event {event_id}: {e}")
        return None

def scrape_neurips_expo_events():
    """Scrape expo events from NeurIPS virtual schedule"""
    
    expo_url = "https://neurips.cc/virtual/2025/loc/san-diego/events/expo-2025"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching expo page: {expo_url}")
    response = requests.get(expo_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Got status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all event cards with data attributes
    event_cards = soup.find_all('div', class_='event-card')
    print(f"Found {len(event_cards)} event cards")
    
    events = []
    expo_types = ['Expo Workshop', 'Expo Talk Panel', 'Expo Demonstration']
    
    for card in event_cards:
        event_id = card.get('data-event-id')
        event_title = card.get('data-event-title')
        event_type = card.get('data-event-type')
        
        # Only process expo events
        if not event_type or event_type not in expo_types:
            continue
        
        if not event_id or not event_title:
            continue
        
        print(f"Processing: {event_type} - {event_title[:60]}...")
        
        # Get detailed info
        details = scrape_event_details(event_id)
        time.sleep(0.5)  # Be respectful to the server
        
        event_data = {
            'title': event_title,
            'neurips_event_type': event_type,
            'neurips_id': event_id,
            'neurips_virtualsite_url': f'https://neurips.cc/virtual/2025/{event_id}'
        }
        
        if details:
            event_data.update({
                'neurips_abstract': details.get('abstract', ''),
                'neurips_location': details.get('location', ''),
                'neurips_starttime': details.get('start_time', ''),
                'authors': details.get('authors', ''),
            })
            
            # Add day and ampm for filtering
            if details.get('day'):
                event_data['day'] = details['day']
                event_data['ampm'] = details.get('ampm', '')
        else:
            event_data.update({
                'neurips_abstract': '',
                'neurips_location': '',
                'neurips_starttime': '',
                'authors': '',
            })
        
        # Add default/empty fields to match schema
        event_data.update({
            'session_area': '',
            'affiliation': '',
            'status': '',
            'rating': '',
            'avg_rating': '',
            'openreview_urls': '',
            'neurips_urls': '',
            'all_urls': '',
            'openreview_id': '',
            'name': '',
            'norm_title_nj': '',
            'neurips_session': event_type,
            'neurips_endtime': '',
            'neurips_paper_url': '',
            'neurips_decision': '',
            'neurips_poster_position': ''
        })
        
        events.append(event_data)
    
    return events

def main():
    print("Starting NeurIPS Expo Events Scraper")
    print("=" * 60)
    
    events = scrape_neurips_expo_events()
    
    if events:
        df = pd.DataFrame(events)
        output_path = 'data/neurips_2025_expo_events.csv'
        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved {len(events)} expo events to {output_path}")
        
        # Show breakdown by type
        print("\nEvent breakdown:")
        print(df['neurips_event_type'].value_counts())
    else:
        print("\n⚠ No events extracted.")

if __name__ == "__main__":
    main()
