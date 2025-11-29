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

# Try to get collection, but don't fail if it doesn't exist
try:
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)
except Exception:
    print(f"WARNING: ChromaDB collection '{COLLECTION_NAME}' not found. Run 'python -m backend.ingest' to create it.")
    collection = None

def search_papers(query: str, n_results: int = 10, filters: dict = None, threshold: float = None):
    """
    Search for papers using semantic search and metadata filters.
    """
    if collection is None:
        raise RuntimeError("ChromaDB not initialized. Please run 'python -m backend.ingest' to create the database.")
    
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
        # Fetch a large number of results to filter in Python
        # We DO NOT pass 'where' here because we need "contains" logic which Chroma doesn't support well for strings.
        results = collection.get(
            limit=10000  # High limit to cover all items
        )
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'])):
                # Apply filters manually with OR logic for arrays
                metadata = results['metadatas'][i]
                
                # Check Affiliation (OR logic if list)
                if filters and filters.get('affiliation'):
                    affiliations = filters['affiliation'] if isinstance(filters['affiliation'], list) else [filters['affiliation']]
                    if not any(aff.lower() in metadata['affiliation'].lower() for aff in affiliations):
                        continue
                
                # Check Author (OR logic if list)
                if filters and filters.get('author'):
                    authors = filters['author'] if isinstance(filters['author'], list) else [filters['author']]
                    if not any(auth.lower() in metadata['authors'].lower() for auth in authors):
                        continue
                        
                # Check Session (OR logic if list)
                if filters and filters.get('session'):
                    sessions = filters['session'] if isinstance(filters['session'], list) else [filters['session']]
                    if not any(sess.lower() in metadata['session'].lower() for sess in sessions):
                        continue
                
                # Check Day filter (OR logic if list)
                if filters and filters.get('day'):
                    days = filters['day'] if isinstance(filters['day'], list) else [filters['day']]
                    item_day = metadata.get('day', '')
                    if not any(day == item_day for day in days):
                        continue
                
                # Check AM/PM filter
                if filters and filters.get('ampm'):
                    item_ampm = metadata.get('ampm', '')
                    if item_ampm != filters['ampm']:
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
            
            # Apply filters manually with OR logic for arrays
            if filters and filters.get('affiliation'):
                affiliations = filters['affiliation'] if isinstance(filters['affiliation'], list) else [filters['affiliation']]
                if not any(aff.lower() in metadata['affiliation'].lower() for aff in affiliations):
                    continue
            if filters and filters.get('author'):
                authors = filters['author'] if isinstance(filters['author'], list) else [filters['author']]
                if not any(auth.lower() in metadata['authors'].lower() for auth in authors):
                    continue
            if filters and filters.get('session'):
                sessions = filters['session'] if isinstance(filters['session'], list) else [filters['session']]
                if not any(sess.lower() in metadata['session'].lower() for sess in sessions):
                    continue
            
            # Check Day (OR logic if list) - extract date and time from start_time
            if filters and filters.get('day'):
                days = filters['day'] if isinstance(filters['day'], list) else [filters['day']]
                start_time = metadata.get('start_time', '')
                if start_time and 'T' in start_time:
                    paper_date = start_time.split('T')[0]  # Extract YYYY-MM-DD
                    paper_time = start_time.split('T')[1] if 'T' in start_time else ''
                    paper_hour = int(paper_time.split(':')[0]) if paper_time and ':' in paper_time else 0
                    
                    match_found = False
                    for day in days:
                        # Check if day filter includes AM/PM
                        if ' AM' in day or ' PM' in day:
                            date_part = day.replace(' AM', '').replace(' PM', '')
                            if date_part in paper_date:
                                if ' AM' in day and paper_hour < 12:
                                    match_found = True
                                    break
                                elif ' PM' in day and paper_hour >= 12:
                                    match_found = True
                                    break
                        else:
                            # No AM/PM specified, match any time on that date
                            if day in paper_date:
                                match_found = True
                                break
                    
                    if not match_found:
                        continue
                else:
                    continue  # Skip papers without valid start_time
            
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

# Cache for uploaded Gemini files - key is tuple of (url1, url2, ...) to identify paper set
_gemini_file_cache = {}

