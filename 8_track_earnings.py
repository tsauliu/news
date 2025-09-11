"""
Step 8: Track earnings dates for selected companies.

What it does
- Uses headless Chrome (Selenium) to load investor relations pages.
- Sends the full page text to the OneAPI Gemini model to extract the next
  earnings date (or last if no next, or none).
- Builds a series of bullets, adding "!!!" if the next date is within 7 days.
- Sends the result to Feishu via the provided incoming webhook.

Usage
- python 8_track_earnings.py

Configuration
- Override Feishu webhook using env var `FEISHU_WEBHOOK_URL` if needed.
- Adjust the `TARGETS` dict for companies and URLs.

Notes
- Requires a Chrome installation; Selenium will attempt to manage the driver.
- Network calls occur when fetching pages and posting to Feishu.
"""

from __future__ import annotations

import json
import os
import re
import time
import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from models import OneAPI_request


# --- Config -----------------------------------------------------------------

# Feishu webhook (override via env var to avoid committing secrets)
FEISHU_WEBHOOK_URL = os.getenv(
    "FEISHU_WEBHOOK_URL",
    "https://open.feishu.cn/open-apis/bot/v2/hook/869f9457-6d3d-4f88-8bee-d21c41b11625",
)

# Company targets
TARGETS: Dict[str, str] = {
    "pony": "https://ir.pony.ai/news-events/press-releases",
    "weride": "https://ir.weride.ai/news-events/news-releases",
    "bidu": "https://ir.baidu.com/press-releases",
    "horizon robotics": "https://ir.horizon.auto/calendar/index.html",
}


# --- Data structures ---------------------------------------------------------

@dataclass
class EarningsResult:
    company: str
    status: str  # "next", "last", or "none"
    date: Optional[dt.date]
    raw_date: str = ""
    confidence: Optional[float] = None
    url: str = ""
    error: Optional[str] = None


# --- Selenium page fetch -----------------------------------------------------

def _init_headless_chrome() -> webdriver.Chrome:
    """Create a headless Chrome webdriver instance with safe defaults."""
    options = Options()
    # Prefer new headless mode for stability
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Reduce noise
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # type: ignore[arg-type]
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(5)
    return driver

def _scroll_to_bottom(driver: webdriver.Chrome, max_steps: int = 10, pause: float = 0.6) -> None:
    last_height = driver.execute_script("return document.body.scrollHeight")
    steps = 0
    while steps < max_steps:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        steps += 1


def fetch_page_text(url: str, wait_selector: Optional[Tuple[By, str]] = None, *, do_scroll: bool = True) -> str:
    """Fetch page content using requests+BS4 first; fallback to headless Chrome.

    Keeps it simple and fast where possible, while remaining robust.
    """
    # First try simple HTTP GET with realistic headers
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "close",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200 and resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text("\n", strip=True)
            text = re.sub(r"\n{2,}", "\n", text)
            # If the content seems substantive, return it; else try Selenium
            if len(text) > 500 and "access denied" not in text.lower():
                return text
    except Exception as e:
        print(f"Requests fetch failed for {url}: {e}. Trying Selenium...")

    # Fallback to Selenium for dynamic sites
    try:
        driver = _init_headless_chrome()
        try:
            driver.get(url)
            if wait_selector:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located(wait_selector))
                time.sleep(3.5)
            else:
                time.sleep(2.0)
            if do_scroll:
                _scroll_to_bottom(driver)
            texts: List[str] = []
            try:
                main_text = driver.execute_script("return document.body.innerText || '';")
                if isinstance(main_text, str) and main_text.strip():
                    texts.append(main_text)
            except Exception:
                pass
            try:
                frames = driver.find_elements(By.TAG_NAME, "iframe")
                for fr in frames[:6]:
                    try:
                        driver.switch_to.frame(fr)
                        time.sleep(0.5)
                        fr_text = driver.execute_script("return document.body.innerText || '';")
                        if isinstance(fr_text, str) and len(fr_text.strip()) > 0:
                            texts.append(fr_text)
                    except Exception:
                        continue
                    finally:
                        driver.switch_to.default_content()
            except Exception:
                pass
            if not texts:
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                texts.append(soup.get_text("\n", strip=True))
            text = "\n\n".join(texts)
        finally:
            driver.quit()
        text = re.sub(r"\n{2,}", "\n", text)
        return text
    except Exception as e:
        print(f"Selenium failed for {url}: {e}")
        return ""


