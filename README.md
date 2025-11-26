# NeuriScout

A full-stack application for searching and analyzing NeurIPS 2025 research papers using semantic search and LLM-powered insights.

## Features

- **Semantic Search**: Search through NeurIPS 2025 papers using natural language queries
- **Advanced Filtering**: Filter by author, affiliation, and session
- **Deep Dive Chat**: Ask questions about selected papers using OpenAI or Google Gemini
- **Markdown & LaTeX Support**: Full rendering of mathematical formulas and formatted text
- **Customizable System Prompts**: Configure how the AI responds to your questions
- **Model Selection**: Choose from available OpenAI and Gemini models

## Project Structure

```
NeuriScout/
├── backend/              # FastAPI backend server
│   ├── main.py          # API endpoints
│   ├── rag.py           # RAG logic and paper fetching
│   └── ingest.py        # Data ingestion script
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Pages and components
│       └── lib/         # API client
├── data/                # Data files (CSV, JSON)
├── scripts/             # Utility scripts for data processing
└── chroma_db/          # Vector database (generated)
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key and/or Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd NeuriScout
```

2. Set up Python environment and install backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

This installs the package in editable mode with all dependencies and creates the `neuriscout-backend` command.

3. Set up frontend:
```bash
cd frontend
npm install
cd ..
```

4. Configure API keys (optional):

You can either set environment variables or enter them in the UI:

```bash
export OPENAI_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
```

### Running the Application

1. **Start the backend** (in one terminal):
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
neuriscout-backend
```
The backend will run on http://localhost:8000

**Note:** The first startup takes 10-30 seconds while loading AI models.

2. **Start the frontend** (in a new terminal):
```bash
cd frontend
npm run dev
```
The frontend will run on http://localhost:3000

3. **Open your browser** to http://localhost:3000

## Usage

1. **Search Papers**: Enter keywords or research questions in the search box
2. **Filter Results**: Use the dropdowns to filter by author, affiliation, or session
3. **Select Papers**: Check the papers you want to analyze
4. **Deep Dive Chat**: 
   - Click "Deep Dive Chat" to open the chat panel
   - Click the settings icon to configure API keys and models
   - Ask questions about the selected papers
   - Customize the system prompt to change AI behavior

## Data Processing

The `scripts/` directory contains utilities for:
- Scraping paper data from various sources
- Merging datasets
- Data validation and debugging

## Technology Stack

**Backend:**
- FastAPI
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- OpenAI API / Google Gemini API

**Frontend:**
- Next.js 16
- React
- TypeScript
- Tailwind CSS
- React Markdown + KaTeX

## License

MIT License
