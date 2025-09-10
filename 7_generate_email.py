"""
Step 7: Generate weekly email (CN/ENG) as MHT

Requirements:
- Inputs: `data/6_final_mds/{date}_*.md`
- Reuse logic/format from Archive email generators (exact structure)
- Work without sellside or podcast (skip sections when files missing)
- Output MHTs to `~/Dropbox/MyServerFiles/AutoWeekly/Deliverable/{YYYY-MM-DD}/{CN|ENG}`

CLI:
  python 7_generate_email.py [--date YYYY-MM-DD] [--cn-only|--eng-only]
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple

from parameters import friday_date


# ---------- File helpers ----------

DATA_DIR = Path("data/6_final_mds")


def read_text_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


# ---------- Podcast parsing (from Archive with light guards) ----------

def parse_consolidated_podcast_summary(file_path: Path) -> List[Tuple[str, str, str, List[str]]]:
    """Parse consolidated podcast summary markdown.

    Returns a list of tuples: (podcast_name, episode_title, summary, bullets)
    """
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []
    lines = content.split("\n")

    podcasts: List[Tuple[str, str, str, List[str]]] = []
    current: dict | None = None
    current_summary = ""
    current_bullets: List[str] = []
    in_summary_paragraph = False

    for line in lines:
        if line.startswith("## "):
            if current:
                podcasts.append((current.get("name", ""), current.get("title", ""), current_summary, current_bullets))
            header = line[3:].strip()
            podcast_name = ""
            episode_with_date = header
            if "[" in header and "]" in header:
                try:
                    start = header.index("[")
                    end = header.index("]")
                    podcast_name = header[start + 1 : end]
                    episode_with_date = header[end + 1 :].strip()
                except Exception:
                    podcast_name = ""
                    episode_with_date = header
            current = {"name": podcast_name, "title": episode_with_date}
            current_summary = ""
            current_bullets = []
            in_summary_paragraph = True
        elif in_summary_paragraph and line.strip() and not line.startswith("-"):
            current_summary = line.strip()
            in_summary_paragraph = False
        elif line.strip().startswith("- "):
            current_bullets.append(line.strip()[2:])

    if current:
        podcasts.append((current.get("name", ""), current.get("title", ""), current_summary, current_bullets))

    return podcasts


# ---------- Key takeaway parsing ----------

def parse_key_takeaway_sections_cn(text: str) -> List[Tuple[str, List[str]]]:
    lines = text.split("\n")
    sections: List[Tuple[str, List[str]]] = []
    current_section: str | None = None
    current_bullets: List[str] = []
    for line in lines:
        if line.startswith("##"):
            if current_section and current_bullets:
                sections.append((current_section, current_bullets))
            current_section = line.replace("##", "").replace("：", "").strip()
            current_bullets = []
        elif line.strip().startswith("- "):
            bullet_text = line.strip()[2:]
            bullet_text = (
                bullet_text.replace("**", "").replace("[", "").replace("]", "").replace("(", " ").replace(")", "")
            )
            if bullet_text:
                current_bullets.append(bullet_text)
    if current_section and current_bullets:
        sections.append((current_section, current_bullets))
    return sections


def parse_key_takeaway_sections_en(text: str) -> List[Tuple[str, List[str]]]:
    lines = text.split("\n")
    sections: List[Tuple[str, List[str]]] = []
    current_section: str | None = None
    current_bullets: List[str] = []
    for line in lines:
        if line.startswith("##"):
            if current_section and current_bullets:
                sections.append((current_section, current_bullets))
            current_section = line.replace("##", "").replace("：", ":").rstrip(":").strip()
            current_bullets = []
        elif line.strip().startswith("- "):
            bullet_text = line.strip()[2:]
            bullet_text = (
                bullet_text.replace("**", "").replace("[", "").replace("]", "").replace("(", " ").replace(")", "")
            )
            if bullet_text:
                current_bullets.append(bullet_text)
    if current_section and current_bullets:
        sections.append((current_section, current_bullets))
    return sections


# ---------- Sellside parsing (from Archive) ----------

def parse_sellside_reports(text: str) -> List[Tuple[str, List[str], str]]:
    reports: List[Tuple[str, List[str], str]] = []
    lines = text.split("\n")
    current_report: str | None = None
    current_bullets: List[str] = []
    current_link: str = ""
    for line in lines:
        line = line.strip()
        if line.startswith("**") and line.endswith("**"):
            if current_report:
                reports.append((current_report, current_bullets, current_link))
            title = line.strip("*")
            current_report = title
            current_bullets = []
            current_link = ""
        elif line.startswith("- "):
            current_bullets.append(line[2:])
        elif line.startswith("[Report Link]"):
            m = re.search(r"\((.*?)\)", line)
            if m:
                current_link = m.group(1)
    if current_report:
        reports.append((current_report, current_bullets, current_link))
    return reports


# ---------- HTML builders (match Archive structure) ----------

def build_html_cn(date_str: str, key_sections: List[Tuple[str, List[str]]], sellside_md: str | None, podcast_items: List[Tuple[str, str, str, List[str]]]) -> str:
    html = """<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">

