#!/bin/bash
# Rescrape expo events with date/time information

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "Starting expo event rescrape with date/time information..."
echo "This will take a few minutes (48 events x 0.5s = ~24 seconds)"
echo ""

python scripts/scrape_expo_events.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Scraping complete!"
    echo "Now re-ingesting data..."
    python backend/ingest.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ All done! Expo events now have date/time information."
    else
        echo "✗ Ingest failed"
        exit 1
    fi
else
    echo "✗ Scraping failed"
    exit 1
fi
