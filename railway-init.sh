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

echo "Checking for ChromaDB collection..."
# Check if collection exists by trying to query it
if python -c "
import chromadb
import sys
try:
    client = chromadb.PersistentClient(path='$CHROMA_DB_PATH')
    collection = client.get_collection('neurips_papers')
    count = collection.count()
    print(f'Collection found with {count} items')
    sys.exit(0 if count > 0 else 1)
except:
    print('Collection not found or empty')
    sys.exit(1)
" 2>/dev/null; then
    echo "✓ ChromaDB collection exists and has data, skipping ingest"
else
    echo "ChromaDB collection missing or empty, running ingest..."
    python -m backend.ingest
    
    # Verify ingest succeeded
    if [ -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
        echo "✓ Ingest completed successfully - chroma.sqlite3 created"
    else
        echo "✗ ERROR: Ingest ran but chroma.sqlite3 not found at $CHROMA_DB_PATH"
        exit 1
    fi
fi

echo "Contents of $CHROMA_DB_PATH:"
ls -lh "$CHROMA_DB_PATH/" || echo "Cannot list chroma_db"

echo "Starting uvicorn server on port $PORT..."
# Start the application
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
