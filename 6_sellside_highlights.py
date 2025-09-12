"""
Step 6: Sellside Highlights

Tasks:
- Ingest raw sellside PDFs from `~/Dropbox/MyServerFiles/AutoWeekly/Sellside/{YYYY-MM-DD}`
- Convert PDF -> Markdown, clean, and summarize using existing logic
- Store intermediate artifacts under `data/temp/sellside/{YYYY-MM-DD}`
- Copy PDFs to CDN folder `data/sellside_reports/{YYYY-MM-DD}/<id>.pdf` (same hosting path semantics)
- Emit final highlights markdown to `data/6_final_mds/{YYYY-MM-DD}_sellside_highlights.md`
- Remove raw files after moving them to the CDN folder

Notes:
- Reuses the prompt (moved to `prompt/sellside_summary.txt`)
- Reuses cleaning behavior from `pdfreport/two_clean_markdown.py`
- Uses `models.OneAPI_request` to summarize cleaned markdown (LLM call)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import re
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from markitdown import MarkItDown

from parameters import friday_date
from models import OneAPI_request
def _clean_markdown_contents(raw_text: str) -> str:
    """Replicate the cleaning heuristic formerly in pdfreport.two_clean_markdown.

    - Keep lines up to and including the first "disclosures" (no "see") or
      Chinese "免责声明" (no "阅读").
    """
    lines = raw_text.split("\n")
    out: List[str] = []
    for line in lines:
        out.append(line)
        low = line.lower()
        if ("disclosures" in low and "see" not in low) or ("免责声明" in low and "阅读" not in low):
            break
    return "\n".join(out)


# Paths
RAW_SELLSIDE_DIR = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Sellside" / friday_date
CDN_DIR = Path("data/sellside_reports") / friday_date
TEMP_ROOT = Path("data/temp/sellside") / friday_date
TEMP_MD = TEMP_ROOT / "02_markdown"
TEMP_CLEAN = TEMP_ROOT / "03_cleaned_markdown"
TEMP_SUM = TEMP_ROOT / "04_summary"
FINAL_MDS_DIR = Path("data/6_final_mds")
PROMPT_PATH = Path("prompt/sellside_summary.txt")


def ensure_dirs() -> None:
    for p in [CDN_DIR, TEMP_MD, TEMP_CLEAN, TEMP_SUM, FINAL_MDS_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: failed to read prompt {PROMPT_PATH}: {e}")
        return ""


def extract_file_id(pdf_name: str) -> str:
    """Extract report id from source filename.

    Legacy behavior: take the last '-' separated token without extension.
    Example: '2025-04-14-Report-abc123.pdf' -> 'abc123'
    """
    base = os.path.basename(pdf_name)
    if base.lower().endswith(".pdf"):
        base = base[:-4]
    parts = base.split("-")
    return parts[-1] if parts else base


def move_pdf_to_cdn(raw_pdf: Path) -> Tuple[Path, str]:
    """Copy raw PDF to CDN folder as <id>.pdf and return (cdn_path, id).

    Also deletes the original raw file after successful copy.
    """
    file_id = extract_file_id(raw_pdf.name)
    cdn_pdf = CDN_DIR / f"{file_id}.pdf"
    shutil.copy2(str(raw_pdf), str(cdn_pdf))
    try:
        raw_pdf.unlink()
    except Exception as e:
        print(f"Warning: failed to remove raw file {raw_pdf}: {e}")
    return cdn_pdf, file_id


def pdf_to_markdown(pdf_path: Path, out_md_dir: Path) -> Path | None:
    out_md = out_md_dir / (pdf_path.stem + ".md")
    if out_md.exists():
        print(f"跳过已存在的文件: {out_md.name}")
        return out_md
    try:
        print(f"开始转换: {pdf_path.name}")
        md = MarkItDown()
        result = md.convert(str(pdf_path))
        out_md.write_text(f"{pdf_path.name}\n\n{result.text_content}", encoding="utf-8")
        print(f"完成转换: {pdf_path.name}")
        return out_md
    except Exception as e:
        print(f"转换 {pdf_path.name} 失败: {e}")
        return None


def clean_markdown_file(in_md: Path, out_dir: Path) -> Path | None:
    out_md = out_dir / in_md.name
    try:
        content = in_md.read_text(encoding="utf-8")
        cleaned = _clean_markdown_contents(content)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_md.write_text(cleaned, encoding="utf-8")
        print(f"完成清理: {in_md.name}")
        return out_md
    except Exception as e:
        print(f"清理 {in_md.name} 失败: {e}")
        return None


def summarize_markdown(clean_md: Path, out_dir: Path, prompt: str) -> Path | None:
    out_md = out_dir / clean_md.name
    if out_md.exists():
        print(f"跳过已存在的文件: {out_md.name}")
        return out_md
    try:
        content = clean_md.read_text(encoding="utf-8")
        if not content.strip():
            print(f"空内容，跳过: {clean_md.name}")
            return None
        print(f"开始生成摘要: {clean_md.name}")
        summary = OneAPI_request(prompt, content, model="gemini-2.5-pro")
        if not summary or len(summary.strip()) < 10:
            print(f"生成摘要失败或内容过短: {clean_md.name}")
            return None
        out_md.write_text(summary, encoding="utf-8")
        print(f"完成摘要: {clean_md.name}")
        return out_md
    except Exception as e:
        print(f"摘要失败 {clean_md.name}: {e}")
        return None


def _split_header_and_bullets(summary_text: str) -> Tuple[str, List[str]]:
    """Extract a single bold header line and bullet points from a summary text.

    - If the first non-empty line starts with '**', use it (trim '**').
    - Else if first non-empty line starts with '-' and looks like a title line
      (date + comma + broker + ':'), convert it to header (strip leading '-').
    - Otherwise, use the first non-empty line as header.
    - Bullets keep lines starting with '- ' (or '* ' -> '- '). For other
      non-empty lines, treat as bullets with minimal cleaning.
    """
    lines = [ln.rstrip() for ln in summary_text.strip().split("\n")]
    # find first non-empty
    first_idx = next((i for i, ln in enumerate(lines) if ln.strip()), None)
    header = ""
    bullets: List[str] = []

    if first_idx is None:
        return header, bullets

    first = lines[first_idx].strip()
    rest = lines[first_idx + 1 :]

    def looks_like_title(s: str) -> bool:
        # Rough check: starts with yyyy-mm-dd or yyyy/mm/dd and has a colon
        import re

        return bool(re.match(r"^\s*-?\s*\d{4}[-/]\d{2}[-/]\d{2}.*[:：]", s))

    if first.startswith("**") and first.endswith("**"):
        header = first.strip("*").strip()
    elif first.startswith("- "):
        # Treat leading bullet as header line (strip marker)
        header = first[2:].strip()
    else:
        header = first

    # Collect bullets from the rest (and also from first if not used as header)
    def push_bullet(s: str):
        s = s.strip()
        if not s:
            return
        if s.startswith("- "):
            bullets.append(s)
        elif s.startswith("* "):
            bullets.append("- " + s[2:].strip())
        elif not s.startswith("#") and len(s) > 0:
            cleaned = (
                s.replace("**", "").replace("*", "").replace("#", "").strip()
            )
            if cleaned:
                bullets.append("- " + cleaned)

    # We always treat the first non-empty line as header; do not include it as a bullet

    for ln in rest:
        push_bullet(ln)

    return header, bullets


def _parse_iso_date_from_text(text: str) -> Optional[str]:
    """Find the first date in text and return it as YYYY-MM-DD.

    Handles:
    - 2025-09-10 or 2025/09/10
    - 10 September 2025 / 10 Sep 2025
    - September 10, 2025 / Sep 10 2025
    - 2025年9月10日 (Chinese)
    """
    if not text:
        return None

    # ISO-like: YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r"(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])", text)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        try:
            dt = datetime(int(y), int(mo), int(d))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Chinese: YYYY年MM月DD日
    m = re.search(r"(20\d{2})\s*年\s*(0?[1-9]|1[0-2])\s*月\s*(0?[1-9]|[12]\d|3[01])\s*日?", text)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        try:
            dt = datetime(int(y), int(mo), int(d))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Month name helpers
    MONTHS = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    # D Month YYYY, e.g., 10 September 2025 or 07 Sep 2025
    m = re.search(
        r"\b(0?[1-9]|[12]\d|3[01])\s+([A-Za-z]{3,9})\.?\s+(20\d{2})\b",
        text,
    )
    if m:
        d, mon, y = m.group(1), m.group(2), m.group(3)
        mon_idx = MONTHS.get(mon.lower())
        if mon_idx:
            try:
                dt = datetime(int(y), int(mon_idx), int(d))
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    # Month D, YYYY or Month D YYYY, e.g., September 10, 2025 / Sep 10 2025
    m = re.search(
        r"\b([A-Za-z]{3,9})\.?\s+(0?[1-9]|[12]\d|3[01]),?\s+(20\d{2})\b",
        text,
    )
    if m:
        mon, d, y = m.group(1), m.group(2), m.group(3)
        mon_idx = MONTHS.get(mon.lower())
        if mon_idx:
            try:
                dt = datetime(int(y), int(mon_idx), int(d))
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    return None


def _strip_leading_date_prefix(s: str) -> str:
    """Remove any leading date expression and following punctuation/space from a string."""
    if not s:
        return s
    patterns = [
        r"^\s*(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\s*[,，]?\s*",
        r"^\s*(0?[1-9]|[12]\d|3[01])\s+[A-Za-z]{3,9}\.?\s+(20\d{2})\s*[,，]?\s*",
        r"^\s*[A-Za-z]{3,9}\.?\s+(0?[1-9]|[12]\d|3[01]),?\s+(20\d{2})\s*[,，]?\s*",
        r"^\s*(20\d{2})\s*年\s*(0?[1-9]|1[0-2])\s*月\s*(0?[1-9]|[12]\d|3[01])\s*日?\s*[,，]?\s*",
    ]
    out = s
    for pat in patterns:
        out = re.sub(pat, "", out)
    return out.strip()


def _normalize_header(header: str, summary_text: str, cleaned_text: Optional[str]) -> str:
    """Normalize a header to: YYYY-MM-DD,<Broker>: <Title> with Friday fallback.

    Strategy:
    1) Prefer headers that already start with an ISO date: "YYYY-MM-DD,<Broker>: <Title>".
       - Use that date if within +/-14 days of the folder Friday date; else fallback to Friday date.
    2) Otherwise, try to extract date from header/summary/cleaned and validate +/-14 days; else fallback to Friday.
    3) Derive broker/title from the header around the first colon.
    """
    # Folder's Friday date
    try:
        friday_dt = datetime.strptime(friday_date, "%Y-%m-%d")
    except Exception:
        friday_dt = None

    header = header.strip()

    # Case 1: Header begins with ISO date
    m = re.match(r"^\s*(\d{4}-\d{2}-\d{2})\s*[,，]?\s*([^:：]+?)\s*[:：]\s*(.+)$", header)
    if m:
        cand_date = m.group(1)
        broker = m.group(2).strip().strip(",，")
        title = m.group(3).strip()
        # Validate date vs Friday
        keep_parsed = False
        if friday_dt:
            try:
                cand_dt = datetime.strptime(cand_date, "%Y-%m-%d")
                keep_parsed = abs((cand_dt - friday_dt).days) <= 14
            except Exception:
                keep_parsed = False
        date_iso = cand_date if keep_parsed else friday_date
        return f"{date_iso},{broker}: {title}"

    # Case 2: Generic extraction
    date_iso = _parse_iso_date_from_text(header) or _parse_iso_date_from_text(summary_text)
    if not date_iso and cleaned_text:
        date_iso = _parse_iso_date_from_text(cleaned_text)

    keep_parsed = False
    if date_iso and friday_dt:
        try:
            cand_dt = datetime.strptime(date_iso, "%Y-%m-%d")
            keep_parsed = abs((cand_dt - friday_dt).days) <= 14
        except Exception:
            keep_parsed = False
    if not date_iso or not keep_parsed:
        date_iso = friday_date

    # Split header into left/right by colon
    left = header
    title = ""
    m2 = re.match(r"^(.*?)[\s]*[:：][\s]*(.*)$", header)
    if m2:
        left = m2.group(1)
        title = m2.group(2).strip()

    broker = _strip_leading_date_prefix(left).strip().strip(",，")
    if not title:
        return f"{date_iso},{broker}" if broker else date_iso
    return f"{date_iso},{broker}: {title}"


def build_highlights_md(items: List[Tuple[str, Path]]) -> str:
    """Compose final highlights markdown matching SS/2025-09-05 format."""
    out_lines: List[str] = [f"# Sellside highlights for Week – {friday_date}", ""]

    for file_id, md_path in items:
        try:
            summary = md_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"读取摘要失败 {md_path.name}: {e}")
            continue

        header, bullets = _split_header_and_bullets(summary)

        # Try to load the corresponding cleaned markdown to aid date extraction
        cleaned_text: Optional[str] = None
        try:
            cleaned_path = TEMP_CLEAN / md_path.name
            if cleaned_path.exists():
                cleaned_text = cleaned_path.read_text(encoding="utf-8")
        except Exception:
            cleaned_text = None

        # Normalize header to desired format with Friday fallback
        header = _normalize_header(header, summary, cleaned_text)

        # Section header
        out_lines.append("")  # ensure an empty line before each section
        out_lines.append(f"**{header}**")
        out_lines.append("")

        # Bullets
        if bullets:
            out_lines.extend(bullets)
            out_lines.append("")

        # Link
        out_lines.append(f"[Report Link](https://auto.bda-news.com/{friday_date}/{file_id}.pdf)")
        out_lines.append("")

    return "\n".join(out_lines).rstrip() + "\n"


def translate_highlights_to_english(cn_path: Path, eng_path: Path) -> bool:
    """Translate the final CN highlights to English preserving structure."""
    if not cn_path.exists():
        print(f"CN highlights not found: {cn_path}")
        return False
    if eng_path.exists():
        try:
            cn_mtime = cn_path.stat().st_mtime
            en_mtime = eng_path.stat().st_mtime
            if cn_mtime <= en_mtime:
                print(f"ENG highlights already up-to-date: {eng_path}")
                return True
            else:
                print("CN updated after ENG; regenerating English translation...")
        except Exception:
            # If stat fails, attempt translation anyway
            pass
    try:
        text = cn_path.read_text(encoding="utf-8")
        # Load translation prompt
        tr_prompt = Path("prompt/gemini_translation_prompt.txt").read_text(
            encoding="utf-8"
        )
        translated = OneAPI_request(tr_prompt, text, model="gemini-2.5-pro")
        if not translated or not translated.strip():
            print("Translation failed or empty output.")
            return False
        eng_path.write_text(translated.strip() + "\n", encoding="utf-8")
        print(f"Sellside highlights (ENG) generated: {eng_path}")
        return True
    except Exception as e:
        print(f"Translation error: {e}")
        return False


def _process_one(cdn_pdf_path: str,
                 file_id: str,
                 temp_md_dir: str,
                 temp_clean_dir: str,
                 temp_sum_dir: str,
                 prompt: str) -> Optional[Tuple[str, str]]:
    """Worker to handle one PDF end-to-end using process-based parallelism.

    Returns (file_id, ds_md_path_str) on success, else None.
    """
    try:
        pdf_path = Path(cdn_pdf_path)
        md_path = pdf_to_markdown(pdf_path, Path(temp_md_dir))
        if not md_path:
            return None
        clean_md = clean_markdown_file(md_path, Path(temp_clean_dir))
        if not clean_md:
            return None
        ds_md = summarize_markdown(clean_md, Path(temp_sum_dir), prompt)
        if not ds_md:
            return None
        return (file_id, str(ds_md))
    except Exception as e:
        print(f"子进程处理失败 {cdn_pdf_path}: {e}")
        return None


def main() -> None:
    ensure_dirs()

    if not RAW_SELLSIDE_DIR.exists():
        print(f"Raw sellside folder not found: {RAW_SELLSIDE_DIR}")
        raw_pdfs = []
    else:
        # Discover PDFs
        raw_pdfs = [p for p in RAW_SELLSIDE_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]

    prompt = load_prompt()
    if not prompt.strip():
        print("Warning: prompt is empty; summaries may fail.")

    if not raw_pdfs:
        print(f"No PDFs found in {RAW_SELLSIDE_DIR}")

    # Sort by name similar to legacy: by date prefix if present
    def sort_key(p: Path):
        name = p.name
        if "-" in name:
            parts = name.split("-")[:3]
            return "-".join(parts)
        return name
    raw_pdfs.sort(key=sort_key, reverse=True)

    # Stage 1: Move all raw PDFs into CDN folder (sequential for safety)
    staged: List[Tuple[str, Path]] = []  # (file_id, cdn_pdf_path)
    for pdf in raw_pdfs:
        print(f"Staging to CDN: {pdf.name}")
        cdn_pdf, file_id = move_pdf_to_cdn(pdf)
        staged.append((file_id, cdn_pdf))

    # After staging, attempt to remove the source folder and any leftover files
    try:
        if RAW_SELLSIDE_DIR.exists():
            leftover = list(RAW_SELLSIDE_DIR.iterdir())
            if leftover:
                # Try removing any leftover files (e.g., .DS_Store)
                only_files = all(p.is_file() for p in leftover)
                if only_files:
                    for p in leftover:
                        try:
                            p.unlink()
                        except Exception as e:
                            print(f"Warning: failed to remove leftover file {p}: {e}")
                    # refresh listing
                    leftover = list(RAW_SELLSIDE_DIR.iterdir())
            if not leftover:
                RAW_SELLSIDE_DIR.rmdir()
                print(f"Removed empty source folder: {RAW_SELLSIDE_DIR}")
            else:
                print(f"Skip removing source folder (not empty): {RAW_SELLSIDE_DIR}")
    except Exception as e:
        print(f"Warning: source folder cleanup issue: {e}")

    # Stage 2: Process in parallel with 10 processes
    results: List[Tuple[str, Path]] = []  # (file_id, ds_summary_md_path)
    if not staged:
        # Fallback: if there are existing summaries, rebuild the final markdown
        existing_ds = [p for p in TEMP_SUM.glob("*.md")]
        if existing_ds:
            print(f"No PDFs staged. Found {len(existing_ds)} existing summaries; rebuilding highlights...")
            results = [(p.stem, p) for p in sorted(existing_ds)]
        else:
            # Another fallback: if CDN has PDFs, process them directly
            if CDN_DIR.exists():
                cdn_pdfs = [p for p in CDN_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
                if not cdn_pdfs:
                    print("No PDFs to process after staging.")
                    return
                staged = [(extract_file_id(p.name), p) for p in sorted(cdn_pdfs)]
            else:
                print("No PDFs to process after staging.")
                return

    if staged:
        MAX_PROCESSES = 10
        print(f"Using {MAX_PROCESSES} processes for conversion/clean/summary...")
        with ProcessPoolExecutor(max_workers=MAX_PROCESSES) as ex:
            futs = [
                ex.submit(
                    _process_one,
                    str(cdn_pdf),
                    file_id,
                    str(TEMP_MD),
                    str(TEMP_CLEAN),
                    str(TEMP_SUM),
                    prompt,
                )
                for (file_id, cdn_pdf) in staged
            ]

            for fut in as_completed(futs):
                res = fut.result()
                if res is None:
                    continue
                fid, ds_md_str = res
                results.append((fid, Path(ds_md_str)))

    if not results:
        print("No summaries generated; nothing to write to highlights.")
        return

    # Build and write final highlights
    highlights_md_path = FINAL_MDS_DIR / f"{friday_date}_sellside_highlights.md"
    content = build_highlights_md(results)
    highlights_md_path.write_text(content, encoding="utf-8")
    print(f"Sellside highlights generated: {highlights_md_path}")

    # Translate to English
    eng_md_path = FINAL_MDS_DIR / f"{friday_date}_sellside_highlights_english.md"
    translate_highlights_to_english(highlights_md_path, eng_md_path)


if __name__ == "__main__":
    main()
