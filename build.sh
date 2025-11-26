#!/bin/bash
# Build script for Render

echo "Installing Python dependencies..."
pip install -e .

echo "Checking if chroma_db exists..."
if [ ! -d "chroma_db" ]; then
    echo "WARNING: chroma_db directory not found!"
    echo "You need to upload your chroma_db to Render's persistent disk"
    echo "Or run the ingest script to create it"
fi

echo "Build complete!"
