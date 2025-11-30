from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union, Any
import uvicorn
import os
from dotenv import load_dotenv
from backend import rag

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NeuriScout - NeurIPS 2025 Paper Explorer")

# Get allowed origins from environment variable
# For development: "http://localhost:3000"
# For production: "https://your-app.vercel.app" or "*" (not recommended for production)
ALLOWED_ORIGINS_STR = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

# Handle wildcard or parse comma-separated origins
if ALLOWED_ORIGINS_STR == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    affiliation: Optional[Any] = None
    author: Optional[Any] = None
    session: Optional[Any] = None
    day: Optional[Any] = None  # Filter by conference day (Dec 3, 4, or 5)
    ampm: Optional[str] = None  # Filter by time of day: 'AM' or 'PM'
    limit: Optional[int] = 10
    threshold: Optional[float] = None # Similarity threshold (0.0 to 1.0, lower distance is better)
    
    @field_validator('affiliation', 'author', 'session', 'day', mode='before')
    @classmethod
    def validate_filter_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return v
        raise ValueError(f'Must be a string or list of strings, got {type(v)}')

class PaperItem(BaseModel):
    url: str
    title: str

class ChatRequest(BaseModel):
    papers: List[PaperItem]
    question: str
    model: str = "openai"
    api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_model: Optional[str] = None
    system_prompt: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest):
    # Debug: Log API key status
    print(f"[DEBUG] Received chat request - API key provided: {request.api_key is not None}, Model: {request.model}")
    print(f"[DEBUG] Number of papers in request: {len(request.papers)}")
    
    # Use URL-based approach for Gemini (no truncation!)
    if request.model == "gemini":
        paper_urls = [(p.title, p.url) for p in request.papers]
        answer = await rag.answer_question_with_urls(
            paper_urls,
            request.question,
            model=request.model,
            api_key=request.api_key,
            gemini_model=request.gemini_model,
            system_prompt=request.system_prompt
        )
        return {"answer": answer}
    
    # For OpenAI, fetch and extract text (with truncation)
    urls = [p.url for p in request.papers]
    texts = await rag.fetch_multiple_papers(urls)
    
    # Combine texts with titles
    combined_context = ""
    for i, text in enumerate(texts):
        combined_context += f"--- Paper: {request.papers[i].title} ---\n{text}\n\n"
    
    # 2. Answer question
    answer = rag.answer_question(
        combined_context, 
        request.question, 
        model=request.model, 
        api_key=request.api_key,
        gemini_model=request.gemini_model,
        openai_model=request.openai_model,
        system_prompt=request.system_prompt
    )
    
    return {"answer": answer}

@app.post("/search")
def search(request: SearchRequest):
    filters = {}
    if request.affiliation:
        filters['affiliation'] = request.affiliation
    if request.author:
        filters['author'] = request.author
    if request.session:
        filters['session'] = request.session
    if request.day:
        filters['day'] = request.day
    if request.ampm:
        filters['ampm'] = request.ampm.upper()
        
    return rag.search_papers(
        query=request.query,
        n_results=request.limit,
        filters=filters,
        threshold=request.threshold
    )

@app.get("/filters")
def get_filters():
    return rag.get_filters()

class GeminiModelsRequest(BaseModel):
    api_key: str

@app.post("/gemini-models")
def get_gemini_models(request: GeminiModelsRequest):
    try:
        import google.generativeai as genai
        genai.configure(api_key=request.api_key)
        
        models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                models.append({
                    'name': model.name,
                    'display_name': model.display_name,
                    'description': model.description if hasattr(model, 'description') else ''
                })
        return {'models': models}
    except Exception as e:
        return {'error': str(e), 'models': []}

class OpenAIModelsRequest(BaseModel):
    api_key: str

@app.post("/openai-models")
def get_openai_models(request: OpenAIModelsRequest):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=request.api_key)
        
        models = []
        # Get list of models
        model_list = client.models.list()
        
        # Filter for chat models (gpt models)
        for model in model_list.data:
            if model.id.startswith('gpt'):
                models.append({
                    'name': model.id,
                    'display_name': model.id,
                    'description': ''
                })
        
        # Sort by name, with gpt-4 models first
        models.sort(key=lambda x: (not x['name'].startswith('gpt-4'), x['name']))
        
        return {'models': models}
    except Exception as e:
        return {'error': str(e), 'models': []}

@app.post("/admin/reingest")
async def trigger_reingest():
    """
    Trigger a re-ingestion of papers into ChromaDB.
    WARNING: This will delete existing data and re-ingest from CSV files.
    """
    import subprocess
    import sys
    import os
    
    try:
        # Get the base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Run ingest as a subprocess with unbuffered output
        result = subprocess.run(
            [sys.executable, "-u", "-m", "backend.ingest"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=base_dir,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "message": "Ingest completed" if result.returncode == 0 else "Ingest failed"
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Ingest process timed out after 10 minutes")
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to run ingest: {str(e)}\n{traceback.format_exc()}")

@app.post("/admin/reingest_async")
def trigger_reingest_async():
    """
    Launch ingest in the background and return immediately.
    Progress is written to /app/ingest.log (or local BASE_DIR/ingest.log).
    """
    import subprocess
    import sys
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "ingest.log")

    try:
        # Start background process piping stdout/stderr to log file
        with open(log_path, "w") as f:
            proc = subprocess.Popen(
                [sys.executable, "-u", "-m", "backend.ingest"],
                cwd=base_dir,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                stdout=f,
                stderr=subprocess.STDOUT,
            )
        return {"started": True, "pid": proc.pid, "log": log_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/ingest-status")
def ingest_status(lines: int = 200):
    """
    Return the last N lines of the ingest log and whether the collection exists.
    """
    import os
    from pathlib import Path
    import chromadb
    base_dir = Path(__file__).parent.parent
    log_path = base_dir / "ingest.log"

    # Read tail of log if exists
    log_tail = ""
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                data = f.readlines()
                log_tail = "".join(data[-lines:])
        except Exception as e:
            log_tail = f"<error reading log: {e}>"

    # Check collection
    chroma_path = os.getenv("CHROMA_DB_PATH", str(base_dir / "chroma_db"))
    status = {"log_path": str(log_path), "log_tail": log_tail, "collection": {}}
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection('neurips_papers')
        status["collection"] = {"exists": True, "count": collection.count()}
    except Exception as e:
        status["collection"] = {"exists": False, "error": str(e)}

    return status

@app.get("/admin/status")
def get_status():
    """Check the status of ChromaDB and data files."""
    import os
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent
    status = {
        "base_dir": str(base_dir),
        "chroma_path": os.getenv("CHROMA_DB_PATH", str(base_dir / "chroma_db")),
        "data_files": {},
        "collection_status": None
    }
    
    # Check CSV files
    csv_files = [
        "data/papercopilot_neurips2025_merged_openreview.csv",
        "data/neurips_2025_enriched_events.csv"
    ]
    
    for csv_file in csv_files:
        csv_path = base_dir / csv_file
        status["data_files"][csv_file] = {
            "exists": csv_path.exists(),
            "size_mb": round(csv_path.stat().st_size / 1024 / 1024, 2) if csv_path.exists() else None
        }
    
    # Check collection
    try:
        import chromadb
        client = chromadb.PersistentClient(path=status["chroma_path"])
        collection = client.get_collection('neurips_papers')
        status["collection_status"] = {
            "exists": True,
            "count": collection.count()
        }
    except Exception as e:
        status["collection_status"] = {
            "exists": False,
            "error": str(e)
        }
    
    return status

def start_server():
    """Entry point for the neuriscout-backend command."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