async def answer_question_with_urls(paper_urls: list[tuple[str, str]], question: str, model: str = "gemini", api_key: str = None, gemini_model: str = None, system_prompt: str = None, use_cache: bool = True):
    """
    Uses Gemini's native file reading to answer questions about papers from URLs.
    paper_urls: list of (title, url) tuples
    use_cache: if True, reuse previously uploaded files for the same paper set
    """
    if model != "gemini":
        return "URL-based paper reading is only supported with Gemini models."
    
    if not system_prompt:
        system_prompt = "You are a helpful assistant answering questions about research papers. Use the provided paper PDFs to answer the question."
    
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return "Gemini API Key not found. Please use the settings (cog wheel) to add your API key."
    
    try:
        import google.generativeai as genai
        import tempfile
        genai.configure(api_key=key)
        
        # Use the specified model or default to gemini-1.5-flash
        model_name = gemini_model or 'gemini-1.5-flash'
        gemini_model_obj = genai.GenerativeModel(model_name)
        
        # Create cache key from URLs
        cache_key = tuple(url for _, url in paper_urls)
        
        # Check cache
        if use_cache and cache_key in _gemini_file_cache:
            uploaded_files = _gemini_file_cache[cache_key]
            print(f"[DEBUG] Using cached files for {len(uploaded_files)} papers")
            status_messages = [f"✓ Using {len(uploaded_files)} previously uploaded papers"]
        else:
            # Upload PDFs to Gemini
            uploaded_files = []
            status_messages = []
            total = len(paper_urls)
            print(f"[DEBUG] Uploading {total} papers to Gemini...")
            
            async with httpx.AsyncClient() as client:
                for idx, (title, url) in enumerate(paper_urls, 1):
                    # Convert OpenReview forum URL to PDF URL
                    pdf_url = url.replace("/forum?", "/pdf?") if "/forum?" in url else url
                    try:
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # Download PDF
                        response = await client.get(pdf_url, follow_redirects=True)
                        response.raise_for_status()
                        
                        # Save temporarily and upload
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(response.content)
                            tmp_path = tmp.name
                        
                        uploaded_file = genai.upload_file(tmp_path, display_name=title)
                        uploaded_files.append((title, uploaded_file))
                        status_msg = f"[{timestamp}] ✓ Uploaded {idx}/{total}"
                        print(f"[DEBUG] {status_msg}")
                        status_messages.append(status_msg)
                        
                        # Clean up temp file
                        import os
                        os.unlink(tmp_path)
                    except Exception as e:
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        error_msg = f"[{timestamp}] ✗ Failed to upload paper {idx}/{total}"
                        print(f"[DEBUG] {error_msg}: {str(e)}")
                        status_messages.append(error_msg)
            
            if not uploaded_files:
                return "Failed to upload any papers to Gemini."
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[DEBUG] Successfully uploaded {len(uploaded_files)} papers")
            status_messages.append(f"[{timestamp}] ✅ Successfully uploaded {len(uploaded_files)}/{total} papers")
            status_messages.append(f"[{timestamp}] 🤖 Generating answer...")
            
            # Cache the uploaded files
            _gemini_file_cache[cache_key] = uploaded_files
        
        # Build prompt with file references
        prompt_parts = [system_prompt, "\n\nPapers:\n"]
        for title, file in uploaded_files:
            prompt_parts.append(f"- {title}\n")
            prompt_parts.append(file)
        prompt_parts.append(f"\n\nQuestion: {question}")
        
        response = gemini_model_obj.generate_content(prompt_parts)
        
        # Prepend status messages to the response
        status_text = "\n".join(status_messages)
        return f"{status_text}\n\n---\n\n{response.text}"
        
    except Exception as e:
        return f"Error calling Gemini with URLs: {str(e)}"

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
            
            # No truncation - send full context
            print(f"[DEBUG] Context length (OpenAI): {len(context)} characters")
            
            # Use the specified model or default to gpt-4o
            model_name = openai_model or 'gpt-4o'
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Papers Content:\n{context}\n\nQuestion: {question}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    elif model == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            return "Gemini API Key not found. Please use the settings (cog wheel) to add your API key."
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            
            # Gemini 1.5 Pro has a large context window, so we can be more generous or pass full text
            # But let's still be reasonable.
            print(f"[DEBUG] Context length before truncation: {len(context)} characters")
            truncated_text = context[:30000]
            print(f"[DEBUG] Context length after truncation (Gemini): {len(truncated_text)} characters")
            
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
    if collection is None:
        return {"authors": [], "affiliations": [], "sessions": [], "days": [], "ampm": ["AM", "PM"]}
    
    global _filters_cache
    if _filters_cache:
        return _filters_cache
        
    import pandas as pd
    try:
        # Read both CSV files to get unique values
        papers_path = "../data/papercopilot_neurips2025_merged_openreview.csv"
        if not os.path.exists(papers_path):
            papers_path = "data/papercopilot_neurips2025_merged_openreview.csv"
            
        events_path = "../data/neurips_2025_enriched_events.csv"
        if not os.path.exists(events_path):
            events_path = "data/neurips_2025_enriched_events.csv"
        
        # Read both CSVs
        df_papers = pd.read_csv(papers_path)
        df_events = pd.read_csv(events_path) if os.path.exists(events_path) else pd.DataFrame()
        
        # Combine for filters
        df = pd.concat([df_papers, df_events], ignore_index=True) if not df_events.empty else df_papers
        
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

        # Derive day list (Tue to Sun) from both CSVs
        # Prefer actual values present in neurips_starttime
        # Filter out Monday (Dec 1) - events in Mexico, not San Diego
        days_set = set()
        if "neurips_starttime" in df.columns:
            for v in df["neurips_starttime"].dropna():
                try:
                    date_part = str(v).split('T')[0]
                    # Filter: San Diego events only (Tue Dec 2 - Sun Dec 7)
                    if date_part and date_part >= "2025-12-02" and date_part <= "2025-12-07":
                        days_set.add(date_part)
                except Exception:
                    pass
        days = sorted(days_set)
        # If empty, fall back to known conference dates (Dec 1-7, 2025)
        if not days:
            days = [
                "2025-12-01",
                "2025-12-02",
                "2025-12-03",
                "2025-12-04",
                "2025-12-05",
                "2025-12-06",
                "2025-12-07",
            ]

        # Build sessions excluding any Mexico City related entries
        raw_sessions = get_unique("neurips_session")
        sessions = [s for s in raw_sessions if 'mexico' not in s.lower()]

        _filters_cache = {
            "affiliations": get_unique("affiliation"),
            "authors": get_unique("authors"),
            "sessions": sessions,
            "days": days,
            "ampm": ["AM", "PM"]
        }
        return _filters_cache
    except Exception as e:
        print(f"Error loading filters: {e}")
        return {"affiliations": [], "authors": [], "sessions": [], "days": [], "ampm": ["AM", "PM"]}