<head>
<title>Autonomous Driving News Summary """ + date_str.replace('-', ' ') + """</title>
<meta http-equiv=Content-Type content="text/html; charset=utf-8">
<meta name=Generator content="Microsoft Word 15">
<meta name=Originator content="Microsoft Word 15">
<style>
<!--
p.MsoNormal, li.MsoNormal, div.MsoNormal
{mso-style-unhide:no;
mso-style-qformat:yes;
margin:0cm;
mso-pagination:none;
font-size:11.0pt;
mso-bidi-font-size:12.0pt;
font-family:"Calibri",sans-serif;
mso-ascii-font-family:Calibri;
mso-ascii-theme-font:minor-latin;
mso-fareast-font-family:等线;
mso-fareast-theme-font:minor-fareast;
mso-hansi-font-family:Calibri;
mso-hansi-theme-font:minor-latin;
mso-font-kerning:1.0pt;}
-->
</style>
</head>

<body lang=ZH-CN style='tab-interval:21.0pt;word-wrap:break-word'>

<div class=WordSection1>

<p class=MsoNormal align=center style='text-align:center'><b><span lang=EN-US style='font-size:14.0pt;font-family:"Calibri",sans-serif'>Autonomous Driving News Summary """ + date_str.replace('-', ' ') + """<o:p></o:p></span></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Hi Pengfei and Caiyao,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span style='font-family:DengXian, 等线'>请查收我们本周的</span><span lang=EN-US style='font-family:"Calibri",sans-serif'>Autonomous Driving News Update</span><span style='font-family:DengXian, 等线'>，</span><span lang=EN-US style='font-family:"Calibri",sans-serif'>key topics</span><span style='font-family:DengXian, 等线'>总结如下，详细信息请查阅附件中完整的</span><span lang=EN-US style='font-family:"Calibri",sans-serif'>news brief</span><span style='font-family:DengXian, 等线'>。有任何问题请随时联系我们，谢谢！</span><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Key News takeaway for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    # Key takeaways (sections and bullets)
    first_section = True
    for section_name, bullets in key_sections:
        if not first_section:
            html += """</ul>
"""
        html += f"""
<p class=MsoNormal><u><span style='font-family:DengXian, 等线'>{section_name}</span></u><span style='font-family:DengXian, 等线'>：</span></p>

<ul style='margin-top:0cm' type=disc>"""
        for bullet in bullets:
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', bullet))
            total_chars = max(len(bullet), 1)
            is_chinese = chinese_chars > total_chars * 0.3
            font = 'DengXian, 等线' if is_chinese else '"Calibri",sans-serif'
            html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l1 level1 lfo1'><span style='font-family:{font}'>{bullet}</span></li>"""
        first_section = False

    if key_sections:
        html += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    # Sellside (optional)
    if sellside_md and sellside_md.strip():
        sellside_reports = parse_sellside_reports(sellside_md)
        if sellside_reports:
            html += """
<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Sellside highlights for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""
            for report_title, bullets, link in sellside_reports:
                if ',' in report_title:
                    parts = report_title.split(',', 1)
                    date_part = parts[0] if len(parts) > 0 else ""
                    rest_part = parts[1] if len(parts) > 1 else report_title
                else:
                    date_part = ""
                    rest_part = report_title
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l0 level1 lfo2'>
    <u><span style='font-family:"Calibri",sans-serif'>{date_part}</span></u>"""
                if date_part and rest_part:
                    html += f"""<u><span style='font-family:"Calibri",sans-serif'>,{rest_part}</span></u>"""
                elif rest_part:
                    html += f"""<u><span style='font-family:"Calibri",sans-serif'>{rest_part}</span></u>"""
                if link:
                    html += f"""<span style='font-family:"Calibri",sans-serif'> (</span><a href="{link}"><span style='font-family:"Calibri",sans-serif'>{link}</span></a><span style='font-family:"Calibri",sans-serif'>)</span>"""
                if bullets:
                    html += """
    <ul style='margin-top:0cm' type=circle>"""
                    for sub_bullet in bullets:
                        html += f"""
      <li class=MsoNormal style='text-align:justify;mso-list:l0 level2 lfo2'><span style='font-family:DengXian, 等线'>{sub_bullet}</span></li>"""
                    html += """
    </ul>"""
                html += """
 </li>"""
            html += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    # Podcasts (optional)
    if podcast_items:
        html += """
<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Podcasts highlights for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""
        for podcast_name, episode_title, summary, takeaways in podcast_items:
            if podcast_name:
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'>
    <u><span style='font-family:DengXian, 等线'>[{podcast_name}] {episode_title}</span></u>
    <span style='font-family:DengXian, 等线'>：{summary}</span>
 </li>"""
            else:
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'>
    <u><span style='font-family:DengXian, 等线'>{episode_title}</span></u>
    <span style='font-family:DengXian, 等线'>：{summary}</span>
 </li>"""
            if takeaways:
                html += """
 <ul style='margin-top:0cm' type=circle>"""
                for tk in takeaways:
                    html += f"""
  <li class=MsoNormal style='text-align:justify;mso-list:l3 level2 lfo5'>
     <span style='font-family:DengXian, 等线'>{tk}</span>
  </li>"""
                html += """
 </ul>"""

    html += """
