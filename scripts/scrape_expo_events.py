"""
Scrape expo events from NeurIPS 2025 virtual schedule
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

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
        if abstract_div:
            abstract = abstract_div.get_text(strip=True)
        
        # Extract session/location info
        session_info = soup.find('div', class_=lambda x: x and 'session' in str(x).lower())
        location = ""
        if session_info:
            location = session_info.get_text(strip=True)
        
        # Extract time info
        time_div = soup.find('div', class_=lambda x: x and ('time' in str(x).lower() or 'date' in str(x).lower()))
        start_time = ""
        if time_div:
            start_time = time_div.get_text(strip=True)
        
        # Extract authors/presenters
        authors_div = soup.find('div', class_=lambda x: x and ('author' in str(x).lower() or 'presenter' in str(x).lower()))
        authors = ""
        if authors_div:
            authors = authors_div.get_text(strip=True)
        
        return {
            'abstract': abstract,
            'location': location,
            'start_time': start_time,
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
