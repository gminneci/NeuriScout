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

def start_server():
    """Entry point for the neuriscout-backend command."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