</div>

</body>

</html>
"""
    return html


def build_html_en(date_str: str, key_sections: List[Tuple[str, List[str]]], sellside_md: str | None, podcast_items: List[Tuple[str, str, str, List[str]]]) -> str:
    html = """<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">

<head>
<title>Autonomous Driving News Summary """ + date_str.replace('-', ' ') + """</title>
<meta http-equiv=Content-Type content="text/html; charset=utf-8">
<meta name=Generator content="Microsoft Word 15">
<meta name=Originator content="Microsoft Word 15">
<style>
<!--
p.MsoNormal, li.MsoNormal, div.MsoNormal
{mso-style-unhide:no;
mso-style-qformat:yes;
margin:0cm;
mso-pagination:none;
font-size:11.0pt;
mso-bidi-font-size:12.0pt;
font-family:"Calibri",sans-serif;
mso-ascii-font-family:Calibri;
mso-ascii-theme-font:minor-latin;
mso-fareast-font-family:Calibri;
mso-fareast-theme-font:minor-latin;
mso-hansi-font-family:Calibri;
mso-hansi-theme-font:minor-latin;
mso-font-kerning:1.0pt;}
-->
</style>
</head>

<body lang=EN-US style='tab-interval:21.0pt;word-wrap:break-word'>

<div class=WordSection1>

