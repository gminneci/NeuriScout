import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
from sentence_transformers import SentenceTransformer
import ast

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "papercopilot_neurips2025_merged_openreview.csv")
EVENTS_CSV_PATH = os.path.join(BASE_DIR, "data", "neurips_2025_enriched_events.csv")
EXPO_CSV_PATH = os.path.join(BASE_DIR, "data", "neurips_2025_expo_events.csv")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "chroma_db"))
COLLECTION_NAME = "neurips_papers"
MODEL_NAME = "all-MiniLM-L6-v2"

def clean_list_string(s):
    if pd.isna(s):
        return []
    try:
        # Some fields might be semicolon separated or actual lists
        if ';' in str(s):
            return [x.strip() for x in str(s).split(';')]
        return [x.strip() for x in str(s).split(',')]
    except:
        return []

def main():
    print(f"Loading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    if os.path.exists(EVENTS_CSV_PATH):
        print(f"Loading events from {EVENTS_CSV_PATH}...")
        df_events = pd.read_csv(EVENTS_CSV_PATH)
        print(f"Loaded {len(df_events)} events.")
        df = pd.concat([df, df_events], ignore_index=True)
    
    if os.path.exists(EXPO_CSV_PATH):
        print(f"Loading expo events from {EXPO_CSV_PATH}...")
        df_expo = pd.read_csv(EXPO_CSV_PATH)
        print(f"Loaded {len(df_expo)} expo events.")
        df = pd.concat([df, df_expo], ignore_index=True)

    # Filter: keep only San Diego events (exclude Mexico City)
    before_count = len(df)
    # Drop any row whose session mentions Mexico or whose start date is 2025-12-01 (Mexico day)
    df = df[~df.get('neurips_session', '').astype(str).str.contains('mexico', case=False, na=False)]
    if 'neurips_starttime' in df.columns:
        df = df[~df['neurips_starttime'].astype(str).str.startswith('2025-12-01')]
    after_count = len(df)
    removed = before_count - after_count
    print(f"Filtered out {removed} Mexico City rows; {after_count} remain (San Diego only).")
    
    # Fill missing abstracts with empty string to include events without abstracts
    df['neurips_abstract'] = df['neurips_abstract'].fillna("")
    
    # Filter out rows without titles
    df = df.dropna(subset=['title'])
    
    # Aggregate duplicate papers (same title)
    # We want to collect all sessions and affiliations for the same paper
    print("Aggregating duplicate papers...")
    aggregation_functions = {
        'authors': 'first',
        'neurips_abstract': 'first',
        'neurips_paper_url': 'first',
        'neurips_virtualsite_url': 'first',
        'openreview_urls': 'first',
        'neurips_starttime': 'first',
        'neurips_event_type': 'first',
        'affiliation': lambda x: '; '.join(sorted(set([i.strip() for s in x.dropna() for i in str(s).split(';') if i.strip()]))),
        'neurips_session': lambda x: '; '.join(sorted(set([i.strip() for s in x.dropna() for i in str(s).split(';') if i.strip()])))
    }
    # Keep other columns if needed, but we mainly use these.
    # We need to make sure we don't lose data.
    
    df_grouped = df.groupby('title', as_index=False).agg(aggregation_functions)
    print(f"Found {len(df_grouped)} unique papers after aggregation (from {len(df)} rows).")
    df = df_grouped


    # Initialize ChromaDB
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Use SentenceTransformer for embeddings
    # We can use Chroma's built-in or custom. Let's use custom to be sure of the model.
    # Actually, Chroma's default is all-MiniLM-L6-v2, but let's be explicit.
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection {COLLECTION_NAME}")
    except Exception:
        pass
    
    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)

    # Prepare data for insertion
    documents = []
    metadatas = []
    ids = []

    print("Processing papers...")
    for idx, row in df.iterrows():
        # Create a rich text representation for embedding
        # Title + Abstract + Event Type is usually best
        event_type = str(row['neurips_event_type']) if not pd.isna(row['neurips_event_type']) else ""
        
        # Use title as abstract if abstract is missing
        abstract_text = row['neurips_abstract']
        if not abstract_text:
            abstract_text = row['title']
            
        text_to_embed = f"Title: {row['title']}\nType: {event_type}\nAbstract: {abstract_text}"
        
        # Derive day and ampm separately from start time if available
        start_time_val = str(row['neurips_starttime']) if 'neurips_starttime' in row else ""
        day = ""
        ampm = ""
        try:
            if start_time_val and start_time_val != 'nan' and 'T' in start_time_val:
                date_part, time_part = start_time_val.split('T', 1)
                hour_str = time_part.split(':')[0]
                hour = int(hour_str) if hour_str.isdigit() else 0
                day = date_part  # Store as YYYY-MM-DD
                ampm = 'AM' if hour < 12 else 'PM'
        except Exception:
            day = ""
            ampm = ""

        # Prepare metadata
        # Chroma metadata must be int, float, str, or bool. No lists.
        # We'll join lists into strings.
        
        meta = {
            "title": str(row['title']),
            "authors": str(row['authors']),
            "affiliation": str(row['affiliation']),
            "session": str(row['neurips_session']) if not pd.isna(row['neurips_session']) else "",
            "event_type": event_type,
            "year": 2025,
            "paper_url": str(row['neurips_paper_url']) if not pd.isna(row['neurips_paper_url']) else "",
            "neurips_virtualsite_url": str(row['neurips_virtualsite_url']) if not pd.isna(row['neurips_virtualsite_url']) else "",
            "openreview_url": str(row['openreview_urls']) if not pd.isna(row['openreview_urls']) else "",
            "start_time": str(row['neurips_starttime']) if not pd.isna(row['neurips_starttime']) else "",
            "day": day,
            "ampm": ampm
        }
        
        documents.append(text_to_embed)
        metadatas.append(meta)
        ids.append(str(idx))

    # Insert in batches to avoid hitting limits
    BATCH_SIZE = 100
    total_batches = len(documents) // BATCH_SIZE + 1
    
    print(f"Inserting {len(documents)} documents in {total_batches} batches...")
    
    for i in range(0, len(documents), BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, len(documents))
        print(f"Batch {i // BATCH_SIZE + 1}/{total_batches}")
        
        collection.add(
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
            ids=ids[i:batch_end]
        )

    print("Ingestion complete!")

if __name__ == "__main__":
    main()
