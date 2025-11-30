#!/bin/bash
# One-time initialization script for Railway

set -e  # Exit on error

# Set default CHROMA_DB_PATH if not set
export CHROMA_DB_PATH=${CHROMA_DB_PATH:-/app/chroma_db}

echo "CHROMA_DB_PATH is set to: $CHROMA_DB_PATH"
echo "Current directory: $(pwd)"
echo "Contents of /app:"
ls -la /app/ || echo "Cannot list /app"

# Ensure chroma_db directory exists
mkdir -p "$CHROMA_DB_PATH"

echo "Checking for ChromaDB at $CHROMA_DB_PATH/chroma.sqlite3..."
if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    echo "ChromaDB not found, running ingest..."
    python -m backend.ingest
    
    # Verify ingest succeeded
    if [ -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
        echo "✓ Ingest completed successfully - chroma.sqlite3 created"
    else
        echo "✗ ERROR: Ingest ran but chroma.sqlite3 not found at $CHROMA_DB_PATH"
        exit 1
    fi
else
    echo "ChromaDB already exists at $CHROMA_DB_PATH, skipping ingest"
fi

echo "Contents of $CHROMA_DB_PATH:"
ls -lh "$CHROMA_DB_PATH/" || echo "Cannot list chroma_db"

echo "Starting uvicorn server on port $PORT..."
# Start the application
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
