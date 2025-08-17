#!/usr/bin/env python3
"""
Two-Week News Summary Generator
Fetches the last two weeks of key_takeaway and sellside_highlights files
and generates a summary using Gemini 2.5 Pro
"""

import os
import datetime
import sys
from pathlib import Path

# Import existing modules
from models import gemini_model
from parameters import friday_date

def get_last_two_fridays():
    """Calculate the dates of the last two Fridays"""
    current_date = datetime.datetime.now()
    
    # Get the most recent Friday (including today if it's Friday)
    days_since_friday = (current_date.weekday() - 4) % 7
    if days_since_friday == 0:  # Today is Friday
        last_friday = current_date
    else:
        last_friday = current_date - datetime.timedelta(days=days_since_friday)
    
    # Get the Friday before that
    second_last_friday = last_friday - datetime.timedelta(days=7)
    
    return [
        second_last_friday.strftime('%Y-%m-%d'),
        last_friday.strftime('%Y-%m-%d')
    ]

def clean_markdown_content(content):
    """Remove WORD_STYLE comments from markdown content"""
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that are purely WORD_STYLE comments
        if line.strip().startswith('<!-- WORD_STYLE:') and line.strip().endswith('-->'):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def fetch_news_files(dates):
    """Fetch key_takeaway and sellside_highlights files for given dates"""
    base_dir = Path('data/6_final_mds')
    all_content = []
    
    for date in dates:
        print(f"\n正在处理 {date} 的新闻文件...")
        
        # Define file paths
        key_takeaway_file = base_dir / f"{date}_key_takeaway.md"
        sellside_file = base_dir / f"{date}_sellside_highlights.md"
        
        # Read key_takeaway file
        if key_takeaway_file.exists():
            print(f"  ✓ 找到 key_takeaway 文件: {key_takeaway_file}")
            with open(key_takeaway_file, 'r', encoding='utf-8') as f:
                content = f.read()
                cleaned_content = clean_markdown_content(content)
                all_content.append(f"## {date} - Key Takeaway\n\n{cleaned_content}")
        else:
            print(f"  ✗ 未找到 key_takeaway 文件: {key_takeaway_file}")
        
        # Read sellside_highlights file
        if sellside_file.exists():
            print(f"  ✓ 找到 sellside_highlights 文件: {sellside_file}")
            with open(sellside_file, 'r', encoding='utf-8') as f:
                content = f.read()
                cleaned_content = clean_markdown_content(content)
                all_content.append(f"## {date} - Sellside Highlights\n\n{cleaned_content}")
        else:
            print(f"  ✗ 未找到 sellside_highlights 文件: {sellside_file}")
    
    return '\n\n---\n\n'.join(all_content)

def load_prompt():
    """Load the prompt from the prompt file"""
    prompt_file = Path('prompt/two_week_summary_prompt.txt')
    
    if not prompt_file.exists():
        print(f"错误: 找不到提示文件 {prompt_file}")
        sys.exit(1)
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def generate_summary(content, prompt):
    """Generate summary using Gemini API"""
    print("\n正在调用 Gemini 2.5 Pro 生成总结...")
    
    try:
        summary = gemini_model(prompt, content)
        print("✓ 成功生成总结")
        return summary
    except Exception as e:
        print(f"✗ 生成总结时出错: {e}")
        return None

def save_summary(summary, dates):
    """Save the generated summary to a file"""
    if not summary:
        print("没有总结内容可保存")
        return None
    
    # Create output filename with current timestamp
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data/6_final_mds')
    output_file = output_dir / f"two_week_summary_{current_time}.md"
    
    # Add metadata header
    header = f"""# 两周新闻总结
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
覆盖周期: {dates[0]} 至 {dates[1]}

---

"""
    
    # Save the file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header + summary)
    
    print(f"\n✓ 总结已保存至: {output_file}")
    return output_file

def main():
    """Main function"""
    print("=" * 60)
    print("两周新闻总结生成器")
    print("=" * 60)
    
    # Get the last two Friday dates
    dates = get_last_two_fridays()
    print(f"\n将处理以下两周的新闻:")
    for date in dates:
        print(f"  • {date}")
    
    # Allow custom dates via command line arguments
    if len(sys.argv) == 3:
        dates = [sys.argv[1], sys.argv[2]]
        print(f"\n使用自定义日期: {dates[0]} 和 {dates[1]}")
    
    # Fetch news files
    combined_content = fetch_news_files(dates)
    
    if not combined_content:
        print("\n错误: 没有找到任何新闻文件")
        sys.exit(1)
    
    print(f"\n已加载 {len(combined_content)} 个字符的内容")
    
    # Load prompt
    prompt = load_prompt()
    print(f"已加载提示文件 ({len(prompt)} 个字符)")
    
    # Generate summary
    summary = generate_summary(combined_content, prompt)
    
    # Save summary
    output_file = save_summary(summary, dates)
    
    if output_file:
        print("\n✅ 处理完成!")
        print(f"输出文件: {output_file}")
    else:
        print("\n❌ 处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()