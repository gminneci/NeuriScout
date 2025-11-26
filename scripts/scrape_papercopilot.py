#!/usr/bin/env python3
"""
Scrape NeurIPS 2025 Accepted Paper List from Paper Copilot:

  https://papercopilot.com/paper-list/neurips-paper-list/neurips-2025-paper-list/

Outputs a CSV with one row per paper, including:

- title
- session_area
- authors
- affiliation
- status
- rating
- avg_rating
- openreview_urls (semicolon-separated)
- neurips_urls (semicolon-separated)
- all_urls (semicolon-separated)
"""

import csv
import time
from dataclasses import dataclass, asdict
from tqdm import tqdm
from typing import List, Dict
import re
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException


URL = "https://papercopilot.com/paper-list/neurips-paper-list/neurips-2025-paper-list/"
OUTPUT_CSV = "papercopilot_neurips2025_raw.csv"


@dataclass
class PaperRow:
    title: str = ""
    session_area: str = ""
    authors: str = ""
    affiliation: str = ""
    status: str = ""
    rating: str = ""
    avg_rating: str = ""
    openreview_urls: str = ""
    neurips_urls: str = ""
    all_urls: str = ""


def setup_driver(headless: bool = False):
    """Create a Chrome WebDriver (non-headless by default so you can interact)."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )
    return driver


def extract_urls_from_row(row_element) -> (List[str], List[str], List[str]):
    """
    Extract all URLs from the row, and classify openreview vs neurips vs others.
    """
    all_urls = []
    openreview_urls = []
    neurips_urls = []

    anchors = row_element.find_elements(By.TAG_NAME, "a")
    for a in anchors:
        href = a.get_attribute("href")
        if not href:
            continue
        all_urls.append(href)
        if "openreview.net" in href:
            openreview_urls.append(href)
        if "neurips.cc" in href or "nips.cc" in href:
            neurips_urls.append(href)

    # Deduplicate while preserving order
    def unique(seq):
        seen = set()
        out = []
        for x in seq:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    all_urls = unique(all_urls)
    openreview_urls = unique(openreview_urls)
    neurips_urls = unique(neurips_urls)

    return openreview_urls, neurips_urls, all_urls


def extract_affiliation_from_cell(cell) -> str:
    """
    Extract affiliation text from the affiliation <td>.

    Strategy:
    1. Look at <a> children inside the cell (this is where Paper Copilot puts orgs).
       - Try tooltip attrs: data-bs-original-title, data-original-title, title, aria-label
       - Try anchor text
    2. If still nothing, fall back to host names from hrefs
       (e.g. 'www.tsinghua.edu.cn' -> 'Tsinghua').
    """
    candidates = []

    anchors = cell.find_elements(By.TAG_NAME, "a")

    # 1) Tooltip attributes / visible text on anchors
    for a in anchors:
        for attr in ["data-bs-original-title", "data-original-title", "title", "aria-label"]:
            val = a.get_attribute(attr)
            if val and val.strip() and val.strip() != "-":
                candidates.append(val.strip())
        txt = (a.text or "").strip()
        if txt and txt != "-":
            candidates.append(txt)

    # 2) Tooltip attributes on the cell itself (just in case)
    for attr in ["data-bs-original-title", "data-original-title", "title", "aria-label"]:
        val = cell.get_attribute(attr)
        if val and val.strip() and val.strip() != "-":
            candidates.append(val.strip())

    # Deduplicate while preserving order
    def unique(seq):
        seen = set()
        out = []
        for x in seq:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    candidates = unique(candidates)

    if candidates:
        return "; ".join(candidates)

    # 3) Fallback: derive names from domains in hrefs (better than empty)
    domain_names = []
    for a in anchors:
        href = a.get_attribute("href") or ""
        if not href:
            continue
        host = urlparse(href).netloc  # e.g. 'www.tsinghua.edu.cn'
        if not host:
            continue
        host = re.sub(r"^www\.", "", host)  # 'tsinghua.edu.cn'
        base = host.split(".")[0]  # crude: 'tsinghua'
        if not base:
            continue
        base = re.sub(r"[-_]", " ", base)
        base = " ".join(w.capitalize() for w in base.split())
        domain_names.append(base)

    domain_names = unique(domain_names)
    if domain_names:
        return "; ".join(domain_names)

    # 4) Last resort: visible text (which is probably just "-")
    txt = (cell.text or "").strip()
    if txt and txt != "-":
        return txt

    return ""


def scrape_table(driver) -> List[PaperRow]:
    """
    Parse the NeurIPS 2025 table on Paper Copilot.

    - Finds the main table
    - Locates the header row by looking for "Title", "Session/Area", "Authors"
    - Uses that row as header; all following rows are treated as data
    """

    wait = WebDriverWait(driver, 40)

    # Wait for at least one table to be present
    wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
    tables = driver.find_elements(By.XPATH, "//table")
    print(f"Found {len(tables)} <table> elements")

    if not tables:
        raise RuntimeError("No <table> elements found at all")

    # Choose the table whose text mentions the column labels
    main_table = None
    for t in tables:
        txt = t.text
        if "Title" in txt and "Session/Area" in txt and "Authors" in txt:
            main_table = t
            break

    if main_table is None:
        print("WARNING: Could not find table containing Title/Session/Area/Authors; using first table.")
        main_table = tables[0]

    rows = main_table.find_elements(By.XPATH, ".//tr")
    print(f"Table has {len(rows)} <tr> rows")

    if len(rows) < 2:
        raise RuntimeError("Table has too few rows (no data?)")

    # --- Find the real header row (the one with Title / Session/Area / Authors) ---

    header_row = None
    header_idx_in_rows = None

    for i, r in enumerate(rows):
        cells = r.find_elements(By.XPATH, ".//th|.//td")
        cell_texts = [c.text.strip() for c in cells if c.text.strip()]
        joined = " ".join(cell_texts)
        if "Title" in joined and "Session/Area" in joined and "Authors" in joined:
            header_row = r
            header_idx_in_rows = i
            break

    if header_row is None:
        print("WARNING: Could not find header row with Title/Session/Area/Authors; using first row as header.")
        header_row = rows[0]
        header_idx_in_rows = 0

    header_cells = header_row.find_elements(By.XPATH, ".//th|.//td")

    def normalize_header(text: str) -> str:
        return text.strip().lower()

    header_index: Dict[str, int] = {}
    for idx, cell in enumerate(header_cells):
        txt = normalize_header(cell.text)
        if txt:
            header_index[txt] = idx

    print("Header index:", header_index)

    # Column mappings (robust to slight variations)
    title_idx = header_index.get("title")
    session_idx = header_index.get("session/area") or header_index.get("session")
    authors_idx = header_index.get("authors")

    # Affiliation column: pick any header that contains "affiliation"
    affiliation_idx = None
    for k, v in header_index.items():
        if "affiliation" in k:
            affiliation_idx = v
            break

    status_idx = header_index.get("status")

    # Rating + average rating: look for 'rating' and 'avg' substrings
    rating_idx = None
    avg_rating_idx = None
    for k, v in header_index.items():
        if "rating" in k and "avg" not in k:
            rating_idx = v
        if "rating" in k and "avg" in k:
            avg_rating_idx = v

    print(
        "Column indices:",
        "title", title_idx,
        "session", session_idx,
        "authors", authors_idx,
        "affiliation", affiliation_idx,
        "status", status_idx,
        "rating", rating_idx,
        "avg_rating", avg_rating_idx,
    )

    records: List[PaperRow] = []

    # Data rows are all rows after the header row
    data_rows = rows[header_idx_in_rows + 1 :]
    print(f"Found {len(data_rows)} data rows (after header row index {header_idx_in_rows})")

    for r in tqdm(data_rows):
        cells = r.find_elements(By.XPATH, ".//td")
        if not cells:
            continue  # skip non-data rows

        def safe_cell(idx):
            if idx is None:
                return ""
            if idx < 0 or idx >= len(cells):
                return ""
            return cells[idx].text.strip()

        title = safe_cell(title_idx)
        if not title:
            continue

        session_area = safe_cell(session_idx)
        authors = safe_cell(authors_idx)
        status = safe_cell(status_idx)
        rating = safe_cell(rating_idx)
        avg_rating = safe_cell(avg_rating_idx)

        if affiliation_idx is not None and 0 <= affiliation_idx < len(cells):
            affiliation = extract_affiliation_from_cell(cells[affiliation_idx])
        else:
            affiliation = ""

        openreview_urls, neurips_urls, all_urls = extract_urls_from_row(r)

        rec = PaperRow(
            title=title,
            session_area=session_area,
            authors=authors,
            affiliation=affiliation,
            status=status,
            rating=rating,
            avg_rating=avg_rating,
            openreview_urls=";".join(openreview_urls),
            neurips_urls=";".join(neurips_urls),
            all_urls=";".join(all_urls),
        )
        records.append(rec)

    return records


def main():
    driver = setup_driver(headless=False)  # visible so you can click
    try:
        print(f"Opening {URL} ...")
        driver.get(URL)

        # Let the page load JS
        time.sleep(5)

        print(
            "\nPlease now click 'Click to Fetch All' in the browser window "
            "until the status under the table shows all records loaded."
        )
        input("When you're sure all records are loaded, press ENTER here to continue... ")

        # Short extra wait to let any remaining rows render
        time.sleep(5)

        print("Scraping table ...")
        records = scrape_table(driver)

        print(f"Writing {len(records)} rows to {OUTPUT_CSV}")
        if records:
            fieldnames = list(asdict(records[0]).keys())
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in records:
                    writer.writerow(asdict(rec))

        print("Done.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
