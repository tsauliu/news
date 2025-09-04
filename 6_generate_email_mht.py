#!/usr/bin/env python3
"""
Generate weekly news summary email in MHT format

Features:
- Mixed Chinese/English font support (等线/Calibri)
- Key takeaways from weekly news
- Sellside research highlights with PDF links
- Podcast summaries with episode details
- Professional Microsoft Word-style HTML formatting
- UTF-8 encoding with proper MIME structure
"""

import os
import re

# Test with specific date
test_date = '2025-08-29'

# Create output directory
os.makedirs('data/7_emails', exist_ok=True)

# Read data sources
key_takeaway = open(f'data/6_final_mds/{test_date}_key_takeaway.md', 'r', encoding='utf-8').read()
sellside = open(f'data/6_final_mds/{test_date}_sellside_highlights.md', 'r', encoding='utf-8').read()

# Extract Podcast name, Summary and Takeaways from podcasts
def extract_podcast_essentials(podcast_path):
    content = open(podcast_path, 'r', encoding='utf-8').read()
    lines = content.split('\n')
    
    podcast_name = ""
    episode_title = ""
    summary = ""
    takeaways = []
    in_info = False
    in_summary = False
    in_takeaways = False
    
    for line in lines:
        if line.strip() == '# Info':
            in_info = True
            continue
        elif line.strip() == '# Summary':
            in_info = False
            in_summary = True
            in_takeaways = False
            continue
        elif line.strip() == '# Takeaways':
            in_summary = False
            in_takeaways = True
            continue
        elif line.strip().startswith('# '):
            in_info = False
            in_summary = False
            in_takeaways = False
            continue
        
        if in_info:
            if line.startswith('- Podcast:'):
                podcast_name = line.replace('- Podcast:', '').strip()
            elif line.startswith('- Episode:'):
                episode_title = line.replace('- Episode:', '').strip()
        elif in_summary and line.strip():
            summary = line.strip()
        elif in_takeaways and line.strip().startswith('*'):
            takeaways.append(line.strip()[1:].strip())
    
    return podcast_name, episode_title, summary, takeaways

# Process podcasts
podcast_summaries = []
podcast_dir = f'podcast/{test_date}'
for file in sorted(os.listdir(podcast_dir)):
    if file.endswith('.md'):
        podcast_name, episode_title, summary, takeaways = extract_podcast_essentials(f'{podcast_dir}/{file}')
        podcast_summaries.append((podcast_name, episode_title, summary, takeaways[:5]))

# Parse markdown to extract sections and bullets
def parse_key_takeaway_sections(text):
    lines = text.split('\n')
    sections = []
    current_section = None
    current_bullets = []
    
    for line in lines:
        if line.startswith('##'):
            # Save previous section if exists
            if current_section and current_bullets:
                sections.append((current_section, current_bullets))
            # Start new section
            current_section = line.replace('##', '').replace('：', '').strip()
            current_bullets = []
        elif line.strip().startswith('- '):
            # Add bullet to current section
            bullet_text = line.strip()[2:]
            # Remove markdown formatting
            bullet_text = bullet_text.replace('**', '').replace('[', '').replace(']', '').replace('(', ' ').replace(')', '')
            if bullet_text:
                current_bullets.append(bullet_text)
    
    # Don't forget the last section
    if current_section and current_bullets:
        sections.append((current_section, current_bullets))
    
    return sections

# Convert markdown to simple bullets (for backwards compatibility)
def md_to_simple_bullets(text):
    lines = text.split('\n')
    bullets = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('##'):
            continue
        if line.startswith('#'):
            line = line.replace('#', '').strip()
        if line.startswith('- '):
            line = line[2:]
        if line.startswith('*'):
            line = line.strip('*').strip()
        
        # Remove markdown formatting
        line = line.replace('**', '').replace('[', '').replace(']', '').replace('(', ' ').replace(')', '')
        
        if len(line) > 10:
            bullets.append(line)
    
    return bullets

# Parse sellside reports with new structure
def parse_sellside_reports(text):
    reports = []
    lines = text.split('\n')
    
    current_report = None
    current_bullets = []
    
    for line in lines:
        line = line.strip()
        
        # Check for report title (starts with **)
        if line.startswith('**') and line.endswith('**'):
            # Save previous report if exists
            if current_report:
                reports.append((current_report, current_bullets, current_link))
            
            # Parse new report
            title = line.strip('*')
            current_report = title
            current_bullets = []
            current_link = ""
            
        # Check for bullet points
        elif line.startswith('- '):
            current_bullets.append(line[2:])
            
        # Check for report link
        elif line.startswith('[Report Link]'):
            match = re.search(r'\((.*?)\)', line)
            if match:
                current_link = match.group(1)
    
    # Don't forget the last report
    if current_report:
        reports.append((current_report, current_bullets, current_link))
    
    return reports

# Generate HTML body with improved formatting
html_body = """<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">

<head>
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

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Hi Pengfei, Caiyao,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span style='font-family:等线'>以下是本周的</span><span lang=EN-US style='font-family:"Calibri",sans-serif'>AI news update</span><span style='font-family:等线'>的关键要点总结，详细信息请参考完整</span><span lang=EN-US style='font-family:"Calibri",sans-serif'>pdf</span><span style='font-family:等线'>文档。如有任何问题请随时联系，谢谢！</span><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Key News takeaway for Week – """ + test_date + """<o:p></o:p></span></u></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>
"""

