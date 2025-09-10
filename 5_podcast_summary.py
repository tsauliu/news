"""
Step 5: Podcast summary pipeline (CN/ENG)

What it does
- Reads podcast inputs from: ~/Dropbox/MyServerFiles/AutoWeekly/Podcast/{YYYY-MM-DD}
  - Accepts Chinese full markdowns (*.md) and optional Chinese PDFs (*.pdf)
- Builds consolidated podcast summary markdown exactly like legacy format (keeps ALL key takeaways):
  - CN:  data/6_final_mds/{friday_date}_podcast_summary.md
  - ENG: data/6_final_mds/{friday_date}_podcast_summary_english.md
- Generates per-episode PDFs with podcast styling to Deliverables:
  - CN PDFs -> ~/Dropbox/MyServerFiles/AutoWeekly/Deliverable/{YYYY-MM-DD}/CN
  - ENG PDFs -> ~/Dropbox/MyServerFiles/AutoWeekly/Deliverable/{YYYY-MM-DD}/ENG

Notes
- Reuses styling/logic from legacy podcast scripts in Archive (HTML/CSS + translation approach).
- English translation uses the same OneAPI format-preserving prompt as step 4.
- If source directory has Chinese PDFs, they’re copied to CN deliverables.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import List, Tuple

from parameters import friday_date
from models import OneAPI_request


# Constants and paths
FINAL_MDS_DIR = Path("data/6_final_mds")
PROMPT_GEMINI_FULL = Path("prompt/gemini_translation_prompt.txt")


def ensure_dirs() -> None:
    FINAL_MDS_DIR.mkdir(parents=True, exist_ok=True)


def _load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Failed to load prompt {path}: {e}")
        return ""


def sanitize_filename(title: str) -> str:
    """Make a safe filename from a title string."""
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        title = title.replace(ch, "")
    title = title.replace("..", ".").replace(". ", " ")
    title = title.replace("\n", " ").replace("\r", " ")
    title = title.strip()
    if len(title) > 150:
        title = title[:150]
    return title or "podcast"


def extract_episode_info(md_path: Path, language: str = "cn") -> Tuple[str, str]:
    """Extract podcast name and episode title from markdown front lines.

    Heuristics:
    - Look for lines like "- 播客: ..." / "- 节目: ..." or EN equivalents.
    - Fallback to first level-1/2 heading as title.
    """
    podcast_name = ""
    episode_title = ""
    try:
        lines = md_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return podcast_name, episode_title

    if language == "cn":
        podcast_pattern = r"-\s*播客[:：]\s*(.+)"
        episode_pattern = r"-\s*(?:节目|集)[:：]\s*(.+)"
    else:
        podcast_pattern = r"-\s*Podcast[:：]\s*(.+)"
        episode_pattern = r"-\s*Episode[:：]\s*(.+)"

    for ln in lines[:40]:
        m1 = re.search(podcast_pattern, ln)
        if m1 and not podcast_name:
            podcast_name = m1.group(1).strip()
        m2 = re.search(episode_pattern, ln)
        if m2 and not episode_title:
            episode_title = m2.group(1).strip()
        if podcast_name and episode_title:
            break

    # Fallback to first heading
    if not episode_title:
        for ln in lines:
            if ln.startswith("# ") or ln.startswith("## "):
                episode_title = ln.lstrip("# ").strip()
                break

    return podcast_name, episode_title


def _clean_timestamp_links(text: str) -> str:
    """Remove markdown timestamp links and common dividers."""
    # e.g., [(12:34)](http://...) or [(1:02:03)](...)
    text = re.sub(r"\[\([0-9]+(?::[0-9]+){1,2}\)\]\([^)]+\)", "", text)
    # standalone '---' lines
    text = re.sub(r"^---$", "", text, flags=re.MULTILINE)
    # collapse excessive blank lines and spaces
    text = re.sub(r"\n\n+", "\n\n", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def translate_markdown_full(md_text: str) -> str:
    """Translate entire markdown using Gemini format-preserving prompt."""
    if not md_text.strip():
        return ""
    prompt = _load_prompt(PROMPT_GEMINI_FULL)
    # Pre-clean to reduce token usage
    cleaned = _clean_timestamp_links(md_text)
    out = OneAPI_request(prompt, cleaned, model="gemini-2.5-pro")
    return out.strip() if out else ""


def create_podcast_html(md_file: Path, language: str = "en") -> str:
    """Create HTML from podcast markdown file with legacy styling (exact match)."""
    import markdown as md

    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    # Extract episode info
    podcast_name, episode_title = extract_episode_info(md_file, language)

    # Font selection based on language (mirror legacy)
    if language == 'cn':
        font_family = "'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif"
        font_size = "10.5pt"
    else:
        font_family = "'Inter', 'Arial', 'Helvetica', sans-serif"
        font_size = "11pt"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="{'zh-CN' if language == 'cn' else 'en'}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{episode_title if episode_title else md_file.stem}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: {font_family};
                font-size: {font_size};
                line-height: {1.6 if language=='cn' else 1.4};
                color: #2c3e50;
                background: #ffffff;
                margin: 0;
                padding: 2em;
            }}
            
            h1 {{
                font-size: 22pt;
                font-weight: 700;
                margin-top: 0.8em;
                margin-bottom: 0.5em;
                color: #2c3e50;
                border-bottom: 3px solid #2E7D32;
                padding-bottom: 0.3em;
                page-break-after: avoid;
            }}
            
            h1:first-child {{
                margin-top: 0;
            }}
            
            h2 {{
                font-size: 16pt;
                font-weight: 600;
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #34495e;
                border-left: 4px solid #43A047;
                padding-left: 0.5em;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 13pt;
                font-weight: 600;
                margin-top: 0.8em;
                margin-bottom: 0.4em;
                color: #2c3e50;
                page-break-after: avoid;
            }}
            
            p {{
                margin-bottom: 0.6em;
                text-align: justify;
                text-justify: inter-word;
            }}
            
            ul, ol {{
                margin: 0.4em 0 0.8em 2em;
                padding: 0;
            }}
            
            li {{
                margin-bottom: 0.4em;
                line-height: {1.6 if language=='cn' else 1.4};
            }}
            
            ul li {{
                list-style-type: none;
                position: relative;
                padding-left: 1.5em;
            }}
            
            ul li:before {{
                content: "•";
                position: absolute;
                left: 0;
                color: #43A047;
                font-weight: bold;
                font-size: 1.2em;
            }}
            
            a {{
                color: #3498db;
                text-decoration: none;
                border-bottom: 1px dotted #3498db;
            }}
            
            a:hover {{
                color: #2980b9;
                border-bottom-style: solid;
            }}
            
            em {{
                font-style: italic;
                color: #7f8c8d;
            }}
            
            strong {{
                font-weight: 600;
                color: #2c3e50;
            }}
            
            blockquote {{
                margin: 0.5em 0;
                padding: 0.8em;
                background: #f5f5f5;
                border-left: 4px solid #66BB6A;
                font-style: italic;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }}
            
            th, td {{
                padding: 0.5em;
                border: 1px solid #ddd;
                text-align: left;
            }}
            
            th {{
                background-color: #f5f5f5;
                font-weight: 600;
            }}
            
            @page {{
                size: A4;
                margin: 2cm 1.5cm;
                
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                    font-family: {font_family};
                }}
                
                @top-right {{
                    content: "{podcast_name if podcast_name else ('播客记录' if language == 'cn' else 'Podcast Transcript')}";
                    font-size: 9pt;
                    color: #95a5a6;
                    font-family: {font_family};
                }}
            }}
            
            @media print {{
                body {{ padding: 0; }}
                h1 {{ page-break-before: auto; }}
                h2 {{ page-break-after: avoid; }}
            }}
        </style>
    </head>
    <body>
    """

    # Add episode title header (legacy)
    if episode_title:
        html_content += f"""
        <div style="text-align: center; margin-bottom: 1.5em; padding: 0.8em; border-bottom: 2px solid #2E7D32;">
            <h1 style="margin: 0; font-size: 22pt; color: #2c3e50; font-weight: 600;">{episode_title}</h1>
            <p style="margin-top: 0.3em; font-size: {font_size}; color: #7f8c8d;">{podcast_name}</p>
        </div>
        """

    # Convert markdown with legacy extensions (including tables)
    md_converter = md.Markdown(extensions=['extra', 'nl2br', 'sane_lists', 'tables'])
    html_from_md = md_converter.convert(markdown_text)

    html_content += html_from_md
    html_content += """
    </body>
    </html>
    """
    return html_content


