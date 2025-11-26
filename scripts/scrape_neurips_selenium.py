#!/usr/bin/env python3
"""
DEPRECATED - download the JSON instead

scrape_neurips_index_selenium.py

Instead of scraping the dynamic papers.html page (which only exposes ~400 rows
in the DOM at a time), this script uses the official NeurIPS Downloads export:

    https://neurips.cc/Downloads/2025

Steps:
  1. Open Downloads 2025 with Selenium (using your logged-in Chrome profile).
  2. Click the "csv" link under "Format".
  3. Wait for a CSV file to be downloaded to a known folder.
  4. Parse the CSV with pandas to get all events (posters, orals, etc.).
  5. Build an index:
        norm_title -> {neurips_id, event_type, location, start_time, raw_row}
  6. Save as a CSV you can join with the PaperCopilot CSV on `norm_title`.
"""

import os
import time
import glob
import argparse
import unicodedata
from typing import Dict, Any

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


NEURIPS_DOWNLOADS_URL = "https://neurips.cc/Downloads/2025"


# ---------- Utilities ----------

def normalize_title(t: str) -> str:
    if not isinstance(t, str):
        return ""
    # Lowercase, strip, remove extra spaces, normalize Unicode
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\n", " ").strip().lower()
    t = " ".join(t.split())
    return t


def latest_file(directory: str, pattern: str = "*.csv") -> str:
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        return ""
    return max(files, key=os.path.getmtime)


# ---------- Selenium setup ----------

def create_driver(download_dir: str, chrome_binary: str = None, driver_path: str = "chromedriver") -> webdriver.Chrome:
    """
    Creates a Chrome WebDriver that automatically downloads files to `download_dir`
    without prompting.
    """
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    # Point to your existing Chrome profile if you want to reuse login state.
    # Example (adjust to your actual profile path):
    # options.add_argument("--user-data-dir=/Users/you/Library/Application Support/Google/Chrome")
    # options.add_argument("--profile-directory=Default")

    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    if chrome_binary:
        options.binary_location = chrome_binary

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver


# ---------- Main logic ----------

def download_neurips_csv(driver: webdriver.Chrome, download_dir: str, timeout: int = 120) -> str:
    """
    Open Downloads 2025 page, click the 'csv' export, wait for a CSV to appear
    in `download_dir`, and return its path.
    """
    print(f"Opening {NEURIPS_DOWNLOADS_URL} ...")
    driver.get(NEURIPS_DOWNLOADS_URL)

    wait = WebDriverWait(driver, 60)

    # Make sure the page is loaded by waiting for "Downloads 2025" header.
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//h1[contains(., 'Downloads 2025')]")
        )
    )

    print("Clicking 'csv' under Format ...")
    # The "csv" link is usually an <a> with text 'csv' or a query param like format=csv.
    csv_link = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//a[normalize-space(text())='csv' or contains(@href, 'format=csv')]",
            )
        )
    )
    before = set(glob.glob(os.path.join(download_dir, "*.csv")))
    csv_link.click()

    # Now wait for a *new* CSV to show up in the download dir
    print("Waiting for CSV download ...")
    start = time.time()
    csv_path = ""
    while time.time() - start < timeout:
        time.sleep(1)
        after = set(glob.glob(os.path.join(download_dir, "*.csv")))
        diff = list(after - before)
        if diff:
            csv_path = max(diff, key=os.path.getmtime)
            break

    if not csv_path:
        # Fallback: maybe it overwrote an existing file; just take latest
        csv_path = latest_file(download_dir, "*.csv")

    if not csv_path:
        raise RuntimeError("Timed out waiting for NeurIPS CSV download")

    print(f"Downloaded CSV: {csv_path}")
    return csv_path


def build_title_index_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load NeurIPS CSV and build a lightweight index DataFrame with:

        norm_title, neurips_id, event_type, location, start_time, raw_title

    Column names in the CSV can change slightly; we try to infer them.
    """
    print(f"Loading NeurIPS CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print("CSV columns:", df.columns.tolist())

    cols_lower = {c.lower(): c for c in df.columns}

    # Heuristic: find title/name column
    title_col = None
    for key in ["title", "name", "event name"]:
        for c in df.columns:
            if key in c.lower():
                title_col = c
                break
        if title_col:
            break
    if not title_col:
        raise RuntimeError("Could not infer title column from CSV")

    # Heuristic: ID column
    id_col = None
    for key in ["event id", "id", "eventid"]:
        for c in df.columns:
            if key in c.lower():
                id_col = c
                break
        if id_col:
            break

    # Heuristic: event type (Poster, Oral, etc.)
    type_col = None
    for key in ["event type", "type", "session type"]:
        for c in df.columns:
            if key in c.lower():
                type_col = c
                break
        if type_col:
            break

    # Heuristic: location
    loc_col = None
    for key in ["location", "room"]:
        for c in df.columns:
            if key in c.lower():
                loc_col = c
                break
        if loc_col:
            break

    # Heuristic: start time
    start_col = None
    for key in ["start time", "start", "date"]:
        for c in df.columns:
            if key in c.lower():
                start_col = c
                break
        if start_col:
            break

    # Build index
    out = pd.DataFrame()
    out["raw_title"] = df[title_col].astype(str)
    out["norm_title"] = out["raw_title"].map(normalize_title)
    if id_col:
        out["neurips_id"] = df[id_col]
    else:
        out["neurips_id"] = None
    if type_col:
        out["event_type"] = df[type_col]
    else:
        out["event_type"] = None
    if loc_col:
        out["neurips_location"] = df[loc_col]
    else:
        out["neurips_location"] = None
    if start_col:
        out["neurips_datetime_raw"] = df[start_col]
    else:
        out["neurips_datetime_raw"] = None

    # Optionally filter to main-conference stuff (e.g. Posters / Orals in San Diego)
    # You can tweak this depending on how broad you want the mapping.
    # Example:
    # out = out[out["event_type"].fillna("").str.contains("Poster|Oral", case=False)]

    print(f"Built index for {len(out)} events")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download-dir",
        type=str,
        default="./neurips_downloads",
        help="Directory where Chrome will download the NeurIPS CSV",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="neurips_2025_events_index.csv",
        help="Where to write the normalized title index CSV",
    )
    parser.add_argument(
        "--chromedriver",
        type=str,
        default="chromedriver",
        help="Path to chromedriver executable",
    )
    parser.add_argument(
        "--chrome-binary",
        type=str,
        default=None,
        help="Path to Chrome binary (if needed)",
    )
    args = parser.parse_args()

    driver = create_driver(
        download_dir=args.download_dir,
        chrome_binary=args.chrome_binary,
        driver_path=args.chromedriver,
    )
    try:
        csv_path = download_neurips_csv(driver, args.download_dir)
    finally:
        driver.quit()

    index_df = build_title_index_from_csv(csv_path)
    print(f"Writing {len(index_df)} rows to {args.output_csv}")
    index_df.to_csv(args.output_csv, index=False)
    print("Done.")


if __name__ == "__main__":
    main()
