#!/bin/bash
# One-time initialization script for Railway

set -e  # Exit on error

# Set default CHROMA_DB_PATH if not set
export CHROMA_DB_PATH=${CHROMA_DB_PATH:-/app/chroma_db}

echo "CHROMA_DB_PATH is set to: $CHROMA_DB_PATH"

# Ensure chroma_db directory exists
mkdir -p "$CHROMA_DB_PATH"

echo "Checking for ChromaDB at $CHROMA_DB_PATH/chroma.sqlite3..."
if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    echo "ChromaDB not found, running ingest..."
    python -m backend.ingest
    echo "Ingest completed successfully"
else
    echo "ChromaDB already exists at $CHROMA_DB_PATH, skipping ingest"
fi

echo "Starting uvicorn server on port $PORT..."
# Start the application
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
