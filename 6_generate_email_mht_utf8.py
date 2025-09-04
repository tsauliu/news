#!/usr/bin/env python3
# Generate Chinese email in MHT format with UTF-8 encoding for browser compatibility

import os
import base64

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

# Generate simple HTML body
html_body = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style>
body {
    font-family: "Calibri", "Microsoft YaHei", sans-serif;
    font-size: 11pt;
    color: #333;
    margin: 20px;
}
p { margin: 8px 0; }
ul { margin: 10px 0; }
li { margin: 5px 0; line-height: 1.6; }
.signature { margin-top: 30px; }
</style>
</head>
<body>

<p>Hi Pengfei, Caiyao,</p>

<p>以下是本周的AI news update的关键要点总结，详细信息请参考完整pdf文档。如有任何问题请随时联系，谢谢！</p>

<p><b><u>News Summary:</u></b></p>

<p><u>Key Takeaways</u></p>
<ul>"""

# Add key takeaway bullets
takeaway_bullets = md_to_simple_bullets(key_takeaway)
for bullet in takeaway_bullets[:15]:
    html_body += f"\n<li>{bullet}</li>"

html_body += """
</ul>

<p><u>Sellside Research</u></p>
<ul>"""

# Add sellside bullets
sellside_bullets = md_to_simple_bullets(sellside)
for bullet in sellside_bullets[:10]:
    html_body += f"\n<li>{bullet}</li>"

html_body += """
</ul>

<p><b><u>Podcasts:</u></b></p>
<ul>"""

# Add podcast summaries
for title, summary, takeaways in podcast_summaries:
    html_body += f"\n<li><u>{title}</u>：{summary}"
    if takeaways:
        html_body += "\n<ul>"
        for takeaway in takeaways[:3]:
            html_body += f"\n<li>{takeaway}</li>"
        html_body += "\n</ul>"
    html_body += "</li>"

html_body += """
</ul>

<div class="signature">
<p>Leo Cao</p>
<p>Deputy Manager</p>
<p>BDA</p>
<p>&nbsp;</p>
<p>BDA (China) Limited</p>
<p>36th Floor, China World Tower 3A,</p>
<p>1 Jian Guo Men Wai Avenue,</p>
<p>Chaoyang District, Beijing 100004, China</p>
<p>Tel: +8610 6564 2288 x 286</p>
<p>Direct: +8610 6564 2286</p>
</div>

</body>
</html>"""

# Create MHT file with UTF-8 and base64 encoding
def create_mht_utf8(html_content, output_path):
    boundary = "----=_NextPart_01DC1DB8.F194A1B0"
    
    # Encode HTML to base64 for proper transmission
    html_bytes = html_content.encode('utf-8')
    html_base64 = base64.b64encode(html_bytes).decode('ascii')
    
    # Format base64 with line breaks every 76 characters
    formatted_base64 = '\n'.join([html_base64[i:i+76] for i in range(0, len(html_base64), 76)])
    
    # Build MHT
    mht_content = f"""MIME-Version: 1.0
Content-Type: multipart/related; boundary="{boundary}"

This document is a Single File Web Page, also known as a Web Archive file.

--{boundary}
Content-Location: file:///C:/AutoNews/email.htm
Content-Transfer-Encoding: base64
Content-Type: text/html; charset="utf-8"

{formatted_base64}

--{boundary}--
"""
    
    with open(output_path, 'wb') as f:
        f.write(mht_content.encode('utf-8'))

# Generate MHT
output_file = f'data/7_emails/{test_date}_email_utf8.mht'
create_mht_utf8(html_body, output_file)

print(f"✅ UTF-8 MHT Email generated: {output_file}")
print(f"📊 Content included:")
print(f"   - Key takeaways: {len(takeaway_bullets)} points")
print(f"   - Sellside reports: {len(sellside_bullets)} items")
print(f"   - Podcast summaries: {len(podcast_summaries)} with key takeaways")