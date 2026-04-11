"""
McLemore Library — Book Import Script
Reads PersonalLibrary.xlsx and bulk-loads into Supabase books table.

Usage:
    pip install supabase openpyxl pandas requests
    python import_books.py

Place this script in the same folder as PersonalLibrary.xlsx, or update XLSX_PATH below.
"""

import os, re, json, math, time
import pandas as pd
from supabase import create_client, Client

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SUPABASE_URL      = "https://zfhbetdwmbvuuvwqmnqu.supabase.co"
SUPABASE_KEY      = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpmaGJldGR3bWJ2dXV2d3FtbnF1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTMwNjk3MSwiZXhwIjoyMDkwODgyOTcxfQ.6sxi1fIYNn3_8r0oqnc99212AsgZMzn7IFhQ2FN4MO4"  # service_role key
XLSX_PATH         = os.path.join(os.path.dirname(__file__), "..", "..", "PersonalLibrary.xlsx")
SHEET_NAME        = "Books"
BATCH_SIZE        = 250   # rows per upsert call
# ────────────────────────────────────────────────────────────────────────────────

# Regex patterns (mirrored from build.py)
ASIN_PATTERN      = re.compile(r'/(?:dp|gp/product)/([A-Z0-9]{10})', re.IGNORECASE)
SERIES_PATTERNS   = [
    re.compile(r'^(.+?)\s*[,;]\s*(?:vol(?:ume)?\.?\s*|book\s*|#)(\d+(?:\.\d+)?)\s*$', re.IGNORECASE),
    re.compile(r'^(.+?)\s+#(\d+(?:\.\d+)?)\s*$'),
    re.compile(r'^(.+?)\s+(?:volume|vol\.?|book)\s+(\d+(?:\.\d+)?)\s*$', re.IGNORECASE),
    re.compile(r'^(.+?)\s+(\d+(?:\.\d+)?)\s*$'),
]


def extract_asin(amazon_url: str) -> str | None:
    if not amazon_url or pd.isna(amazon_url):
        return None
    m = ASIN_PATTERN.search(str(amazon_url))
    return m.group(1) if m else None


def make_cover_url(cover_url: str, asin: str | None) -> str | None:
    if cover_url and not pd.isna(cover_url) and str(cover_url).startswith("http"):
        return str(cover_url).strip()
    if asin:
        return f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01.LZZZZZZZ.jpg"
    return None


def parse_series(title: str):
    """Returns (series_name, series_volume) or (None, None)."""
    if not title:
        return None, None
    for pat in SERIES_PATTERNS:
        m = pat.match(title.strip())
        if m:
            try:
                vol = float(m.group(2))
                return m.group(1).strip(), vol
            except (ValueError, IndexError):
                pass
    return None, None


def clean_str(val) -> str | None:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    return s if s else None


def parse_tags(raw: str) -> list[str]:
    if not raw or pd.isna(raw):
        return []
    parts = [t.strip() for t in re.split(r'[,;]', str(raw)) if t.strip()]
    return parts[:20]  # cap at 20 tags


def parse_int(val) -> int | None:
    try:
        n = int(float(val))
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def process_row(row) -> dict:
    title     = clean_str(row.get("Title"))
    author    = clean_str(row.get("Author"))
    amazon_url = clean_str(row.get("Amazon Book URL"))
    asin      = extract_asin(amazon_url)
    cover_raw = clean_str(row.get("CoverURL"))
    cover     = make_cover_url(cover_raw, asin)
    series_name, series_vol = parse_series(title or "")

    return {
        "id":           clean_str(row.get("Book_Id")),
        "title":        title,
        "author":       author,
        "format":       clean_str(row.get("Format")),
        "category":     clean_str(row.get("Category")),
        "pages":        parse_int(row.get("Pages")),
        "tags":         parse_tags(row.get("Tag")),
        "location":     clean_str(row.get("Location")),
        "summary":      clean_str(row.get("Summary")),
        "isbn_13":      clean_str(row.get("ISBN-13")),
        "isbn_10":      clean_str(row.get("ISBN-10")),
        "logos_id":     clean_str(row.get("LogosID")),
        "cover_url":    cover,
        "amazon_url":   amazon_url,
        "asin":         asin,
        "series_name":  series_name,
        "series_volume": series_vol,
    }


def main():
    print(f"📚 McLemore Library Import")
    print(f"   Reading {XLSX_PATH} …")
    df = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME, dtype=str)
    print(f"   {len(df):,} rows found\n")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    records = []
    skipped = 0
    for _, row in df.iterrows():
        rec = process_row(row)
        if not rec["id"] or not rec["title"]:
            skipped += 1
            continue
        records.append(rec)

    print(f"   {len(records):,} valid records  |  {skipped} skipped (missing id/title)\n")

    # Batch upsert
    total_batches = math.ceil(len(records) / BATCH_SIZE)
    inserted = 0
    errors   = 0

    for i in range(0, len(records), BATCH_SIZE):
        batch      = records[i : i + BATCH_SIZE]
        batch_num  = (i // BATCH_SIZE) + 1
        print(f"   Batch {batch_num}/{total_batches} — uploading {len(batch)} records …", end=" ")
        try:
            supabase.table("books").upsert(batch, on_conflict="id").execute()
            inserted += len(batch)
            print("✓")
        except Exception as e:
            errors += len(batch)
            print(f"✗  {e}")
        time.sleep(0.1)  # gentle rate limiting

    print(f"\n{'─'*50}")
    print(f"✅  Import complete")
    print(f"   Inserted/updated : {inserted:,}")
    print(f"   Errors           : {errors:,}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    main()
