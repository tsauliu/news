"""
Step 4: Generate weekly news summary markdowns (CN/ENG) and PDFs.

Outputs:
- Markdown (CN): `data/6_final_mds/{friday_date}_key_takeaway.md`
- Markdown (CN): `data/6_final_mds/{friday_date}_detailed_news.md`
- Markdown (ENG): `data/6_final_mds/{friday_date}_key_takeaway_english.md`
- Markdown (ENG): `data/6_final_mds/{friday_date}_detailed_news_english.md`
- PDFs saved directly to `~/Dropbox/MyServerFiles/AutoWeekly/Deliverable/{YYYY-MM-DD}/{CN|ENG}`

Notes:
- No sellside highlights, no podcast handling (per plan).
- Reuses step-3 outputs:
  - Combined per-sector summary: `data/5_summary_mds/{friday_date}_summary.md`
  - Combined detailed news:     `data/4_combined_mds/{friday_date}_combined_news.md`
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import List

from parameters import friday_date, sector_list
from utils import archive_existing_in_target
from models import OneAPI_request


# Input locations from previous steps
SUMMARY_MD = f"data/5_summary_mds/{friday_date}_summary.md"
COMBINED_NEWS_MD = f"data/4_combined_mds/{friday_date}_combined_news.md"

# Output locations for this step
FINAL_MDS_DIR = Path("data/6_final_mds")


def ensure_dirs() -> None:
    FINAL_MDS_DIR.mkdir(parents=True, exist_ok=True)
    # Archive old outputs (keep current date)
    archive_existing_in_target(str(FINAL_MDS_DIR), exclude_contains=[friday_date])


def load_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Missing input: {path}")
        return ""


def build_key_takeaway_md(summary_md_text: str) -> str:
    """Build key_takeaway markdown matching original logic in Archive/5a.

    - Keep lines starting with '##' as section headers
    - For other header lines starting with '#', if length > 10, convert to bullets
    - Ignore non-header lines
    """
    if not summary_md_text.strip():
        return ""

    lines = summary_md_text.strip().split("\n")
    out_lines: List[str] = [f"# Key News takeaway for Week – {friday_date}", ""]

    for line in lines:
        if line.startswith("##"):
            out_lines.append("")
            out_lines.append(line)
            out_lines.append("")
        elif line.startswith("#") and len(line) > 10:
            cleaned = (
                line.replace("*", "")
                .replace("**", "")
                .replace("- ", "")
                .replace("#", "")
                .strip()
            )
            out_lines.append(f"- {cleaned}")

    return "\n".join(out_lines).rstrip() + "\n"


def build_detailed_news_md(combined_md_text: str) -> str:
    """Create detailed news markdown grouped by sector from combined article MD.

    Expects fields in the combined MD: title/link/sector/author/date/content.
    Filters out '其他' sector. Orders by configured sector_list.
    """
    if not combined_md_text.strip():
        return ""

    # Lightweight parse of key-value lines
    items = []
    current = {}
    for ln in combined_md_text.splitlines():
        if ln.startswith("title: "):
            if current:
                items.append(current)
            current = {"title": ln[7:].strip()}
        elif ln.startswith("link: ") and current:
            current["link"] = ln[6:].strip()
        elif ln.startswith("sector: ") and current:
            # take first part before any delimiter like '、'
            current["sector"] = ln[8:].strip().split("、")[0]
        elif ln.startswith("author: ") and current:
            current["author"] = ln[8:].strip()
        elif ln.startswith("date: ") and current:
            current["date"] = ln[6:].strip()
        elif ln.startswith("content: ") and current:
            current["content"] = ln[9:].strip()
    if current:
        items.append(current)

    # Filter and sort items by sector order then date(desc lexicographically)
    items = [it for it in items if it.get("sector") and it["sector"] != "其他"]

    # Build output
    out: List[str] = [f"# Detailed News for Week – {friday_date}", ""]
    for sector in sector_list:
        sector_items = [it for it in items if it.get("sector") == sector]
        if not sector_items:
            continue
        # naive date-desc sort; format expected YYYY-MM-DD
        sector_items.sort(key=lambda d: d.get("date", ""), reverse=True)

        out.append(f"## {sector}")
        out.append("")
        for it in sector_items:
            title = it.get("title", "Untitled")
            out.append(f"### {title}")
            out.append("")
            link = it.get("link")
            if link:
                out.append(f"[原文链接]({link})")
                out.append("")
            meta_parts = []
            if it.get("date"):
                meta_parts.append(it["date"])
            if it.get("author"):
                meta_parts.append(it["author"])
            if meta_parts:
                out.append(f"*{' - '.join(meta_parts)}*")
                out.append("")
            if it.get("content"):
                out.append(it["content"])
                out.append("")

    return "\n".join(out).strip() + "\n"


PROMPT_GEMINI_FULL = Path("prompt/gemini_translation_prompt.txt")
PROMPT_LINE = Path("prompt/line_translation_prompt.txt")


def _load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Failed to load prompt {path}: {e}")
        return ""


def translate_file_with_gemini_full(md_text: str) -> str:
    """Full-file translation using the original Gemini prompt (format-preserving)."""
    if not md_text.strip():
        return ""
    prompt = _load_prompt(PROMPT_GEMINI_FULL)
    translated = OneAPI_request(prompt, md_text, model="gemini-2.5-pro")
    return translated.strip() if translated else ""


def translate_line_with_gemini(text: str) -> str:
    """Line-level translation using gemini-2.5-flash and the original line prompt."""
    if not text or len(text.strip()) < 1:
        return text
    prompt = _load_prompt(PROMPT_LINE)
    translated = OneAPI_request(prompt, text, model="gemini-2.5-flash")
    return translated.strip() if translated else text


def translate_detailed_news_by_news(input_path: Path, output_path: Path, max_workers: int = 50) -> bool:
    """Translate detailed news markdown chunk-by-chunk (one news item per request).

    - Uses `gemini-2.5-flash` with the original Gemini formatting prompt.
    - Retains original markdown structure while reducing API calls.
    """
    if not input_path.exists():
        print(f"Warning: File {input_path} not found, skipping...")
        return False

    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    pieces: List[dict] = []  # [{type: 'raw'|'sector'|'news', 'text': str}]
    current_news: List[str] | None = None

    def flush_news():
        nonlocal current_news
        if current_news is not None:
            chunk = "\n".join(current_news).strip()
            if chunk:
                pieces.append({"type": "news", "text": chunk})
            current_news = None

    for ln in lines:
        if ln.startswith("## "):
            flush_news()
            pieces.append({"type": "sector", "text": ln})
        elif ln.startswith("### "):
            flush_news()
            current_news = [ln]
        else:
            if current_news is not None:
                current_news.append(ln)
            else:
                # raw lines (top header, blank lines, etc.)
                pieces.append({"type": "raw", "text": ln})
    flush_news()

    # Prepare concurrent translation for news chunks
    from concurrent.futures import ThreadPoolExecutor, as_completed

    prompt = _load_prompt(PROMPT_GEMINI_FULL)

    def translate_news_chunk(md_chunk: str) -> str:
        out = OneAPI_request(prompt, md_chunk, model="gemini-2.5-flash")
        return out.strip() if out else md_chunk

    translated_news: List[str] = []
    # Map piece index to future for reconstruction
    news_indices = [i for i, p in enumerate(pieces) if p["type"] == "news"]
    results_map = {}
    if news_indices:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(translate_news_chunk, pieces[i]["text"]): i for i in news_indices}
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results_map[idx] = fut.result()
                except Exception as e:
                    print(f"Chunk translation failed at piece {idx}: {e}")
                    results_map[idx] = pieces[idx]["text"]

    # Reconstruct document
    out_lines: List[str] = []
    for i, piece in enumerate(pieces):
        typ = piece["type"]
        if typ == "raw":
            out_lines.append(piece["text"])
        elif typ == "sector":
            # Translate header text only
            header_text = piece["text"][2:].strip('# ').strip()
            translated = translate_line_with_gemini(header_text)
            out_lines.append(f"## {translated if translated else header_text}")
            out_lines.append("")
        elif typ == "news":
            translated_chunk = results_map.get(i, piece["text"])  # default to original on failure
            out_lines.append(translated_chunk)
            out_lines.append("")

    output_path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    return True


def write_text(path: Path, content: str) -> None:
    if not content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_cn_html() -> str:
    """Match original CN PDF HTML format (Archive/5b) without sellside section."""
    import markdown
    # Input markdown files
    input_dir = Path('data/6_final_mds')
    takeaway_md = input_dir / f'{friday_date}_key_takeaway.md'
    detailed_md = input_dir / f'{friday_date}_detailed_news.md'

    html_content: List[str] = []
    html_content.append(
        (
            """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>自动驾驶AI新闻摘要 - {friday_date}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', Arial, sans-serif; font-size: 11pt; line-height: 1.3; color: #2c3e50; background: #ffffff; margin: 0; padding: 0; }
            .content { padding: 0; margin: 0; padding-top: 0; }
            h1 { font-size: 22pt; font-weight: 700; margin-top: 0.8em; margin-bottom: 0.3em; color: #2c3e50; border-bottom: 3px solid #2E7D32; padding-bottom: 0.2em; page-break-after: avoid; }
            .section-break h1:first-child { margin-top: 0.8em; }
            h2 { font-size: 16pt; font-weight: 600; margin-top: 0.5em; margin-bottom: 0.3em; color: #34495e; border-left: 4px solid #43A047; padding-left: 0.5em; page-break-after: avoid; }
            h3 { font-size: 13pt; font-weight: 600; margin-top: 0.4em; margin-bottom: 0.2em; color: #2c3e50; page-break-after: avoid; }
            p { margin-bottom: 0.5em; text-align: justify; text-justify: inter-word; }
            ul, ol { margin: 0.3em 0 0.5em 2em; padding: 0; }
            li { margin-bottom: 0.3em; line-height: 1.3; }
            ul li { list-style-type: none; position: relative; padding-left: 1.5em; }
            ul li:before { content: "•"; position: absolute; left: 0; color: #43A047; font-weight: bold; font-size: 1.2em; }
            a { color: #3498db; text-decoration: none; border-bottom: 1px dotted #3498db; }
            a:hover { color: #2980b9; border-bottom-style: solid; }
            em { font-style: italic; color: #7f8c8d; }
            strong { font-weight: 600; color: #2c3e50; }
            blockquote { margin: 0.3em 0; padding: 0.5em; background: #f5f5f5; border-left: 4px solid #66BB6A; font-style: italic; }
            .section-break { page-break-before: always; padding-top: 0; margin-top: 0; }
            .news-item { margin-bottom: 0.5em; padding-bottom: 0.3em; border-bottom: 1px dashed #bdc3c7; }
            .news-item:last-child { border-bottom: none; }
            .news-meta { font-size: 10pt; color: #7f8c8d; font-style: italic; margin-bottom: 0.2em; }
            .highlight-box { background: #f9f9f9; border: 2px solid #4CAF50; border-radius: 8px; padding: 0.5em; margin: 0.3em 0; }
            @page { size: A4; margin: 2cm 1cm; @bottom-center { content: counter(page); font-size: 10pt; color: #7f8c8d; font-family: 'Noto Sans SC', sans-serif; } @top-right { content: "BDA Autonomous Driving New Update"; font-size: 9pt; color: #95a5a6; font-family: 'Noto Sans SC', sans-serif; } }
            @media print { .cover-page { height: 100vh; } .section-break { page-break-before: always; } }
        </style>
    </head>
    <body>
            """
        ).replace('{friday_date}', friday_date)
    )

    sections = [
        ('takeaway', takeaway_md, '本周要闻提炼'),
        ('detailed', detailed_md, '详细新闻内容'),
    ]

    for section_id, md_file, _ in sections:
        if not md_file.exists():
            print(f"Warning: {md_file} not found, skipping...")
            continue
        html_content.append(
            f'<div class="{"content" if section_id == "takeaway" else "section-break content"}" id="{section_id}">'
        )
        markdown_text = md_file.read_text(encoding='utf-8')
        md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        html_from_md = md_converter.convert(markdown_text)
        if section_id == 'detailed':
            html_from_md = html_from_md.replace('<h3>', '<div class="news-item"><h3>')
            html_from_md = html_from_md.replace('<h2>', '</div><h2>')
            html_from_md = html_from_md + '</div>'
            html_from_md = html_from_md.replace('</div><h2>', '<h2>')
        html_content.append(html_from_md)
        html_content.append('</div>')

    html_content.append('</body></html>')
    return '\n'.join(html_content)


def create_eng_html() -> str:
    """Match original ENG PDF HTML format (Archive/5c) without sellside section."""
    import markdown
    input_dir = Path('data/6_final_mds')
    takeaway_eng_md = input_dir / f'{friday_date}_key_takeaway_english.md'
    detailed_eng_md = input_dir / f'{friday_date}_detailed_news_english.md'

    html_content: List[str] = []
    html_content.append(
        (
            """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Autonomous Driving AI News Summary - {friday_date}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Inter', 'Arial', 'Helvetica', sans-serif; font-size: 11pt; line-height: 1.3; color: #2c3e50; background: #ffffff; margin: 0; padding: 0; }
            .content { padding: 0; margin: 0; padding-top: 0; }
            h1 { font-size: 22pt; font-weight: 700; margin-top: 0.8em; margin-bottom: 0.3em; color: #2c3e50; border-bottom: 3px solid #2E7D32; padding-bottom: 0.2em; page-break-after: avoid; }
            .section-break h1:first-child { margin-top: 0.8em; }
            h2 { font-size: 16pt; font-weight: 600; margin-top: 0.5em; margin-bottom: 0.3em; color: #34495e; border-left: 4px solid #43A047; padding-left: 0.5em; page-break-after: avoid; }
            h3 { font-size: 13pt; font-weight: 600; margin-top: 0.4em; margin-bottom: 0.2em; color: #2c3e50; page-break-after: avoid; }
            p { margin-bottom: 0.5em; text-align: justify; text-justify: inter-word; }
            ul, ol { margin: 0.3em 0 0.5em 2em; padding: 0; }
            li { margin-bottom: 0.3em; line-height: 1.3; }
            ul li { list-style-type: none; position: relative; padding-left: 1.5em; }
            ul li:before { content: "•"; position: absolute; left: 0; color: #43A047; font-weight: bold; font-size: 1.2em; }
            a { color: #3498db; text-decoration: none; border-bottom: 1px dotted #3498db; }
            a:hover { color: #2980b9; border-bottom-style: solid; }
            em { font-style: italic; color: #7f8c8d; }
            strong { font-weight: 600; color: #2c3e50; }
            blockquote { margin: 0.3em 0; padding: 0.5em; background: #f5f5f5; border-left: 4px solid #66BB6A; font-style: italic; }
            .section-break { page-break-before: always; padding-top: 0; margin-top: 0; }
            .news-item { margin-bottom: 0.5em; padding-bottom: 0.3em; border-bottom: 1px dashed #bdc3c7; }
            .news-item:last-child { border-bottom: none; }
            .news-meta { font-size: 10pt; color: #7f8c8d; font-style: italic; margin-bottom: 0.2em; }
            .highlight-box { background: #f9f9f9; border: 2px solid #4CAF50; border-radius: 8px; padding: 0.5em; margin: 0.3em 0; }
            @page { size: A4; margin: 2cm 1cm; @bottom-center { content: counter(page); font-size: 10pt; color: #7f8c8d; font-family: 'Inter', sans-serif; } @top-right { content: "BDA Autonomous Driving New Update"; font-size: 9pt; color: #95a5a6; font-family: 'Inter', sans-serif; } }
            @media print { .cover-page { height: 100vh; } .section-break { page-break-before: always; } }
        </style>
    </head>
    <body>
            """
        ).replace('{friday_date}', friday_date)
    )

    sections = [
        ('takeaway', takeaway_eng_md, 'Key News Takeaway'),
        ('detailed', detailed_eng_md, 'Detailed News'),
    ]

    for section_id, md_file, _ in sections:
        if not md_file.exists():
            print(f"Warning: {md_file} not found, skipping...")
            continue
        html_content.append(
            f'<div class="{"content" if section_id == "takeaway" else "section-break content"}" id="{section_id}">'
        )
        markdown_text = md_file.read_text(encoding='utf-8')
        md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        html_from_md = md_converter.convert(markdown_text)
        if section_id == 'detailed':
            html_from_md = html_from_md.replace('<h3>', '<div class="news-item"><h3>')
            html_from_md = html_from_md.replace('<h2>', '</div><h2>')
            html_from_md = html_from_md + '</div>'
            html_from_md = html_from_md.replace('</div><h2>', '<h2>')
        html_content.append(html_from_md)
        html_content.append('</div>')

    html_content.append('</body></html>')
    return '\n'.join(html_content)


def render_pdf(html_content: str, lang: str) -> Path | None:
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        print(f"PDF dependencies missing: {e}")
        return None

    out_name = (
        f"Autonomous Driving AI News Summary {friday_date.replace('-', ' ')}"
        + ("_ENG" if lang == "ENG" else "")
        + ".pdf"
    )
    deliver_dir = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Deliverable" / friday_date / ("CN" if lang == "CN" else "ENG")
    deliver_dir.mkdir(parents=True, exist_ok=True)
    out_path = deliver_dir / out_name
    HTML(string=html_content).write_pdf(out_path, stylesheets=[CSS(string='@page { size: A4; margin: 2cm 1cm; }')])
    return out_path


# No copy step needed; PDFs are written directly to deliverable folders.


def main() -> None:
    ensure_dirs()

    summary_text = load_text(SUMMARY_MD)
    combined_text = load_text(COMBINED_NEWS_MD)
    if not summary_text or not combined_text:
        print("Missing inputs from previous steps; aborting step 4.")
        return

    # Generate CN markdowns
    cn_takeaway = build_key_takeaway_md(summary_text)
    cn_detailed = build_detailed_news_md(combined_text)

    cn_takeaway_path = FINAL_MDS_DIR / f"{friday_date}_key_takeaway.md"
    cn_detailed_path = FINAL_MDS_DIR / f"{friday_date}_detailed_news.md"
    write_text(cn_takeaway_path, cn_takeaway)
    write_text(cn_detailed_path, cn_detailed)
    print(f"Saved CN markdowns to {FINAL_MDS_DIR}")

    # Translate to ENG using original prompts
    eng_takeaway = translate_file_with_gemini_full(cn_takeaway)
    # Detailed: line-by-line with gemini-2.5-flash (50 workers)
    eng_detailed = None  # will be written by line-by-line function

    eng_takeaway_path = FINAL_MDS_DIR / f"{friday_date}_key_takeaway_english.md"
    eng_detailed_path = FINAL_MDS_DIR / f"{friday_date}_detailed_news_english.md"
    write_text(eng_takeaway_path, eng_takeaway)
    # news-by-news translation writes directly to file
    translate_detailed_news_by_news(cn_detailed_path, eng_detailed_path, max_workers=50)
    print(f"Saved ENG markdowns to {FINAL_MDS_DIR}")

    # Render PDFs with original formatting
    cn_html = create_cn_html()
    cn_pdf = render_pdf(cn_html, lang="CN")
    if cn_pdf:
        print(f"CN PDF: {cn_pdf}")

    eng_html = create_eng_html()
    eng_pdf = render_pdf(eng_html, lang="ENG")
    if eng_pdf:
        print(f"ENG PDF: {eng_pdf}")


if __name__ == "__main__":
    main()