def fetch_page_text_and_links(url: str, *, max_click_rounds: int = 4) -> Tuple[str, List[str]]:
    """Fetch page text and collect links after scrolling/clicking 'load more'.

    Returns (text, absolute_links).
    """
    text = ""
    links: List[str] = []
    try:
        driver = _init_headless_chrome()
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Try clicking common 'load more' patterns a few times
            for _ in range(max_click_rounds):
                clicked = False
                for t in ["load more", "more", "next", "show more", "view more"]:
                    try:
                        el = driver.find_element(
                            By.XPATH,
                            f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{t}')] | "
                            f"//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{t}')]",
                        )
                        el.click()
                        time.sleep(0.8)
                        clicked = True
                        break
                    except Exception:
                        pass
                if not clicked:
                    break

            _scroll_to_bottom(driver, max_steps=14, pause=0.4)
            html = driver.page_source
        finally:
            driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        text = re.sub(r"\n{2,}", "\n", text)
        for a in soup.find_all("a", href=True):
            links.append(urljoin(url, a["href"]))
        return text, links
    except Exception as e:
        print(f"fetch_page_text_and_links fallback for {url}: {e}")
        # Fallback to earlier method
        return fetch_page_text(url), []


def fetch_company_corpus(company: str, url: str) -> str:
    """Fetch primary page text plus relevant detail pages for better recall.

    Strategy by site type:
    - Press releases pages (pony, bidu, weride): pull the landing page and also
      follow up to 3 recent links whose text suggests earnings/financial results.
    - Event calendar (horizon robotics): landing page should suffice.
    """
    base_text = fetch_page_text(url, wait_selector=(By.TAG_NAME, "body"), do_scroll=True)
    if not base_text:
        return base_text

    # Only the first page content is used per user guidance
    corpus = f"=== SOURCE: {url} ===\n{base_text}"
    # Trim very large corpus to keep LLM input manageable
    if len(corpus) > 120000:
        corpus = corpus[:120000]
    return corpus


# --- LLM extraction ----------------------------------------------------------

EXTRACTION_PROMPT = (
    "You are an expert financial events extractor.\n"
    "Input is concatenated sections labeled as '=== SOURCE: <url> ==='.\n"
    "Goal: Identify the company's earnings-related date (future preferred). Follow these rules:\n"
    "1) If a future earnings-related event is explicitly stated (e.g., 'to report ... on Aug. 12, 2025', 'will announce results on August 12, 2025', 'earnings call on 2025-08-12'), output status 'next' and that date.\n"
    "2) Otherwise, if past earnings-related date is given (e.g., 'reported results on August 1, 2025'), output status 'last' and that date.\n"
    "3) If neither appears, output status 'none' and date ''.\n"
    "Earnings-related includes: earnings release, financial results, quarterly/annual results, earnings call/webcast, results announcement.\n"
    "Date formats to recognize: 'Aug. 12, 2025', 'August 12, 2025', '12 August 2025', '2025-08-12'. Always output as YYYY-MM-DD.\n"
    "If multiple future dates exist, pick the nearest upcoming. If only past dates, pick the most recent past. Do NOT infer approximate dates.\n"
    "Return ONLY a single JSON object with keys exactly: {status: 'next'|'last'|'none', date: 'YYYY-MM-DD' or '', confidence: number 0..1}. No prose, no code fences.\n"
)


def _parse_date_yyyy_mm_dd(s: str) -> Optional[dt.date]:
    try:
        return dt.datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _fallback_find_any_date(text: str) -> Optional[str]:
    """Best-effort regex to pick any YYYY-MM-DD from text (last resort)."""
    m = re.search(r"(20[0-9]{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12][0-9]|3[01])", text)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return dt.date(y, mo, d).strftime("%Y-%m-%d")
    except Exception:
        return None


