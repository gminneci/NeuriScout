#!/bin/bash
# One-time initialization script for Railway

if [ ! -d "$CHROMA_DB_PATH" ] || [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    echo "ChromaDB not found, running ingest..."
    python -m backend.ingest
else
    echo "ChromaDB already exists, skipping ingest"
fi

# Start the application
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
