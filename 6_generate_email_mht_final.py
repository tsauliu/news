#!/usr/bin/env python3
# Generate Chinese email in MHT format with UTF-8 encoding for proper display

import os

# Test with specific date
test_date = '2025-08-29'

# Create output directory
os.makedirs('data/7_emails', exist_ok=True)

# Read data sources
key_takeaway = open(f'data/6_final_mds/{test_date}_key_takeaway.md', 'r', encoding='utf-8').read()
sellside = open(f'data/6_final_mds/{test_date}_sellside_highlights.md', 'r', encoding='utf-8').read()

# Extract only Summary and Takeaways from podcasts
def extract_podcast_essentials(podcast_path):
    content = open(podcast_path, 'r', encoding='utf-8').read()
    lines = content.split('\n')
    
    summary = ""
    takeaways = []
    in_summary = False
    in_takeaways = False
    
    for line in lines:
        if line.strip() == '# Summary':
            in_summary = True
            in_takeaways = False
            continue
        elif line.strip() == '# Takeaways':
            in_summary = False
            in_takeaways = True
            continue
        elif line.strip().startswith('# '):
            in_summary = False
            in_takeaways = False
            continue
        
        if in_summary and line.strip():
            summary = line.strip()
        elif in_takeaways and line.strip().startswith('*'):
            takeaways.append(line.strip()[1:].strip())
    
    return summary, takeaways

# Process podcasts
podcast_summaries = []
podcast_dir = f'podcast/{test_date}'
for file in sorted(os.listdir(podcast_dir)):
    if file.endswith('.md'):
        title = file.replace('.md', '')
        summary, takeaways = extract_podcast_essentials(f'{podcast_dir}/{file}')
        podcast_summaries.append((title, summary, takeaways[:5]))

# Convert markdown to simple bullets
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

# Generate HTML body with UTF-8 encoding
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
mso-font-kerning:1.0pt;}
-->
</style>
</head>

<body lang=ZH-CN style='tab-interval:21.0pt;word-wrap:break-word'>

<div class=WordSection1>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'>Hi Pengfei, Caiyao,<o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><span style='font-family:"Calibri",sans-serif'>以下是本周的AI news update的关键要点总结，详细信息请参考完整pdf文档。如有任何问题请随时联系，谢谢！</span><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p></o:p></span></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>News Summary:<o:p></o:p></span></u></b></p>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Key Takeaways<o:p></o:p></span></u></p>

<ul style='margin-top:0cm' type=disc>"""

# Add key takeaway bullets
takeaway_bullets = md_to_simple_bullets(key_takeaway)
for bullet in takeaway_bullets[:15]:
    html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l1 level1 lfo1'><span style='font-family:"Calibri",sans-serif'>{bullet}</span></li>"""

html_body += """
</ul>

<p class=MsoNormal><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Sellside Research<o:p></o:p></span></u></p>

<ul style='margin-top:0cm' type=disc>"""

# Add sellside bullets
sellside_bullets = md_to_simple_bullets(sellside)
for bullet in sellside_bullets[:10]:
    html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l0 level1 lfo2'><span style='font-family:"Calibri",sans-serif'>{bullet}</span></li>"""

html_body += """
</ul>

<p class=MsoNormal><span lang=EN-US style='font-family:"Calibri",sans-serif'><o:p>&nbsp;</o:p></span></p>

<p class=MsoNormal><b><u><span lang=EN-US style='font-family:"Calibri",sans-serif'>Podcasts:<o:p></o:p></span></u></b></p>

<ul style='margin-top:0cm' type=disc>"""

# Add podcast summaries
for title, summary, takeaways in podcast_summaries:
    html_body += f"""
 <li class=MsoNormal style='text-align:justify;mso-list:l3 level1 lfo5'><u><span style='font-family:"Calibri",sans-serif'>{title}</span></u><span style='font-family:"Calibri",sans-serif'>：{summary}</span></li>"""
    
    if takeaways:
        html_body += """
 <ul style='margin-top:0cm' type=circle>"""
        for takeaway in takeaways[:3]:
            html_body += f"""
  <li class=MsoNormal style='text-align:justify;mso-list:l3 level2 lfo5'><span style='font-family:"Calibri",sans-serif'>{takeaway}</span></li>"""
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
def create_mht_final(html_content, output_path):
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
output_file = f'data/7_emails/{test_date}_email_final.mht'
create_mht_final(html_body, output_file)

print(f"✅ Final MHT Email generated: {output_file}")
print(f"📊 Content included:")
print(f"   - Key takeaways: {len(takeaway_bullets)} points")
print(f"   - Sellside reports: {len(sellside_bullets)} items")
print(f"   - Podcast summaries: {len(podcast_summaries)} with key takeaways")
print(f"\n📝 File uses UTF-8 encoding for proper Chinese display")