<p class=MsoNormal align=center style='text-align:center'><b><span lang=EN-US style='font-size:14.0pt;font-family:"Calibri",sans-serif'>Autonomous Driving News Summary """ + date_str.replace('-', ' ') + """<o:p></o:p></span></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Hi Griffin and Vince,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Please find attached our Autonomous Driving News Update for this week. The key topics are summarized below, and full details can be found in the complete news brief attached. Should you have any questions, please feel free to contact us. Thanks!<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Key News Takeaway for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    first_section = True
    for section_name, bullets in key_sections:
        if not first_section:
            html += """</ul>
"""
        html += f"""
<p class=MsoNormal><u><span style='font-family:"Calibri",sans-serif'>{section_name}</span></u><span style='font-family:"Calibri",sans-serif'>:</span></p>

<ul style='margin-top:0cm' type=disc>"""
        for bullet in bullets:
            html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l1 level1 lfo1'><span style='font-family:"Calibri",sans-serif'>{bullet}</span></li>"""
        first_section = False

    if key_sections:
        html += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    # Sellside (optional)
    if sellside_md and sellside_md.strip():
        sellside_reports = parse_sellside_reports(sellside_md)
        if sellside_reports:
            html += """
<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Sellside Highlights for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""
            for report_title, bullets, link in sellside_reports:
                if ',' in report_title:
                    parts = report_title.split(',', 1)
                    date_part = parts[0] if len(parts) > 0 else ""
                    rest_part = parts[1] if len(parts) > 1 else report_title
                else:
                    date_part = ""
                    rest_part = report_title
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l0 level1 lfo2'>
    <u><span style='font-family:"Calibri",sans-serif'>{date_part}</span></u>"""
                if date_part and rest_part:
                    html += f"""<u><span style='font-family:"Calibri",sans-serif'>,{rest_part}</span></u>"""
                elif rest_part:
                    html += f"""<u><span style='font-family:"Calibri",sans-serif'>{rest_part}</span></u>"""
                if link:
                    html += f"""<span style='font-family:"Calibri",sans-serif'> (</span><a href="{link}"><span style='font-family:"Calibri",sans-serif'>{link}</span></a><span style='font-family:"Calibri",sans-serif'>)</span>"""
                if bullets:
                    html += """
    <ul style='margin-top:0cm' type=circle>"""
                    for sub_bullet in bullets:
                        html += f"""
      <li class=MsoNormal style='text-align:justify;mso-list:l0 level2 lfo2'><span style='font-family:"Calibri",sans-serif'>{sub_bullet}</span></li>"""
                    html += """
    </ul>"""
                html += """
 </li>"""
            html += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

    # Podcasts (optional)
    if podcast_items:
        html += """
<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Podcast Highlights for Week – """ + date_str + """<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""
        for podcast_name, episode_title, summary, takeaways in podcast_items:
            if podcast_name:
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'>
    <u><span style='font-family:"Calibri",sans-serif'>[{podcast_name}] {episode_title}</span></u>
    <span style='font-family:"Calibri",sans-serif'>: {summary}</span>
 </li>"""
            else:
                html += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'>
    <u><span style='font-family:"Calibri",sans-serif'>{episode_title}</span></u>
    <span style='font-family:"Calibri",sans-serif'>: {summary}</span>
 </li>"""
            if takeaways:
                html += """
 <ul style='margin-top:0cm' type=circle>"""
                for tk in takeaways:
                    html += f"""
  <li class=MsoNormal style='text-align:justify;mso-list:l3 level2 lfo5'>
     <span style='font-family:"Calibri",sans-serif'>{tk}</span>
  </li>"""
                html += """
 </ul>"""

        html += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

</div>

</body>

</html>
"""
    return html


# ---------- MHT writer (same as Archive) ----------

