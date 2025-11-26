# Deployment Checklist for NeuriScout

## Pre-Deployment Security Check ✅

- [x] No hardcoded API keys in code
- [x] API keys handled via environment variables or UI input
- [x] .env files added to .gitignore
- [x] CORS configured for production domains
- [x] Environment variable examples created

## Files Created for Deployment

### Configuration Files
- `.env.example` - Example environment variables for backend
- `frontend/.env.local.example` - Example for local development
- `frontend/.env.production.example` - Example for production
- `requirements.txt` - Python dependencies (for platforms that prefer it over pyproject.toml)
- `Procfile` - For Heroku-style deployments
- `render.yaml` - Render.com configuration
- `vercel.json` - Vercel configuration
- `build.sh` - Build script for Render

### Code Changes
- `backend/main.py` - Added CORS configuration with environment variables
- `backend/rag.py` - Made ChromaDB path configurable via CHROMA_DB_PATH env var
- `frontend/src/lib/api.ts` - Made API URL configurable via NEXT_PUBLIC_API_URL

## Deployment Steps

### 1. Backend (Render.com)

#### Initial Setup
- [ ] Create Render account
- [ ] Connect GitHub repository
- [ ] Create new Web Service
- [ ] Select Python environment
- [ ] Configure build and start commands

#### Environment Variables
Set these in Render dashboard:
- [ ] `PYTHON_VERSION=3.11.0`
- [ ] `HOST=0.0.0.0`
- [ ] `PORT=8000`
- [ ] `CHROMA_DB_PATH=/opt/render/project/src/chroma_db`
- [ ] `ALLOWED_ORIGINS=https://your-app.vercel.app` (update after frontend deployment)
- [ ] `OPENAI_API_KEY` (optional - can be set in UI)
- [ ] `GEMINI_API_KEY` (optional - can be set in UI)

#### Persistent Storage
- [ ] Add persistent disk (1GB free tier)
- [ ] Mount path: `/opt/render/project/src/chroma_db`
- [ ] Upload or generate ChromaDB data

#### After First Deploy
- [ ] Test backend health: `https://your-backend.onrender.com/docs`
- [ ] Copy backend URL for frontend configuration

### 2. Frontend (Vercel)

#### Initial Setup
- [ ] Create Vercel account
- [ ] Import GitHub repository
- [ ] Set root directory to `frontend`
- [ ] Select Next.js framework preset

#### Environment Variables
- [ ] `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`

#### After Deploy
- [ ] Test frontend loads
- [ ] Copy Vercel URL
- [ ] Update backend CORS settings with Vercel URL

### 3. Final Configuration

#### Update CORS on Backend
- [ ] Go to Render dashboard
- [ ] Update `ALLOWED_ORIGINS` environment variable
- [ ] Include your Vercel URL and preview URLs
- [ ] Example: `https://neuriscout.vercel.app,https://neuriscout-*.vercel.app`
- [ ] Redeploy backend if needed

#### Test Everything
- [ ] Search functionality works
- [ ] Filters work (author, affiliation, session)
- [ ] Paper selection works
- [ ] Deep Dive Chat opens
- [ ] Chat with API key (entered in UI or env var) works
- [ ] LaTeX rendering works
- [ ] No CORS errors in browser console

### 4. ChromaDB Data

Choose one option:

#### Option A: Upload Existing Database
- [ ] Use Render Shell or SSH
- [ ] Upload your local `chroma_db` directory to persistent disk
- [ ] Verify files are in `/opt/render/project/src/chroma_db`

#### Option B: Generate on Server
- [ ] Upload data files to server
- [ ] Run `neuriscout-ingest` via Render Shell
- [ ] Wait for ingestion to complete
- [ ] Verify database was created

## Common Issues

### Backend Sleeping (Render Free Tier)
- ✅ Expected behavior - wakes in ~30 seconds on first request
- Consider keeping it awake with periodic pings if needed
- Or upgrade to paid tier for always-on

### CORS Errors
- Check `ALLOWED_ORIGINS` includes your frontend domain
- Include wildcard for preview deployments: `https://*-yourapp.vercel.app`
- Redeploy backend after changing CORS settings

### Large Model Downloads
- First startup may take 2-3 minutes downloading sentence-transformers model
- Models are cached after first download
- Consider including models in Docker image for faster starts

### ChromaDB Not Found
- Verify persistent disk is mounted correctly
- Check `CHROMA_DB_PATH` environment variable
- Run ingest script or upload database

## Free Tier Limitations

### Render
- ✅ 750 hours/month (enough for one service 24/7)
- ✅ Sleeps after 15 min inactivity
- ✅ 1GB persistent disk
- ⚠️ Cold start ~30 seconds
- ⚠️ Slower CPU than paid tiers

### Vercel
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic SSL
- ✅ Preview deployments for PRs
- ⚠️ 10-second serverless function timeout

## Optional Improvements

### Performance
- [ ] Add Redis caching for search results
- [ ] Pre-warm backend to avoid cold starts
- [ ] Optimize ChromaDB queries
- [ ] Add CDN for static assets

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Add analytics (Vercel Analytics)
- [ ] Monitor backend health
- [ ] Set up uptime monitoring

### Features
- [ ] Add user authentication
- [ ] Save search history
- [ ] Bookmark favorite papers
- [ ] Share search results via URL

## Support

If you encounter issues:
1. Check Render/Vercel deployment logs
2. Verify environment variables are set correctly
3. Test backend API directly at `/docs` endpoint
4. Check browser console for CORS errors
5. Verify ChromaDB data exists on persistent disk
