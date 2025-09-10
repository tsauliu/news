#!/usr/bin/env python3
"""
Two-Week News Summary (root step 10)

Generates a trailing two-week summary by reusing the legacy logic and
format from Archive/10_two_week_summary.py, with the following behavior:

- Collect inputs from the last two Fridays: key_takeaway + sellside_highlights
  located under `data/6_final_mds/{YYYY-MM-DD}_*.md`.
- Clean WORD_STYLE comments from markdown before feeding to the LLM.
- Use the prompt at `prompt/two_week_summary_prompt.txt`.
- Save a timestamped artifact under `data/6_final_mds/two_week_summary_*.md`.
- Also write/overwrite a stable Markdown at
  `~/Dropbox/MyServerFiles/AutoWeekly/Deliverable/two_week_summary.md`.

Optional CLI:
    python 10_two_week_summary.py                 # auto-pick last two Fridays
    python 10_two_week_summary.py 2025-09-05 2025-09-12  # custom dates
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import List, Optional

from models import OneAPI_request
from parameters import friday_date


FINAL_DIR = Path("data/6_final_mds")
# Legacy/archived weeks are stored under the SS subfolder of 6_final_mds
LEGACY_SS_DIR = FINAL_DIR / "SS"
PROMPT_PATH = Path("prompt/two_week_summary_prompt.txt")
DROPBOX_DELIVERABLE = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly" / "Deliverable"


def get_last_two_fridays(now: Optional[datetime.datetime] = None) -> List[str]:
    """Return dates (YYYY-MM-DD) for the last two Fridays (inclusive if today is Friday)."""
    current = now or datetime.datetime.now()
    days_since_friday = (current.weekday() - 4) % 7  # Friday=4
    last_friday = current if days_since_friday == 0 else current - datetime.timedelta(days=days_since_friday)
    second_last = last_friday - datetime.timedelta(days=7)
    return [second_last.strftime("%Y-%m-%d"), last_friday.strftime("%Y-%m-%d")]


def clean_markdown_content(content: str) -> str:
    """Strip lines like: <!-- WORD_STYLE: ... -->"""
    out: list[str] = []
    for line in content.split("\n"):
        s = line.strip()
        if s.startswith("<!-- WORD_STYLE:") and s.endswith("-->"):
            continue
        out.append(line)
    return "\n".join(out)


def fetch_news_files(dates: List[str]) -> str:
    """Read key_takeaway and sellside_highlights markdown for given dates; join with separators."""
    blocks: list[str] = []
    for date in dates:
        print(f"\n处理 {date} 的新闻文件…")
        key_takeaway = FINAL_DIR / f"{date}_key_takeaway.md"
        sellside = FINAL_DIR / f"{date}_sellside_highlights.md"

        if key_takeaway.exists():
            print(f"  ✓ key_takeaway: {key_takeaway}")
            blocks.append(f"## {date} - Key Takeaway\n\n" + clean_markdown_content(key_takeaway.read_text(encoding="utf-8")))
        else:
            # Try legacy SS dir (if user keeps old artifacts there)
            legacy_kt = LEGACY_SS_DIR / f"{date}_key_takeaway.md"
            if legacy_kt.exists():
                print(f"  ✓ key_takeaway(legacy): {legacy_kt}")
                blocks.append(f"## {date} - Key Takeaway\n\n" + clean_markdown_content(legacy_kt.read_text(encoding="utf-8")))
            else:
                print(f"  ✗ 缺少 key_takeaway: {key_takeaway}")

        if sellside.exists():
            print(f"  ✓ sellside_highlights: {sellside}")
            blocks.append(
                f"## {date} - Sellside Highlights\n\n" + clean_markdown_content(sellside.read_text(encoding="utf-8"))
            )
        else:
            legacy_ss = LEGACY_SS_DIR / f"{date}_sellside_highlights.md"
            if legacy_ss.exists():
                print(f"  ✓ sellside_highlights(legacy): {legacy_ss}")
                blocks.append(
                    f"## {date} - Sellside Highlights\n\n" + clean_markdown_content(legacy_ss.read_text(encoding="utf-8"))
                )
            else:
                print(f"  ✗ 缺少 sellside_highlights: {sellside}")

    return "\n\n---\n\n".join(blocks)


def load_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def generate_summary(content: str, prompt: str) -> str:
    print("\n调用 Gemini (OneAPI) 生成两周总结…")
    try:
        return OneAPI_request(prompt, content, model="gemini-2.5-pro")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return ""


def save_local_summary(summary: str, dates: List[str]) -> Optional[Path]:
    if not summary.strip():
        print("没有总结内容，跳过本地保存")
        return None
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = FINAL_DIR / f"two_week_summary_{ts}.md"
    header = (
        f"# 两周新闻总结\n"
        f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"覆盖周期: {dates[0]} 至 {dates[1]}\n\n---\n\n"
    )
    out_path.write_text(header + summary, encoding="utf-8")
    print(f"✓ 本地已保存: {out_path}")
    return out_path


def save_dropbox_summary(summary: str, dates: List[str]) -> Optional[Path]:
    if not summary.strip():
        return None
    DROPBOX_DELIVERABLE.mkdir(parents=True, exist_ok=True)
    out_path = DROPBOX_DELIVERABLE / "two_week_summary.md"
    header = (
        f"# 两周新闻总结\n"
        f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"覆盖周期: {dates[0]} 至 {dates[1]}\n\n---\n\n"
    )
    out_path.write_text(header + summary, encoding="utf-8")
    print(f"✓ Dropbox 已保存/覆盖: {out_path}")
    return out_path


def main() -> None:
    print("=" * 60)
    print("两周新闻总结生成器 (Step 10)")
    print("=" * 60)

    # Dates: CLI override or computed
    if len(sys.argv) == 3:
        dates = [sys.argv[1], sys.argv[2]]
        print(f"使用自定义日期: {dates[0]} 和 {dates[1]}")
    else:
        # Use pipeline anchor: current configured Friday and previous Friday
        try:
            curr = datetime.datetime.strptime(friday_date, "%Y-%m-%d")
        except Exception:
            # Fallback to runtime computation if parameters.friday_date is invalid
            dates = get_last_two_fridays()
        else:
            prev = curr - datetime.timedelta(days=7)
            dates = [prev.strftime("%Y-%m-%d"), curr.strftime("%Y-%m-%d")]
        print("将处理以下两周:")
        for d in dates:
            print(f"  • {d}")

    combined = fetch_news_files(dates)
    if not combined.strip():
        print("\n错误: 未找到任何输入文件内容，退出")
        sys.exit(1)

    prompt = load_prompt()
    print(f"已加载提示词，长度 {len(prompt)} 字符")

    summary = generate_summary(combined, prompt)
    if not summary.strip():
        print("\n❌ 总结生成失败")
        sys.exit(1)

    local_path = save_local_summary(summary, dates)
    dropbox_path = save_dropbox_summary(summary, dates)

    print("\n✅ 完成")
    if local_path:
        print(f"本地输出: {local_path}")
    if dropbox_path:
        print(f"Dropbox 输出: {dropbox_path}")


if __name__ == "__main__":
    main()
