"""
1_fetching_news.py

Combined pipeline for fetching news (steps 0 + 1 + 2):
- RSS mode: parses OPML, extracts entries to CSV, writes raw MDs, builds URL list, and backfills placeholders.
- remote_db mode: pulls remote/local SQLite wechat data to URLs CSV/XLSX, then downloads raw MDs from remote server.

Preserves behavior of:
- 0_RSS.py
- 1_sql_to_urls.py
- 2_get_mds.py

Configuration:
- `parameters.ARTICLE_SOURCE` controls mode: 'rss' or 'remote_db'
- `apikey.news_start` (optional) or env `NEWS_START` controls lookback window (days)
"""

from __future__ import annotations

import os
import datetime as dt
import sqlite3
from typing import List, Dict
from pathlib import Path

import pandas as pd

# Third-party libraries used by the original scripts
import feedparser
from bs4 import BeautifulSoup
import requests

from parameters import (
    friday_date,
    download_file,
    get_filename,
    ARTICLE_SOURCE,
    errorkeywords,
)
from utils import archive_existing_in_target


NEWS_LOOKBACK_DAYS = int(os.getenv("NEWS_START", "7"))

# Constants/paths
URLS_DIR = "data/1_urls"
RAW_MDS_ROOT_DIR = "data/2_raw_mds"
RAW_MDS_DIR = f"{RAW_MDS_ROOT_DIR}/{friday_date}"
RSS_ARTICLES_CSV = "data/rss_articles.csv"
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/869f9457-6d3d-4f88-8bee-d21c41b11625"


def send_feishu_notification(article_count: int) -> None:
    """Send the weekly article count to the Feishu webhook."""
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"{friday_date} weekly news URLs prepared: {article_count} items."
        },
    }

    try:
        response = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code != 200:
            print(
                "Feishu notification failed: "
                f"{response.status_code} {response.text.strip()}"
            )
    except requests.RequestException as exc:
        print(f"Feishu notification error: {exc}")


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def _ensure_dirs() -> None:
    os.makedirs(URLS_DIR, exist_ok=True)
    os.makedirs(RAW_MDS_DIR, exist_ok=True)


def _ensure_weekly_external_folders() -> None:
    """Ensure this week's Podcast and Sellside source folders exist under Dropbox.

    Creates:
    - ~/Dropbox/MyServerFiles/AutoWeekly/Podcast/{friday_date}
    - ~/Dropbox/MyServerFiles/AutoWeekly/Sellside/{friday_date}
    """
    base = Path.home() / "Dropbox" / "MyServerFiles" / "AutoWeekly"
    podcast_dir = base / "Podcast" / friday_date
    sellside_dir = base / "Sellside" / friday_date
    try:
        podcast_dir.mkdir(parents=True, exist_ok=True)
        sellside_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: failed to ensure external weekly folders: {e}")


# ---------------------------
# RSS (former 0_RSS.py)
# ---------------------------
def read_opml_feeds_to_df(opml_file: str = "rss_source.opml") -> pd.DataFrame:
    """Read RSS feed URLs from an OPML file, parse feeds, and return entries.

    Also writes raw MD placeholders/content under `data/2_raw_mds/{friday_date}`
    when new items are found (skips overwriting existing files).
    """
    import xml.etree.ElementTree as ET

    articles: List[Dict] = []
    sources: List[Dict[str, str]] = []

    if not os.path.exists(opml_file):
        print(f"Error: OPML file '{opml_file}' not found.")
        return pd.DataFrame(articles)

    print(f"Reading RSS sources from OPML file: {opml_file}")
    try:
        tree = ET.parse(opml_file)
        root = tree.getroot()
        for outline in root.findall(".//body//outline[@xmlUrl]"):
            url = outline.get("xmlUrl")
            name = outline.get("text", outline.get("title", "Unknown Source"))
            if url:
                sources.append({"name": name, "url": url})
    except ET.ParseError as e:
        print(f"Error parsing OPML file '{opml_file}': {e}")
        return pd.DataFrame(articles)
    except Exception as e:
        print(f"Error reading OPML file '{opml_file}': {e}")
        return pd.DataFrame(articles)

    if not sources:
        print("No RSS feed sources found in the OPML file.")
        return pd.DataFrame(articles)

    print(f"Processing {len(sources)} RSS sources from '{opml_file}'...")
    _ensure_dirs()

    for src in sources:
        url = src["url"]
        source_name = src["name"]
        print(f"  Fetching feed: {source_name} ({url})")
        feed = feedparser.parse(url)
        if getattr(feed, "bozo", False):
            print(f"    Warning: Potential issue parsing feed {url}. Reason: {feed.bozo_exception}")

        for entry in getattr(feed, "entries", []):
            link = entry.get("link")
            title = entry.get("title")
            published = entry.get("published")

            articles.append(
                {
                    "source_name": source_name,
                    "published": published,
                    "title": title,
                    "link": link,
                }
            )

            # Write raw MD once per unique link-derived filename
            filename = f"{get_filename(link, 'rss')}.md"
            output_path = os.path.join(RAW_MDS_DIR, filename)
            if os.path.exists(output_path):
                continue

            text_content = ""
            try:
                content_items = entry.get("content")
                if content_items and isinstance(content_items, list) and content_items:
                    content_html = content_items[0].get("value")
                    text_content = _html_to_text(content_html)
            except Exception:
                text_content = ""

            if not text_content or any(k in text_content for k in errorkeywords):
                summary_html = entry.get("summary") or entry.get("description")
                if summary_html:
                    text_content = _html_to_text(summary_html)

            if not text_content:
                safe_title = title or "Untitled"
                text_content = (
                    "[No content extracted]\n"
                    f"Source: {source_name}\nTitle: {safe_title}\nLink: {link}\nPublished: {published}"
                )

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
            except Exception as e:
                print(f"    Error writing file for {link}: {e}")

    print(f"Finished processing. Extracted {len(articles)} articles.")
    return pd.DataFrame(articles)


