#!/usr/bin/env python3
"""
DEPRECATED - download the JSON instead


Enrich PaperCopilot NeurIPS 2025 CSV with NeurIPS paper URLs and session info.

Inputs:
  - papercopilot_neurips2025_raw.csv (from your Selenium scraper)
    columns: title, session_area, authors, affiliation, status, rating,
             avg_rating, openreview_urls, neurips_urls, all_urls

Process:
  1. Scrape https://neurips.cc/virtual/2025/loc/san-diego/papers.html
     to get (title, neurips_paper_url).
  2. For each NeurIPS paper URL, scrape the page to get:
       - presentation_type (e.g. "San Diego Poster", "San Diego Oral")
       - location (e.g. "Exhibit Hall C,D,E #2504")
       - datetime_raw (e.g. "Fri 5 Dec 4:30 p.m. PST — 7:30 p.m. PST")
  3. Join by normalized title with the PaperCopilot CSV.

Output:
  - papercopilot_neurips2025_enriched.csv
"""

import csv
import re
import time
from typing import Dict, Tuple

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

INPUT_CSV = "papercopilot_neurips2025_raw.csv"
OUTPUT_CSV = "papercopilot_neurips2025_enriched.csv"

NEURIPS_PAPERS_URL = "https://neurips.cc/virtual/2025/loc/san-diego/papers.html"

HEADERS = {
    "User-Agent": "NeurIPS-2025-Schedule-Joiner (contact: your-email@example.com)"
}
REQUEST_TIMEOUT = 20
SLEEP_BETWEEN_REQUESTS = 0.3  # be polite


session = requests.Session()
session.headers.update(HEADERS)


def fetch(url: str) -> str:
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def norm_title(title: str) -> str:
    """Normalize title for matching across sources."""
    t = title.lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


# ---------- STEP 1: Read your existing CSV ----------

def load_papercopilot_csv(path: str):
    rows = []
    by_norm_title: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # ensure all expected keys exist
            for k in [
                "title",
                "session_area",
                "authors",
                "affiliation",
                "status",
                "rating",
                "avg_rating",
                "openreview_urls",
                "neurips_urls",
                "all_urls",
            ]:
                if k not in row:
                    row.setdefault(k, "")
            t = row["title"].strip()
            row["norm_title"] = norm_title(t)
            rows.append(row)
            by_norm_title[row["norm_title"]] = row
    return rows, by_norm_title


# ---------- STEP 2: Scrape NeurIPS index (title -> URL) ----------

def scrape_neurips_index() -> Dict[str, str]:
    """
    Return mapping: norm_title -> neurips_paper_url for San Diego papers.
    """
    html = fetch(NEURIPS_PAPERS_URL)
    soup = BeautifulSoup(html, "html.parser")

    mapping: Dict[str, str] = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Filter to San Diego poster/oral/talk pages
        if "/virtual/2025/loc/san-diego/" in href and (
            "/poster/" in href or "/oral/" in href or "/talk/" in href
        ):
            title = a.get_text(strip=True)
            if not title:
                continue
            url = urljoin("https://neurips.cc", href)
            nt = norm_title(title)
            # If duplicates happen, last one wins; in practice titles should be unique here
            mapping[nt] = url

    print(f"[NeurIPS index] Found {len(mapping)} unique titles with URLs")
    return mapping


# ---------- STEP 3: Scrape each NeurIPS paper page ----------

def parse_neurips_paper_page(url: str) -> Tuple[str, str, str]:
    """
    Parse a NeurIPS poster/oral page.

    Returns (presentation_type, location, datetime_raw).
    Example page (poster):
      - "###  San Diego Poster"
      - "##  Coloring Learning for Heterophilic Graph Representation"
      - "##### Exhibit Hall C,D,E #2504"
      - "Fri 5 Dec 4:30 p.m. PST — 7:30 p.m. PST"
    """
    try:
        html = fetch(url)
    except Exception as e:
        print(f"[WARN] Failed to fetch NeurIPS page {url}: {e}")
        return "", "", ""

    soup = BeautifulSoup(html, "html.parser")

    # Presentation type: look for heading containing "Poster", "Oral", "Talk"
    presentation_type = ""
    for h in soup.find_all(["h3", "h4"]):
        txt = h.get_text(" ", strip=True)
        if any(word in txt for word in ["Poster", "Oral", "Talk"]):
            presentation_type = txt
            break

    # Location: the "Exhibit Hall..." line (or a Room)
    location = ""
    # Date/time: line that contains timezone & an em dash or hyphen
    datetime_raw = ""

    for tag in soup.find_all(["h5", "h6", "p", "span"]):
        txt = tag.get_text(" ", strip=True)
        if not txt:
            continue
        if any(k in txt for k in ["Exhibit Hall", "Room", "#"]):
            if not location:
                location = txt
        if any(tz in txt for tz in ["PST", "PDT"]) and ("—" in txt or "-" in txt):
            if not datetime_raw:
                datetime_raw = txt

    return presentation_type, location, datetime_raw


def build_neurips_metadata(neurips_index: Dict[str, str]) -> Dict[str, dict]:
    """
    For each (norm_title -> url) in the NeurIPS index, fetch session info.

    Returns: norm_title -> {
        'neurips_paper_url': ...,
        'neurips_id': ...,
        'presentation_type': ...,
        'location': ...,
        'datetime_raw': ...
    }
    """
    meta: Dict[str, dict] = {}
    for nt, url in neurips_index.items():
        # extract numeric id if present
        m = re.search(r"/(poster|oral|talk)/(\d+)", url)
        neurips_id = m.group(2) if m else ""

        presentation_type, location, datetime_raw = parse_neurips_paper_page(url)

        meta[nt] = {
            "neurips_paper_url": url,
            "neurips_id": neurips_id,
            "presentation_type": presentation_type,
            "location": location,
            "datetime_raw": datetime_raw,
        }

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"[NeurIPS detail] Built metadata for {len(meta)} titles")
    return meta


# ---------- STEP 4: Join and write out ----------

def main():
    print(f"Loading PaperCopilot CSV: {INPUT_CSV}")
    rows, pc_by_title = load_papercopilot_csv(INPUT_CSV)
    print(f"Loaded {len(rows)} rows from PaperCopilot")

    print("Scraping NeurIPS index (San Diego)...")
    neurips_index = scrape_neurips_index()

    print("Scraping per-paper NeurIPS pages for session info...")
    neurips_meta = build_neurips_metadata(neurips_index)

    # Add new columns to each row
    for row in rows:
        nt = row["norm_title"]
        meta = neurips_meta.get(nt, {})
        row["neurips_paper_url"] = meta.get("neurips_paper_url", "")
        row["neurips_id"] = meta.get("neurips_id", "")
        row["presentation_type"] = meta.get("presentation_type", "")
        row["neurips_location"] = meta.get("location", "")
        row["neurips_datetime_raw"] = meta.get("datetime_raw", "")

    # Write out
    fieldnames = list(rows[0].keys())
    print(f"Writing enriched CSV: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
