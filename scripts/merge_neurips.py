import pandas as pd
import json
import unicodedata
import re


PAPERCOPILOT_CSV = "papercopilot_neurips2025_raw.csv"
NEURIPS_JSON = "neurips_2025.json"
OUTPUT_CSV = "papercopilot_neurips2025_merged_openreview.csv"


def normalize_title(t: str) -> str:
    """Lightweight normalization for grouping NeurIPS events by title."""
    if not isinstance(t, str):
        return ""
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def extract_openreview_id_from_url(url: str) -> str:
    """
    Given a URL like 'https://openreview.net/forum?id=4OsgYD7em5',
    return '4OsgYD7em5'.
    """
    if not isinstance(url, str):
        return ""
    m = re.search(r"[?&]id=([^&]+)", url)
    if m:
        return m.group(1).strip()
    return ""


def extract_openreview_id_pc(openreview_urls: str) -> str:
    """
    PaperCopilot stores OpenReview URLs as a semicolon-separated list.
    Pick the first 'openreview.net/forum' URL and extract its id.
    """
    if not isinstance(openreview_urls, str):
        return ""
    parts = [p.strip() for p in openreview_urls.split(";") if p.strip()]
    for p in parts:
        if "openreview.net/forum" in p:
            return extract_openreview_id_from_url(p)
    return ""


def load_papercopilot(path: str) -> pd.DataFrame:
    pc = pd.read_csv(path)
    pc["openreview_id"] = pc["openreview_urls"].map(extract_openreview_id_pc)
    return pc


def load_neurips_json(path: str) -> pd.DataFrame:
    """
    Load NeurIPS JSON and extract:
      - openreview_id (from paper_url or eventmedia["OpenReview"])
      - abstract
      - session/location/time info, etc.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for ev in data["results"]:
        paper_url = ev.get("paper_url") or ""
        openreview_id = extract_openreview_id_from_url(paper_url)

        # Fallback: look in eventmedia for an OpenReview URL
        if not openreview_id:
            for em in ev.get("eventmedia", []) or []:
                uri = em.get("uri")
                if not uri:
                    continue
                if "openreview.net/forum" in uri:
                    cand = extract_openreview_id_from_url(uri)
                    if cand:
                        openreview_id = cand
                        break

        name = ev.get("name") or ""

        rows.append({
            "neurips_id": ev.get("id"),
            "name": name,
            "norm_title_nj": normalize_title(name),
            "openreview_id": openreview_id,
            "neurips_abstract": ev.get("abstract"),          # <-- NEW
            "neurips_event_type": ev.get("eventtype") or ev.get("event_type"),
            "neurips_session": ev.get("session"),
            "neurips_location": ev.get("room_name"),
            "neurips_starttime": ev.get("starttime"),
            "neurips_endtime": ev.get("endtime"),
            "neurips_virtualsite_url": ev.get("virtualsite_url"),
            "neurips_paper_url": paper_url,
            "neurips_decision": ev.get("decision"),
            "neurips_poster_position": ev.get("poster_position"),
        })

    nj = pd.DataFrame(rows)
    return nj


def choose_group_openreview_id(series: pd.Series) -> str:
    """
    For a group of NeurIPS rows with the same norm_title_nj,
    pick one canonical OpenReview ID and propagate it.

    Heuristic:
      - Prefer IDs that do NOT start with '2025-' (i.e., real OpenReview IDs)
      - If none, fall back to the first non-empty string.
    """
    vals = [v for v in series if isinstance(v, str) and v.strip()]
    if not vals:
        return ""

    # Prefer "clean" IDs (not starting with 2025-)
    for v in vals:
        if not v.startswith("2025-"):
            return v
    # Otherwise just use the first
    return vals[0]


def propagate_openreview_ids(nj: pd.DataFrame) -> pd.DataFrame:
    """
    For each norm_title_nj, propagate a chosen OpenReview ID to all rows
    in that group.
    """
    # Compute group-level canonical IDs
    group_ids = (
        nj.groupby("norm_title_nj")["openreview_id"]
        .apply(choose_group_openreview_id)
        .to_dict()
    )

    # Map canonical IDs back onto all rows
    nj["openreview_id"] = nj["norm_title_nj"].map(group_ids)
    return nj


def main():
    print("Loading PaperCopilot CSV…")
    pc = load_papercopilot(PAPERCOPILOT_CSV)
    print(f"PaperCopilot rows: {len(pc)}")
    print("Non-empty openreview_id in PC:", pc["openreview_id"].astype(bool).sum())

    print("Loading NeurIPS JSON…")
    nj = load_neurips_json(NEURIPS_JSON)
    print(f"NeurIPS event rows: {len(nj)}")
    print("Non-empty openreview_id in NJ BEFORE propagation:", nj["openreview_id"].astype(bool).sum())

    print("Propagating OpenReview IDs across NeurIPS events with same title…")
    nj = propagate_openreview_ids(nj)
    print("Non-empty openreview_id in NJ AFTER propagation:", nj["openreview_id"].astype(bool).sum())

    # Debug for the RL paper
    mask_pc = pc["title"].str.contains("Does Reinforcement Learning Really Incentivize", na=False)
    mask_nj = nj["name"].str.contains("Does Reinforcement Learning Really Incentivize", na=False)
    print("PC openreview_id for RL paper:", pc.loc[mask_pc, "openreview_id"].unique())
    print("NJ openreview_id for RL paper:", nj.loc[mask_nj, "openreview_id"].unique())

    print("Merging with OUTER join on openreview_id (duplicates allowed)…")
    merged = pd.merge(
        pc,
        nj,
        on="openreview_id",
        how="outer",
        suffixes=("_pc", "_nj"),
    )

    has_pc = merged["title"].notna()
    has_nj = merged["name"].notna()
    both = has_pc & has_nj
    print(f"Rows with both PaperCopilot + NeurIPS data: {both.sum()}")

    print(f"Writing merged CSV → {OUTPUT_CSV}")
    merged.to_csv(OUTPUT_CSV, index=False)
    print("Done.")


if __name__ == "__main__":
    main()

