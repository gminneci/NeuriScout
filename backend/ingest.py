import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
from sentence_transformers import SentenceTransformer
import ast

# Configuration
CSV_PATH = "../data/papercopilot_neurips2025_merged_openreview.csv"
CHROMA_PATH = "../chroma_db"
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
    
    # Filter out rows without abstracts or titles
    # Filter out rows without abstracts or titles
    df = df.dropna(subset=['neurips_abstract', 'title'])
    
    # Aggregate duplicate papers (same title)
    # We want to collect all sessions and affiliations for the same paper
    print("Aggregating duplicate papers...")
    aggregation_functions = {
        'authors': 'first',
        'neurips_abstract': 'first',
        'neurips_paper_url': 'first',
        'openreview_urls': 'first',
        'neurips_starttime': 'first',
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
        # Title + Abstract is usually best
        text_to_embed = f"Title: {row['title']}\nAbstract: {row['neurips_abstract']}"
        
        # Prepare metadata
        # Chroma metadata must be int, float, str, or bool. No lists.
        # We'll join lists into strings.
        
        meta = {
            "title": str(row['title']),
            "authors": str(row['authors']),
            "affiliation": str(row['affiliation']),
            "session": str(row['neurips_session']) if not pd.isna(row['neurips_session']) else "",
            "year": 2025,
            "paper_url": str(row['neurips_paper_url']) if not pd.isna(row['neurips_paper_url']) else "",
            "openreview_url": str(row['openreview_urls']) if not pd.isna(row['openreview_urls']) else "",
            "start_time": str(row['neurips_starttime']) if not pd.isna(row['neurips_starttime']) else ""
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