def render_pdf(html: str, out_path: Path) -> bool:
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        print(f"PDF dependencies missing: {e}")
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(out_path, stylesheets=[CSS(string='@page { size: A4; margin: 2cm 1.5cm; }')])
    return True


def collect_podcast_files(source_dir: Path) -> Tuple[List[Path], List[Path]]:
    """Return (markdown_files, pdf_files) under the source directory."""
    mds = sorted(source_dir.glob("*.md"))
    pdfs = sorted(source_dir.glob("*.pdf"))
    return mds, pdfs


def build_consolidated_podcast_summary(md_files: List[Path]) -> str:
    """Build consolidated podcast summary exactly like legacy format, preserving ALL takeaways.

    Expected episode input format (per file):
    - '# Info' section with '- 播客:' / '- 节目:' or EN equivalents
    - '# Summary' section as a paragraph
    - '# Takeaways' (or '# Key Takeaways') section with bullet lines

    Consolidated output format (per episode):
    ## [Podcast Name] Episode Title
    <one-line summary>
    - <takeaway 1>
    - <takeaway 2>
    ... (all bullet points)
    """
    out: List[str] = [f"# Podcast Summary – {friday_date}", ""]

    def parse_episode(md_path: Path) -> Tuple[str, str, str, List[str]]:
        podcast_name = ""
        episode_title = ""
        summary_lines: List[str] = []
        takeaways: List[str] = []

        try:
            lines = md_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return podcast_name, episode_title, "", takeaways

        in_info = in_summary = in_takeaways = False
        for ln in lines:
            stripped = ln.strip()
            # Section toggles (support both '# ' and '## ')
            if stripped.lower() in {"# info", "## info"}:
                in_info, in_summary, in_takeaways = True, False, False
                continue
            if stripped.lower() in {"# summary", "## summary"}:
                in_info, in_summary, in_takeaways = False, True, False
                continue
            if stripped.lower() in {"# takeaways", "## takeaways", "# key takeaways", "## key takeaways"}:
                in_info, in_summary, in_takeaways = False, False, True
                continue
            if stripped.startswith("# ") or stripped.startswith("## "):
                in_info = in_summary = in_takeaways = False
                continue

            if in_info:
                if stripped.startswith("- "):
                    info = stripped[2:].strip()
                    if info.startswith("播客:") or info.startswith("Podcast:"):
                        podcast_name = info.split(":", 1)[1].strip()
                    elif info.startswith("节目:") or info.startswith("集:") or info.startswith("Episode:"):
                        episode_title = info.split(":", 1)[1].strip()
            elif in_summary:
                if stripped:
                    summary_lines.append(stripped)
            elif in_takeaways:
                if stripped.startswith("- ") or stripped.startswith("* "):
                    # keep full text as a takeaway (remove leading marker)
                    bullet = stripped[1:].lstrip("*-").strip()
                    if bullet:
                        takeaways.append(bullet)

        # Fallbacks
        if not (podcast_name and episode_title):
            pn, et = extract_episode_info(md_path, language="cn")
            podcast_name = podcast_name or pn
            episode_title = episode_title or et or md_path.stem

        # Single-line summary
        summary = " ".join(summary_lines).strip()
        return podcast_name, episode_title, summary, takeaways

    for md in md_files:
        pn, et, summary, takeaways = parse_episode(md)
        # compose header
        if pn:
            out.append(f"## [{pn}] {et}")
        else:
            out.append(f"## {et}")
        if summary:
            out.append("")
            out.append(summary)
        out.append("")
        for tk in takeaways:
            out.append(f"- {tk}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    # Resolve source and destination paths
    source_dir = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Podcast" / friday_date
    deliver_base = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Deliverable" / friday_date
    deliver_cn = deliver_base / "CN"
    deliver_en = deliver_base / "ENG"

    print(f"Podcast source: {source_dir}")
    ensure_dirs()

    if not source_dir.exists():
        print("No podcast directory found for date; nothing to do.")
        return

    md_files, pdf_files = collect_podcast_files(source_dir)
    if not md_files and not pdf_files:
        print("No podcast markdown or PDFs found; nothing to do.")
        return

    # 1) Build consolidated podcast summary (CN + ENG), preserving ALL takeaways
    if md_files:
        cn_summary = build_consolidated_podcast_summary(md_files)
        cn_summary_path = FINAL_MDS_DIR / f"{friday_date}_podcast_summary.md"
        cn_summary_path.write_text(cn_summary, encoding="utf-8")
        print(f"Saved CN podcast summary: {cn_summary_path}")

        en_summary = translate_markdown_full(cn_summary)
        en_summary_path = FINAL_MDS_DIR / f"{friday_date}_podcast_summary_english.md"
        en_summary_path.write_text(en_summary or "", encoding="utf-8")
        print(f"Saved ENG podcast summary: {en_summary_path}")

    # 2) Generate CN PDFs from Chinese markdowns
    for md in md_files:
        podcast_name, episode_title = extract_episode_info(md, language="cn")
        base_name = sanitize_filename(episode_title or md.stem)
        out_name = f"Podcast - {base_name}.pdf"
        out_path = deliver_cn / out_name
        try:
            # Validate readable file
            _ = md.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Skip CN PDF for {md.name}: {e}")
            continue
        html = create_podcast_html(md, language="cn")
        ok = render_pdf(html, out_path)
        if ok:
            print(f"CN PDF: {out_path}")

    # 3) Translate to English and generate ENG PDFs
    eng_md_dir = Path("data") / "podcast_eng" / friday_date
    eng_md_dir.mkdir(parents=True, exist_ok=True)
    for md in md_files:
        podcast_name, episode_title = extract_episode_info(md, language="cn")
        base_name = sanitize_filename(episode_title or md.stem)
        out_name = f"Podcast - {base_name}_ENG.pdf"
        out_path = deliver_en / out_name

        try:
            cn_text = md.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Skip ENG PDF for {md.name} (read failed): {e}")
            continue

        en_text = translate_markdown_full(cn_text)
        # Persist translated markdown (optional helper)
        eng_md_path = eng_md_dir / md.name
        eng_md_path.write_text(en_text or "", encoding="utf-8")

        html = create_podcast_html(eng_md_path, language="en")
        ok = render_pdf(html, out_path)
        if ok:
            print(f"ENG PDF: {out_path}")

    # 4) Copy any provided Chinese PDFs straight to CN deliverables
    for pdf in pdf_files:
        dest = deliver_cn / pdf.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            # avoid overwriting existing generated files
            print(f"Skip copy (exists): {dest.name}")
            continue
        shutil.copy2(pdf, dest)
        print(f"Copied source PDF -> {dest}")


if __name__ == "__main__":
    main()
