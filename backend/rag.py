import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import httpx
from bs4 import BeautifulSoup
import io
import pypdf
import os
from pathlib import Path

# Configuration
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", str(Path(__file__).parent.parent / "chroma_db"))
COLLECTION_NAME = "neurips_papers"
MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize ChromaDB Client (Global)
client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
collection = client.get_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)

def search_papers(query: str, n_results: int = 10, filters: dict = None, threshold: float = None):
    """
    Search for papers using semantic search and metadata filters.
    """
    where_clause = {}
    if filters:
        # ChromaDB 'where' clause supports $and, $or, etc.
        # Simple implementation: exact match for provided keys
        # Note: Ingested metadata strings might need partial match, but Chroma only supports exact or $in
        # For this MVP, we'll assume exact match or handle filtering post-retrieval if needed.
        # But wait, our metadata are strings like "MIT; Harvard". Exact match won't work well for "MIT".
        # Chroma doesn't support "contains" for strings in the `where` clause natively in all versions.
        # We might need to fetch more results and filter in Python if complex filtering is needed.
        # Let's try to use basic filtering if provided.
        pass
        
    # We will fetch more results and filter in python for "contains" logic if needed, 
    # but for now let's just do semantic search.
    
    # Handle wildcard or empty query (Metadata filtering only)
    if not query or query.strip() == "*":
        # Fetch a large number of results (or all) to filter in Python
        # Chroma's .get() supports limit. We'll set a high limit.
        # We DO NOT pass 'where' here because we need "contains" logic which Chroma doesn't support well for strings.
        results = collection.get(
            limit=2000 # Fetch enough to filter. 
        )
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'])):
                # Apply filters manually
                metadata = results['metadatas'][i]
                
                # Check Affiliation
                if filters and filters.get('affiliation'):
                    if filters['affiliation'].lower() not in metadata['affiliation'].lower():
                        continue
                
                # Check Author
                if filters and filters.get('author'):
                    if filters['author'].lower() not in metadata['authors'].lower():
                        continue
                        
                # Check Session
                if filters and filters.get('session'):
                    if filters['session'].lower() not in metadata['session'].lower():
                        continue
                
                formatted_results.append({
                    "id": results['ids'][i],
                    "title": metadata['title'],
                    "abstract": results['documents'][i].split("Abstract: ")[1] if "Abstract: " in results['documents'][i] else "",
                    "authors": metadata['authors'],
                    "affiliation": metadata['affiliation'],
                    "session": metadata['session'],
                    "paper_url": metadata['paper_url'],
                    "openreview_url": metadata['openreview_url'],
                    "distance": 0.0
                })
        
        # Apply similarity threshold if provided (distance lower is more similar)
        if threshold is not None:
            formatted_results = [r for r in formatted_results if r.get('distance', 0.0) <= threshold]
        
        return formatted_results[:n_results]

    # Semantic Search
    # For semantic search, we also want "contains" logic for filters.
    # Chroma's `where` is exact match.
    # So we should NOT pass filters to Chroma, but filter in Python after fetching.
    results = collection.query(
        query_texts=[query],
        n_results=n_results * 5, # Fetch more to allow for filtering
    )
    
    # Format results
    formatted_results = []
    if results['ids']:
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            
            # Apply filters manually
            if filters and filters.get('affiliation'):
                if filters['affiliation'].lower() not in metadata['affiliation'].lower():
                    continue
            if filters and filters.get('author'):
                if filters['author'].lower() not in metadata['authors'].lower():
                    continue
            if filters and filters.get('session'):
                if filters['session'].lower() not in metadata['session'].lower():
                    continue
            
            distance = results['distances'][0][i] if results['distances'] else 0.0
            
            # Apply similarity threshold if provided
            if threshold is not None and distance > threshold:
                continue

            formatted_results.append({
                "id": results['ids'][0][i],
                "title": metadata['title'],
                "abstract": results['documents'][0][i].split("Abstract: ")[1] if "Abstract: " in results['documents'][0][i] else "",
                "authors": metadata['authors'],
                "affiliation": metadata['affiliation'],
                "session": metadata['session'],
                "paper_url": metadata['paper_url'],
                "openreview_url": metadata['openreview_url'],
                "distance": distance
            })
            
    return formatted_results[:n_results]

