# NeuriScout

A full-stack application for searching and analyzing NeurIPS 2025 research papers using semantic search and LLM-powered insights.

## Features

- **Semantic Search**: Search through NeurIPS 2025 papers, workshops, tutorials, and invited talks using natural language queries
- **Advanced Filtering**: Filter by author, affiliation, session/event type, and conference day/time (AM/PM)
  - **Full Conference Coverage**: Search across the entire NeurIPS 2025 San Diego program (Dec 2-7)
  - **Multiple Content Types**: Papers (5,450 items), workshops, tutorials, and invited talks
  - **Smart Session Filtering**: Find specific event types like "Invited Talk" or "Workshop"
- **Deep Dive Chat**: Add up to 25 papers to a Deep Dive queue and chat about them with OpenAI or Google Gemini
   - **One-click add**: Use the button on each paper card or “Add all to Deep Dive” for the current results
   - **Smart Pre-upload**: Papers are uploaded when you open the chat panel, making your first query instant
   - **File Caching**: Papers are cached per session - no re-uploading on subsequent questions
   - **Full Paper Access**: Gemini reads complete PDFs natively (no truncation)
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
git clone https://github.com/gminneci/NeuriScout.git
cd NeuriScout
```

2. Set up Python environment and install backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

This installs the package in editable mode with all dependencies and creates the `neuriscout-backend` and `neuriscout-ingest` commands.

3. Generate the ChromaDB database:
```bash
neuriscout-ingest
```

This will process the data from:
- `data/papercopilot_neurips2025_merged_openreview.csv` (papers)
- `data/neurips_2025_enriched_events.csv` (workshops, tutorials, invited talks)

Creates the vector database in `chroma_db/` with embeddings for 5,450 unique items (papers + events). This takes a few minutes and creates ~90MB of data.

**Note:** The ChromaDB is required for the application to work. Keep it in the `chroma_db/` directory (it's excluded from git).

4. Set up frontend:
```bash
cd frontend
npm install
cd ..
```

5. Configure API keys (optional):

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

1. **Search Papers & Events**: Enter keywords or research questions in the search box
2. **Filter Results**: 
   - Use the dropdowns to filter by author, affiliation, or session
   - Filter by session to find specific content types:
     - "Invited Talk" - Find all 6 invited talks (Rich Sutton, Zeynep Tufekci, Yejin Choi, Melanie Mitchell, Kyunghyun Cho, Andrew Saxe)
     - "Workshop" - Browse workshop sessions
     - "Tutorial" - Find tutorial sessions
     - Or filter by poster sessions (e.g., "San Diego Poster Session 1")
   - Use day filters (Tue-Sun) and time filters (AM/PM) to browse by conference schedule
   - Combine multiple filters with OR logic (e.g., "MIT" OR "Stanford")
3. **Build Your Deep Dive**:
   - Click "Add to Deep Dive" on individual paper cards (or "Add all to Deep Dive" for the current results)
   - Track how many slots remain (up to 25 papers can be active at once)
   - Remove papers from the Deep Dive button if you want to swap them out
4. **Deep Dive Chat**:
   - Click "Deep Dive (X/25)" to open the chat panel
   - Papers are automatically uploaded in the background (Gemini only)
   - Click the settings icon to configure API keys and models
   - Ask questions about the Deep Dive papers and tweak the system prompt anytime
   - Subsequent questions are instant thanks to file caching

## Data Processing

The `scripts/` directory contains utilities for:
- Scraping paper data from various sources
- Merging datasets
- Data validation and debugging

## Deployment (Free Hosting)

### Deploy to Vercel (Frontend) + Render (Backend)

#### Backend Deployment (Render)

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Name: `neuriscout-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -e .`
   - Start Command: `neuriscout-backend`

3. **Add a Persistent Disk** (for ChromaDB):
   - Go to your service settings
   - Add Disk: Mount path `/opt/render/project/src/chroma_db`, Size: 1GB

4. **Set Environment Variables**:
   ```
   PYTHON_VERSION=3.11.0
   HOST=0.0.0.0
   PORT=8000
   CHROMA_DB_PATH=/opt/render/project/src/chroma_db
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
   
   Optional (or enter in UI):
   ```
   OPENAI_API_KEY=your_key
   GEMINI_API_KEY=your_key
   ```

5. **Upload ChromaDB data**:
   - The ChromaDB database is NOT included in the repository (it's ~90MB)
   - You need to generate it locally using `neuriscout-ingest` and then upload it
   - Options for uploading:
     - **Via Render Shell**: Access your service's Shell tab and run `neuriscout-ingest`
     - **Manual upload**: Use `scp` or Render's file upload to copy your local `chroma_db/` directory to the persistent disk mount path
   - The database contains 5,450 unique items (papers, workshops, tutorials, invited talks) with embeddings and takes a few minutes to generate

6. **Copy your service URL** (e.g., `https://neuriscout-backend.onrender.com`)

#### Frontend Deployment (Vercel)

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

2. **Import your repository**:
   - Click "New Project"
   - Import your GitHub repository
   - Root Directory: `frontend`
   - Framework Preset: `Next.js`

3. **Configure Environment Variables**:
   - Add `NEXT_PUBLIC_API_URL` with your Render backend URL
   - Example: `https://neuriscout-backend.onrender.com`

4. **Update CORS on Backend**:
   - Go back to Render dashboard
   - Update `ALLOWED_ORIGINS` to include your Vercel URL
   - Example: `https://neuriscout.vercel.app,https://neuriscout-*.vercel.app`

5. **Deploy!**
   - Vercel will automatically deploy
   - Your app will be live at `https://your-app.vercel.app`

#### Important Notes:

- **Cold Starts**: Render's free tier sleeps after 15 minutes of inactivity. First request takes ~30 seconds to wake up.
- **API Keys**: You can set API keys as environment variables on Render, or users can enter them in the UI.
- **ChromaDB Database**: 
  - The vector database is NOT in the repository (excluded via `.gitignore`)
  - Generate it locally with `neuriscout-ingest` before deploying
  - Upload to the persistent disk after deployment (via Render Shell or manual transfer)
  - The database is ~90MB and contains embeddings for 5,450 items (papers + events)
- **Custom Domain**: Both Vercel and Render support custom domains for free.

### Alternative: Deploy to Railway

Railway offers $5 free credit per month and simpler deployment:

1. **Create Railway account** at [railway.app](https://railway.app)
2. **Deploy from GitHub**:
   - New Project → Deploy from GitHub
   - Select your repository
3. **Set environment variables**:
   ```
   HOST=0.0.0.0
   ALLOWED_ORIGINS=*
   CHROMA_DB_PATH=/app/chroma_db
   ```
4. **Upload ChromaDB**:
   - Generate locally: `neuriscout-ingest`
   - Upload using Railway CLI or create a persistent volume and transfer files
   - The `chroma_db/` directory (~90MB) must be accessible at the path set in `CHROMA_DB_PATH`

**Note**: Railway paid tier ($5/month) is recommended for reliable hosting with better resources.

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
