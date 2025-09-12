"""
Upload historical sellside PDFs under data/sellside_reports to Google Cloud Storage
and validate folder layout.

Expected layout:
- data/sellside_reports/{YYYY-MM-DD}/{id}.pdf

Usage:
  python script/upload_history_to_gcs.py --dry-run
  PUBLIC_URL_BASE=http://auto.bda-news.com GCS_BUCKET=bda_auto_pdf_reports \
  python script/upload_history_to_gcs.py --upload

Notes:
- Requires google-cloud-storage installed and GCP credentials (ADC or service account).
- Does not modify or delete files; only uploads and logs anomalies.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure repo root is on sys.path to import google_cloud module
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from google_cloud import upload_to_gcs


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "data" / "sellside_reports"


DATE_DIR_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")


def find_pdfs() -> List[Tuple[str, Path]]:
    items: List[Tuple[str, Path]] = []
    if not BASE_DIR.exists():
        print(f"Not found: {BASE_DIR}")
        return items

    for child in sorted(BASE_DIR.iterdir()):
        if not child.is_dir():
            # Skip non-dir items (e.g., stray scripts)
            print(f"Skip non-folder item in sellside root: {child}")
            continue
        if not DATE_DIR_RE.match(child.name):
            print(f"Skip non-date folder: {child}")
            continue

        for pdf in sorted(child.glob("*.pdf")):
            items.append((child.name, pdf))
    return items


def main(argv: List[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="List files and URLs only")
    ap.add_argument("--upload", action="store_true", help="Upload files to GCS")
    args = ap.parse_args(argv)

    pairs = find_pdfs()
    if not pairs:
        print("No PDFs found under data/sellside_reports.")
        return 0

    public_base = os.getenv("PUBLIC_URL_BASE") or os.getenv("GCS_URL_BASE") or "https://auto.bda-news.com"
    bucket = os.getenv("GCS_BUCKET") or os.getenv("GCS_BUCKET_NAME") or "bda_auto_pdf_reports"
    print(f"Target bucket: {bucket}")
    print(f"Public base: {public_base}")

    total = len(pairs)
    print(f"Found {total} PDFs to process.")

    for idx, (date_str, pdf_path) in enumerate(pairs, 1):
        file_id = pdf_path.stem
        blob = f"{date_str}/{file_id}.pdf"
        expect_url = (
            f"{public_base.rstrip('/')}/{bucket}/{blob}"
            if "storage.googleapis.com" in public_base
            else f"{public_base.rstrip('/')}/{blob}"
        )
        print(f"[{idx}/{total}] {pdf_path} -> {blob}")
        print(f"  expected URL: {expect_url}")

        if args.dry_run and not args.upload:
            continue

        if args.upload:
            try:
                url = upload_to_gcs(
                    pdf_path,
                    blob_path=blob,
                    content_type="application/pdf",
                )
                print(f"  uploaded: {url}")
            except Exception as e:
                print(f"  upload failed: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