import asyncio

async def fetch_paper_text(url: str):
    """
    Fetches the full text of a paper given its URL.
    Tries to find a PDF link and extract text.
    """
    # Basic implementation: 
    # 1. If URL is OpenReview, try to find /pdf link
    # 2. Download PDF
    # 3. Extract text
    
    pdf_url = None
    if "openreview.net" in url:
        # OpenReview usually has /pdf?id=...
        if "/forum?" in url:
            pdf_url = url.replace("/forum?", "/pdf?")
        elif "/pdf?" in url:
            pdf_url = url
            
    if not pdf_url:
        return f"Could not determine PDF URL from {url}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url, follow_redirects=True)
            response.raise_for_status()
            
            # Check if content type is PDF
            if "application/pdf" not in response.headers.get("content-type", ""):
                 return f"URL {url} did not return a PDF."
                 
            f = io.BytesIO(response.content)
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text
    except Exception as e:
        return f"Error fetching paper {url}: {str(e)}"

async def fetch_multiple_papers(urls: list[str]):
    tasks = [fetch_paper_text(url) for url in urls]
    return await asyncio.gather(*tasks)

def answer_question(context: str, question: str, model: str = "openai", api_key: str = None, gemini_model: str = None, openai_model: str = None, system_prompt: str = None):
    """
    Uses an LLM to answer a question about the paper text.
    """
    
    # Default system prompt if not provided
    if not system_prompt:
        system_prompt = "You are a helpful assistant answering questions about research papers. Use the provided paper content to answer the question."
    
    print(system_prompt)

    if model == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
             return "OpenAI API Key not found. Please set OPENAI_API_KEY in backend/.env or provide it in the UI."
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            
            # Truncate text to avoid context limits (naive approach)
            truncated_text = context[:15000] 
            
            # Use the specified model or default to gpt-4o
            model_name = openai_model or 'gpt-4o'
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Papers Content:\n{truncated_text}\n\nQuestion: {question}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    elif model == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            return "Gemini API Key not found. Please set GEMINI_API_KEY in backend/.env or provide it in the UI."
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            
            # Gemini 1.5 Pro has a large context window, so we can be more generous or pass full text
            # But let's still be reasonable.
            truncated_text = context[:30000]
            
            # Use the specified model or default to gemini-1.5-flash
            model_name = gemini_model or 'gemini-1.5-flash'
            gemini_model_obj = genai.GenerativeModel(model_name)
            response = gemini_model_obj.generate_content(
                f"{system_prompt}\n\nPapers Content:\n{truncated_text}\n\nQuestion: {question}"
            )
            return response.text
        except Exception as e:
            return f"Error calling Gemini: {str(e)}"
            
    else:
        return f"Unknown model: {model}"

# Cache for filters
_filters_cache = None

def get_filters():
    global _filters_cache
    if _filters_cache:
        return _filters_cache
        
    import pandas as pd
    try:
        # Read CSV to get unique values
        # CSV is now in the data/ directory
        csv_path = "../data/papercopilot_neurips2025_merged_openreview.csv"
        if not os.path.exists(csv_path):
             # Fallback if running from root
             csv_path = "data/papercopilot_neurips2025_merged_openreview.csv"
             
        df = pd.read_csv(csv_path)
        
        # Helper to split and clean
        def get_unique(col):
            if col not in df.columns: return []
            values = set()
            for x in df[col].dropna():
                # Split by semicolon or comma if multiple values
                # The data seems to use various separators or just strings.
                # Let's just take unique strings for now to be safe, or split if obvious.
                # The ingest script split by comma/semicolon.
                parts = str(x).replace(';', ',').split(',')
                for p in parts:
                    clean = p.strip()
                    if clean:
                        values.add(clean)
            return sorted(list(values))

        _filters_cache = {
            "affiliations": get_unique("affiliation"),
            "authors": get_unique("authors"),
            "sessions": get_unique("neurips_session")
        }
        return _filters_cache
    except Exception as e:
        print(f"Error loading filters: {e}")
        return {"affiliations": [], "authors": [], "sessions": []}