def extract_earnings(company: str, url: str, page_text: str) -> EarningsResult:
    today = dt.date.today()
    context = (
        f"Company: {company}\n"
        f"URL: {url}\n"
        f"Today: {today.isoformat()}\n"
        "--- BEGIN PAGE TEXT ---\n"
        f"{page_text[:80000]}\n"  # trim to avoid huge context; adjust if needed
        "--- END PAGE TEXT ---"
    )

    raw = OneAPI_request(EXTRACTION_PROMPT, context, model="gemini-2.5-pro")
    status = "none"
    date_str = ""
    conf: Optional[float] = None

    if raw:
        # Try parse JSON strictly; if model returns extra text, extract JSON block
        json_block = None
        try:
            json_block = json.loads(raw)
        except Exception:
            # Attempt to find a JSON object in the response
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    json_block = json.loads(m.group(0))
                except Exception:
                    json_block = None
        if isinstance(json_block, dict):
            status = str(json_block.get("status", "none")).lower()
            date_str = str(json_block.get("date", "")).strip()
            try:
                conf_val = json_block.get("confidence")
                conf = float(conf_val) if conf_val is not None else None
            except Exception:
                conf = None

    # Last-resort fallback
    if status not in {"next", "last", "none"}:
        status = "none"

    parsed_date = _parse_date_yyyy_mm_dd(date_str) if date_str else None
    # Heuristic extraction to improve recall on PR headlines
    h_status, h_date = heuristic_extract_next_or_last(page_text)
    if h_date:
        h_parsed = _parse_date_yyyy_mm_dd(h_date)
        if h_parsed:
            # Prefer heuristic when model says none or provided no date
            if status == "none" or not parsed_date:
                status = h_status
                parsed_date = h_parsed
                date_str = h_date
            else:
                # If both exist but disagree on status recency, pick the nearer to future
                try:
                    if status != "next" and h_status == "next":
                        parsed_date = h_parsed
                        date_str = h_date
                        status = h_status
                except Exception:
                    pass
    if not parsed_date and page_text:
        # Robust fallback: scan all dates (month-name and numeric) and pick nearest
        f_status, f_date = fallback_scan_all_dates(page_text)
        if f_date:
            parsed_date = _parse_date_yyyy_mm_dd(f_date)
            if parsed_date:
                status = f_status
                date_str = f_date

    return EarningsResult(
        company=company,
        status=status,
        date=parsed_date,
        raw_date=date_str,
        confidence=conf,
        url=url,
        error=None if (status in {"next", "last"} or status == "none") else "unrecognized status",
    )


# --- Heuristic parsing -------------------------------------------------------

_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _parse_month_name_date(text: str) -> Optional[str]:
    """Parse MonthName DD, YYYY patterns including abbreviated months.
    Returns YYYY-MM-DD if found.
    """
    # Allow optional dot after abbreviated month (e.g., Aug. 12, 2025)
    pattern = re.compile(
        r"\b(" + "|".join(sorted({k for k in _MONTHS if len(k) > 3}, key=len, reverse=True)) + r"|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+([0-9]{1,2}),\s+(20[0-9]{2})",
        re.IGNORECASE,
    )
    m = pattern.search(text)
    if not m:
        return None
    mon_name = m.group(1).lower().rstrip(".")
    day = int(m.group(2))
    year = int(m.group(3))
    # Normalize month key
    if mon_name in _MONTHS:
        month = _MONTHS[mon_name]
    else:
        month = _MONTHS.get(mon_name[:3], 0)
    if not month:
        return None
    try:
        d = dt.date(year, month, day)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None


def heuristic_extract_next_or_last(text: str) -> Tuple[str, Optional[str]]:
    """Best-effort extraction of earnings-related date using keyword proximity.

    Returns tuple(status, date_str_or_None).
    """
    if not text:
        return "none", None

    keywords = [
        "financial results", "earnings", "results announcement", "quarter", "earnings call", "earnings webcast",
        "to report", "will report", "to announce", "will announce",
    ]
    lower = text.lower()
    today = dt.date.today()

    # Search windows around keywords
    indices: List[Tuple[int, int]] = []
    for kw in keywords:
        start = 0
        while True:
            idx = lower.find(kw, start)
            if idx == -1:
                break
            window_start = max(0, idx - 120)
            window_end = min(len(text), idx + len(kw) + 120)
            indices.append((window_start, window_end))
            start = idx + len(kw)

    # Merge overlapping windows
    indices.sort()
    merged: List[Tuple[int, int]] = []
    for s, e in indices:
        if not merged or s > merged[-1][1]:
            merged.append((s, e))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))

    candidates: List[Tuple[dt.date, str]] = []
    for s, e in merged[:8]:  # limit
        window = text[s:e]
        # Month name pattern first
        d1 = _parse_month_name_date(window)
        if d1:
            parsed = _parse_date_yyyy_mm_dd(d1)
            if parsed:
                candidates.append((parsed, d1))
                continue
        # Fallback numeric date in window
        d2 = _fallback_find_any_date(window)
        if d2:
            parsed = _parse_date_yyyy_mm_dd(d2)
            if parsed:
                candidates.append((parsed, d2))

    if not candidates:
        return "none", None

    # Prefer the soonest future date; else most recent past
    future = [c for c in candidates if c[0] >= today]
    if future:
        future.sort(key=lambda x: x[0])
        return "next", future[0][1]
    # Past
    candidates.sort(key=lambda x: x[0], reverse=True)
    return "last", candidates[0][1]


