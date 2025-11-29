#!/bin/bash
# One-time initialization script for Railway

# Set default CHROMA_DB_PATH if not set
export CHROMA_DB_PATH=${CHROMA_DB_PATH:-/app/chroma_db}

# Ensure chroma_db directory exists
mkdir -p "$CHROMA_DB_PATH"

if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    echo "ChromaDB not found at $CHROMA_DB_PATH, running ingest..."
    python -m backend.ingest
else
    echo "ChromaDB already exists at $CHROMA_DB_PATH, skipping ingest"
fi

# Start the application
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