def save_and_merge_rss_articles(articles_df: pd.DataFrame) -> pd.DataFrame:
    """Merge with existing RSS CSV, drop duplicate title+link, then save and return."""
    if articles_df.empty:
        print("No RSS articles to save.")
        return articles_df

    articles_df = articles_df.copy()
    articles_df["published"] = pd.to_datetime(articles_df["published"], errors="coerce")
    articles_df = articles_df.sort_values(by="published", ascending=False)

    if os.path.exists(RSS_ARTICLES_CSV):
        existing_df = pd.read_csv(RSS_ARTICLES_CSV)
        existing_df["published"] = pd.to_datetime(existing_df["published"], errors="coerce")
        combined = pd.concat([existing_df, articles_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["title", "link"], keep="first")
        combined = combined.sort_values(by="published", ascending=False)
        print(
            f"Added {len(combined) - len(existing_df)} new articles to existing {len(existing_df)} articles."
        )
        combined.to_csv(RSS_ARTICLES_CSV, index=False)
        return combined
    else:
        articles_df.to_csv(RSS_ARTICLES_CSV, index=False)
        print(f"Created new file with {len(articles_df)} articles.")
        return articles_df


# ---------------------------
# URLs extraction (former 1_sql_to_urls.py)
# ---------------------------
def build_urls_from_remote_db() -> pd.DataFrame:
    """Build URL rows from remote/local wechat SQLite DBs and return a normalized DataFrame."""
    local_db_path = "data/wechat_articles.db"

    try:
        remote_db_url = "http://118.193.44.18:8000/data/wechat_articles.db"
        os.makedirs("data", exist_ok=True)
        download_file(remote_db_url, local_db_path)
    except Exception as e:
        print(f"Error downloading remote database file: {e}")

    conn_wechat = sqlite3.connect(local_db_path)
    wechat_articles = pd.read_sql_query("SELECT * FROM articles", conn_wechat)
    conn_wechat.close()

    wechat_articles["pub_time"] = pd.to_datetime(
        wechat_articles["pub_time"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    wechat_articles["source"] = "wechat"
    wechat_articles.rename(
        columns={
            "pub_time": "publish_time",
            "article_title": "title",
            "channel_scraped": "mp_name",
        },
        inplace=True,
    )
    wechat_articles = wechat_articles[["mp_name", "title", "url", "publish_time", "source"]].sort_values(
        by="publish_time", ascending=False
    )

    conn = sqlite3.connect("data/wewe-rss.db")
    articles = pd.read_sql_query("SELECT * FROM articles", conn)
    articles["publish_time"] = (
        pd.to_datetime(articles["publish_time"], unit="s", utc=True)
        .dt.tz_convert("Asia/Shanghai")
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    articles["created_at"] = (
        pd.to_datetime(articles["created_at"], unit="ms", utc=True)
        .dt.tz_convert("Asia/Shanghai")
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    articles["updated_at"] = (
        pd.to_datetime(articles["updated_at"], unit="ms", utc=True)
        .dt.tz_convert("Asia/Shanghai")
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    articles["url"] = "https://mp.weixin.qq.com/s/" + articles["id"].astype(str)
    feeds = pd.read_sql_query("SELECT * FROM feeds", conn)
    conn.close()

    article_clean = articles[["mp_id", "title", "publish_time", "url"]].merge(
        feeds.rename(columns={"id": "mp_id"})[["mp_id", "mp_name"]], on="mp_id", how="left"
    ).drop(columns=["mp_id"])
    article_clean.sort_values(by="publish_time", ascending=False, inplace=True)
    article_clean["source"] = "wewerss"

    # Merge both wechat sources, dedupe by url
    merged = pd.concat([article_clean, wechat_articles]).drop_duplicates(subset=["url"])
    merged.sort_values(by="publish_time", ascending=False, inplace=True)
    return merged[["publish_time", "mp_name", "title", "url", "source"]]


def build_urls_from_rss_df(rss_df: pd.DataFrame) -> pd.DataFrame:
    df = rss_df.copy()
    df["source"] = "rss"
    df["publish_time"] = pd.to_datetime(df["published"], errors="coerce").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df["url"] = df["link"]
    df["mp_name"] = df["source_name"]
    cols = ["publish_time", "mp_name", "title", "url", "source"]
    df = df[cols].sort_values(by="publish_time", ascending=False)
    return df


def filter_recent(df: pd.DataFrame, days: int) -> pd.DataFrame:
    cutoff = pd.to_datetime(friday_date) - pd.Timedelta(days=days)
    return df[pd.to_datetime(df["publish_time"]) >= cutoff].sort_values(
        by="publish_time", ascending=False
    )


def save_urls_outputs(df_all: pd.DataFrame, df_recent: pd.DataFrame) -> None:
    os.makedirs(URLS_DIR, exist_ok=True)
    csv_path = os.path.join(URLS_DIR, f"{friday_date}_article_urls.csv")
    xlsx_path = os.path.join(URLS_DIR, "article_urls.xlsx")

    df_recent.to_csv(csv_path, index=False)
    df_all.sort_values(by="publish_time", ascending=False).to_excel(xlsx_path, index=False)

    print(f"{os.path.basename(csv_path)} saved")
    print(f"{len(df_all)} total articles saved to Excel")

    send_feishu_notification(len(df_recent))


# ---------------------------
# Raw MD fetch/backfill (former 2_get_mds.py)
# ---------------------------
def backfill_rss_placeholders(urls_df: pd.DataFrame) -> None:
    print("RSS mode: verifying raw MDs; backfilling placeholders if missing.")
    missing = 0
    for _, row in urls_df.iterrows():
        url = row.get("url")
        source = row.get("source", "rss")
        rawfilename = f"{get_filename(url, source)}.md"
        output_path = os.path.join(RAW_MDS_DIR, rawfilename)
        if os.path.exists(output_path):
            continue

        try:
            missing += 1
            safe_title = row.get("title") or "Untitled"
            published = row.get("publish_time") or row.get("published") or ""
            mp_name = row.get("mp_name") or row.get("source_name") or ""
            placeholder = (
                "[No content extracted]\n"
                f"Source: {mp_name}\nTitle: {safe_title}\nLink: {url}\nPublished: {published}\n"
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(placeholder)
        except Exception as e:
            print(f"  Warning: failed to write placeholder for {url}: {e}")

    if missing:
        print(f"Backfilled {missing} placeholder MD(s) under {RAW_MDS_DIR}")
    else:
        print("All expected MDs present.")


def download_wechat_raw_mds(urls_df: pd.DataFrame) -> None:
    print(f"Processing {len(urls_df)} URLs (remote_db mode)")
    for _, row in urls_df.iterrows():
        url = row["url"]
        # Treat any mp.weixin links as wechat content regardless of 'source' label
        if "mp.weixin.qq.com" in url or row.get("source") in ("wechat", "wewerss"):
            filename = f"{get_filename(url, 'wechat')}.md"
            output_path = os.path.join(RAW_MDS_DIR, filename)
            if os.path.exists(output_path):
                continue

            remote_md_url = f"http://118.193.44.18:8000/data/articles/{friday_date}/{filename}"
            status = download_file(remote_md_url, output_path)
            if not status:
                last_friday_date = (dt.datetime.strptime(friday_date, "%Y-%m-%d") - dt.timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                )
                remote_md_url = f"http://118.193.44.18:8000/data/articles/{last_friday_date}/{filename}"
                download_file(remote_md_url, output_path)
        else:
            # Non-wechat URL in remote_db mode; nothing to fetch here
            continue
    print(f"Processed {len(urls_df)} URLs")


def main() -> None:
    # Archive existing outputs before generating new ones, but keep this week's
    # files/folders to allow caching and incremental runs.
    archive_existing_in_target(URLS_DIR, exclude_contains=[friday_date])
    archive_existing_in_target(RAW_MDS_ROOT_DIR, exclude_names=[friday_date])

    _ensure_dirs()
    _ensure_weekly_external_folders()

    if ARTICLE_SOURCE == "rss":
        # Step 0: RSS ingest + write raw mds
        rss_df = read_opml_feeds_to_df("rss_source.opml")
        merged_rss_df = save_and_merge_rss_articles(rss_df)

        if merged_rss_df.empty:
            print("No articles collected.")
            return

        # Step 1: Build URLs (recent + all) and save
        urls_all = build_urls_from_rss_df(merged_rss_df)
        urls_recent = filter_recent(urls_all, NEWS_LOOKBACK_DAYS)
        save_urls_outputs(urls_all, urls_recent)

        # Step 2: Backfill any missing raw MDs
        backfill_rss_placeholders(urls_recent)

    elif ARTICLE_SOURCE == "remote_db":
        # Step 1: Build URLs from DBs and save
        urls_all = build_urls_from_remote_db()
        urls_recent = filter_recent(urls_all, NEWS_LOOKBACK_DAYS)
        save_urls_outputs(urls_all, urls_recent)

        # Step 2: Download raw MDs for WeChat articles
        download_wechat_raw_mds(urls_recent)

    else:
        raise ValueError("Unknown ARTICLE_SOURCE. Use 'remote_db' or 'rss'.")


if __name__ == "__main__":
    main()