def _find_all_month_name_dates(text: str) -> List[str]:
    """Find all MonthName DD, YYYY style dates; return list of YYYY-MM-DD strings."""
    pattern = re.compile(
        r"\b(" + "|".join(sorted({k for k in _MONTHS if len(k) > 3}, key=len, reverse=True)) + r"|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+([0-9]{1,2}),\s+(20[0-9]{2})",
        re.IGNORECASE,
    )
    out: List[str] = []
    for m in pattern.finditer(text):
        mon_name = m.group(1).lower().rstrip(".")
        day = int(m.group(2))
        year = int(m.group(3))
        month = _MONTHS.get(mon_name, _MONTHS.get(mon_name[:3], 0))
        if not month:
            continue
        try:
            d = dt.date(year, month, day)
            out.append(d.strftime("%Y-%m-%d"))
        except Exception:
            continue
    return out


def _find_all_numeric_dates(text: str) -> List[str]:
    """Find all YYYY-MM-DD (or with / .) numeric-like dates; return YYYY-MM-DD strings."""
    pattern = re.compile(r"(20[0-9]{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12][0-9]|3[01])")
    out: List[str] = []
    for m in pattern.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            out.append(dt.date(y, mo, d).strftime("%Y-%m-%d"))
        except Exception:
            continue
    return out


def fallback_scan_all_dates(text: str) -> Tuple[str, Optional[str]]:
    """Scan whole text for any plausible dates; choose nearest upcoming else latest past.

    Returns (status, YYYY-MM-DD or None)
    """
    dates = set(_find_all_month_name_dates(text) + _find_all_numeric_dates(text))
    if not dates:
        return "none", None
    today = dt.date.today()
    parsed = []
    for ds in dates:
        d = _parse_date_yyyy_mm_dd(ds)
        if d:
            parsed.append(d)
    if not parsed:
        return "none", None
    future = sorted([d for d in parsed if d >= today])
    if future:
        return "next", future[0].strftime("%Y-%m-%d")
    past = sorted(parsed, reverse=True)
    return "last", past[0].strftime("%Y-%m-%d")


# --- Output composition ------------------------------------------------------

def _is_within_next_week(d: dt.date) -> bool:
    today = dt.date.today()
    delta = (d - today).days
    return 0 <= delta <= 7


def format_bullet(res: EarningsResult) -> str:
    if res.status == "none" or not res.date:
        return f"- {res.company}: none"
    flag = " !!!" if res.status == "next" and _is_within_next_week(res.date) else ""
    return f"- {res.company}: {res.status} {res.date.strftime('%Y-%m-%d')}{flag}"


def build_message(results: Dict[str, EarningsResult]) -> str:
    lines = [format_bullet(r) for r in results.values()]
    return "\n".join(lines)


# --- Feishu posting ----------------------------------------------------------

def post_to_feishu(text: str) -> Tuple[bool, str]:
    if not FEISHU_WEBHOOK_URL:
        return False, "FEISHU_WEBHOOK_URL not set"
    payload = {"msg_type": "text", "content": {"text": text}}
    try:
        resp = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, "ok"
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


# --- Main -------------------------------------------------------------------

def main() -> None:
    results: Dict[str, EarningsResult] = {}

    # Optional per-site selectors in case dynamic loads need waiting
    wait_map: Dict[str, Optional[Tuple[By, str]]] = {
        "pony": (By.TAG_NAME, "body"),
        "weride": (By.TAG_NAME, "body"),
        "bidu": (By.TAG_NAME, "body"),
        "horizon robotics": (By.TAG_NAME, "body"),
    }

    for company, url in TARGETS.items():
        print(f"Fetching: {company} -> {url}")
        text = fetch_company_corpus(company, url)
        if not text:
            results[company] = EarningsResult(
                company=company,
                status="none",
                date=None,
                raw_date="",
                confidence=None,
                url=url,
                error="failed to fetch page",
            )
            continue

        res = extract_earnings(company, url, text)
        results[company] = res

    message = build_message(results)
    print("\nEarnings dates:")
    print(message)

    ok, info = post_to_feishu(message)
    print(f"\nFeishu post: {'success' if ok else 'failed'} - {info}")


if __name__ == "__main__":
    main()
