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
git clone https://github.com/gminneci/NeuriScout.git
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
   - After first deploy, SSH into your service or use Render Shell
   - Run `neuriscout-ingest` or upload your local `chroma_db` to the persistent disk

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
- **Database**: The ChromaDB data must be on the persistent disk. Make sure to run the ingest script or upload your data after deployment.
- **Custom Domain**: Both Vercel and Render support custom domains for free.

### Alternative: Deploy to Railway

Railway offers $5 free credit per month and simpler deployment:

1. **Create Railway account** at [railway.app](https://railway.app)
2. **Deploy from GitHub**:
   - New Project → Deploy from GitHub
   - Select your repository
3. **Add two services**:
   - Backend: Root directory `.`, Start command `neuriscout-backend`
   - Frontend: Root directory `frontend`, Start command `npm run start`
4. **Set environment variables** similar to above
5. **Add persistent volume** for ChromaDB

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