# Parse and add key takeaway sections with ALL bullets
takeaway_sections = parse_key_takeaway_sections(key_takeaway)

first_section = True
for section_name, bullets in takeaway_sections:
    if not first_section:
        # Close previous list
        html_body += """</ul>
"""
    
    # Add section header as paragraph text with underline (colon not underlined)
    html_body += f"""
<p class=MsoNormal><u><span style='font-family:等线'>{section_name}</span></u><span style='font-family:等线'>：</span></p>

<ul style='margin-top:0cm' type=disc>"""
    
    # Add ALL bullets for this section
    for bullet in bullets:
        # Detect if content is primarily Chinese or English
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', bullet))
        total_chars = len(bullet)
        is_chinese = chinese_chars > total_chars * 0.3
        
        font = '等线' if is_chinese else '"Calibri",sans-serif'
        html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l1 level1 lfo1'><span style='font-family:{font}'>{bullet}</span></li>"""
    
    first_section = False

html_body += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Sellside highlights for Week – """ + test_date + """<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""

# Parse and add sellside reports with new format
sellside_reports = parse_sellside_reports(sellside)
for report_title, bullets, link in sellside_reports:
    # Format: Date,Firm: Title (URL)
    if ',' in report_title:
        parts = report_title.split(',', 1)
        date_part = parts[0] if len(parts) > 0 else ""
        rest_part = parts[1] if len(parts) > 1 else report_title
    else:
        date_part = ""
        rest_part = report_title
    
    html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l0 level1 lfo2'>
    <span style='font-family:"Calibri",sans-serif'>{date_part}</span>"""
    
    if date_part and rest_part:
        html_body += f"""<span style='font-family:"Calibri",sans-serif'>,{rest_part}</span>"""
    elif rest_part:
        html_body += f"""<span style='font-family:"Calibri",sans-serif'>{rest_part}</span>"""
    
    if link:
        html_body += f"""<span style='font-family:"Calibri",sans-serif'> (</span><a href="{link}"><span style='font-family:"Calibri",sans-serif'>{link}</span></a><span style='font-family:"Calibri",sans-serif'>)</span>"""
    
    # Add sub-bullets for key points
    if bullets:
        html_body += """
    <ul style='margin-top:0cm' type=circle>"""
        for sub_bullet in bullets[:2]:  # Limit to 2 key points per report
            html_body += f"""
      <li class=MsoNormal style='text-align:justify;mso-list:l0 level2 lfo2'><span style='font-family:等线'>{sub_bullet}</span></li>"""
        html_body += """
    </ul>"""
    
    html_body += """
 </li>"""

html_body += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Podcasts:<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""

# Add podcast summaries with improved format
for podcast_name, episode_title, summary, takeaways in podcast_summaries:
    # Format as: [Podcast Name] Episode Title：Summary (all underlined)
    html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'>
    <u><span style='font-family:等线'>[{podcast_name}] {episode_title}</span></u>
    <span style='font-family:等线'>：{summary}</span>
 </li>"""
    
    if takeaways:
        html_body += """
 <ul style='margin-top:0cm' type=circle>"""
        for takeaway in takeaways[:3]:
            # Clean takeaways without any prefix
            html_body += f"""
  <li class=MsoNormal style='text-align:justify;mso-list:l3 level2 lfo5'>
     <span style='font-family:等线'>{takeaway}</span>
  </li>"""
        html_body += """
 </ul>"""

html_body += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Leo Cao<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Deputy Manager<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>BDA<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>&nbsp;<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>BDA (China) Limited<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>36th Floor, China World Tower 3A,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>1 Jian Guo Men Wai Avenue,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Chaoyang District, Beijing 100004, China<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Tel: +8610 6564 2288 x 286<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Direct: +8610 6564 2286<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US><o:p>&nbsp;</o:p></span></p>

</div>

</body>

</html>
"""

# Create MHT file with UTF-8 encoding and CRLF
def create_mht_improved(html_content, output_path):
    boundary = "----=_NextPart_01DC1DB8.F194A1B0"
    
    # Build MHT content with CRLF line endings
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
        ""
    ]
    
    # Join with CRLF
    mht_content = '\r\n'.join(mht_lines)
    
    # Write with UTF-8 encoding
    with open(output_path, 'wb') as f:
        f.write(mht_content.encode('utf-8'))

# Generate MHT
output_file = f'data/7_emails/{test_date}_email.mht'
create_mht_improved(html_body, output_file)

# Calculate total bullets from all sections
total_bullets = sum(len(bullets) for _, bullets in takeaway_sections)

print(f"✅ MHT Email generated: {output_file}")
print(f"📊 Content included:")
print(f"   - Key takeaways: {len(takeaway_sections)} sections, {total_bullets} total points")
print(f"   - Sellside reports: {len(sellside_reports)} items with links")
print(f"   - Podcast summaries: {len(podcast_summaries)} episodes")