def write_mht(html_content: str, output_path: Path) -> None:
    boundary = "----=_NextPart_01DC1DB8.F194A1B0"
    mht_lines = [
        "MIME-Version: 1.0",
        f'Content-Type: multipart/related; boundary="{boundary}"',
        "",
        "This document is a Single File Web Page, also known as a Web Archive file.",
        "",
        f"--{boundary}",
        "Content-Location: file:///C:/AutoNews/email.htm",
        "Content-Transfer-Encoding: 8bit",
        'Content-Type: text/html; charset="utf-8"',
        "",
        html_content,
        "",
        f"--{boundary}--",
        "",
    ]
    mht_content = "\r\n".join(mht_lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(mht_content.encode("utf-8"))


# ---------- Orchestration ----------

def generate_one(lang: str, date_str: str) -> Path | None:
    assert lang in ("CN", "ENG")

    # Required: key_takeaway
    key_path = (
        DATA_DIR / f"{date_str}_key_takeaway.md"
        if lang == "CN"
        else DATA_DIR / f"{date_str}_key_takeaway_english.md"
    )
    key_text = read_text_if_exists(key_path)
    if not key_text.strip():
        print(f"Missing key takeaway for {lang}: {key_path}")
        return None

    # Optional: sellside
    sellside_path = (
        DATA_DIR / f"{date_str}_sellside_highlights.md"
        if lang == "CN"
        else DATA_DIR / f"{date_str}_sellside_highlights_english.md"
    )
    sellside_text = read_text_if_exists(sellside_path)

    # Optional: podcasts (consolidated)
    podcast_path = (
        DATA_DIR / f"{date_str}_podcast_summary.md"
        if lang == "CN"
        else DATA_DIR / f"{date_str}_podcast_summary_english.md"
    )
    podcast_items = parse_consolidated_podcast_summary(podcast_path)

    # Build HTML using legacy structure
    if lang == "CN":
        key_sections = parse_key_takeaway_sections_cn(key_text)
        html = build_html_cn(date_str, key_sections, sellside_text, podcast_items)
        out_name = f"{date_str}_email.mht"
    else:
        key_sections = parse_key_takeaway_sections_en(key_text)
        html = build_html_en(date_str, key_sections, sellside_text, podcast_items)
        out_name = f"{date_str}_email_english.mht"

    # Save to Deliverable path under CN/ENG
    deliver_dir = (
        Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Deliverable" / date_str / ("CN" if lang == "CN" else "ENG")
    )
    output_path = deliver_dir / out_name
    write_mht(html, output_path)

    # Brief stats
    total_bullets = sum(len(b) for _, b in key_sections)
    print(
        f"✅ {lang} email generated: {output_path}\n"
        f"   - Key takeaways: {len(key_sections)} sections, {total_bullets} bullets\n"
        f"   - Sellside: {'yes' if sellside_text.strip() else 'no'}\n"
        f"   - Podcasts: {len(podcast_items)} episode(s)"
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly MHT email (CN/ENG)")
    parser.add_argument("--date", type=str, default=friday_date, help=f"Date (default: {friday_date})")
    parser.add_argument("--cn-only", action="store_true", help="Generate CN only")
    parser.add_argument("--eng-only", action="store_true", help="Generate ENG only")
    args = parser.parse_args()

    if args.cn_only and args.eng_only:
        print("Both --cn-only and --eng-only specified; nothing to do.")
        return

    langs: List[str]
    if args.cn_only:
        langs = ["CN"]
    elif args.eng_only:
        langs = ["ENG"]
    else:
        langs = ["CN", "ENG"]

    print("=" * 60)
    print("📧 Weekly Email Generator (MHT)")
    print("=" * 60)
    print(f"📅 Date: {args.date}")
    print(f"🌐 Languages: {', '.join(langs)}")

    any_ok = False
    for lg in langs:
        out = generate_one(lg, args.date)
        any_ok = any_ok or (out is not None)

    if any_ok:
        print("✅ Done.")
    else:
        print("❌ Failed to generate any email. Ensure key takeaway exists.")


if __name__ == "__main__":
    main()
