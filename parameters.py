# Calculate the date of the Friday of the current week
#%%
import datetime
import os
import requests
import shutil
from urllib.parse import urlparse, parse_qs

current_date = datetime.datetime.now()
days_until_friday = (6 - (current_date.weekday() + 2) % 7) % 7  # 6 represents Friday in this system
friday_date = (current_date + datetime.timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
errorkeywords=["微信，是一个生活方式","参数错误","LinkReader","微信输入法"]
sector_list=['商业落地','核心技术','政策监管','企业战略','硬件设备','数据与地图','资本动向']#%%

# Article source selection: 'remote_db' or 'rss'
# Can be overridden via env var ARTICLE_SOURCE
ARTICLE_SOURCE = os.getenv('ARTICLE_SOURCE', 'rss').lower()


def download_file(url, local_path):        # Download the database file
    try:
        print(f"Downloading file from {url}...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
                print(f"File successfully downloaded to {local_path}")
                return True
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False
def get_filename(url, source):
    """Return a safe identifier for storing content fetched from a URL.

    - wechat: keep existing behavior (used by remote fetch paths); do not change.
    - rss: prefer the 'sn' query param when present; fallback to '/s/<id>' segment;
      finally fallback to an md5 of the URL to avoid illegal filename chars.
    - default: last path segment.
    """
    if not isinstance(url, str) or not url:
        return "unknown"

    if source == 'wechat':
        # Preserve legacy behavior to remain compatible with remote article store
        return url.split('/')[-1]
    elif source == 'rss':
        try:
            parsed = urlparse(url)
            q = parse_qs(parsed.query)
            sn = q.get('sn', [None])[0]
            if sn:
                return sn
            # Fallback: /s/<id> style links
            path_last = (parsed.path or '').strip('/').split('/')[-1]
            if path_last and path_last != 's':
                return path_last
            # Last-resort: stable hash of the URL
            import hashlib

            return hashlib.md5(url.encode('utf-8')).hexdigest()
        except Exception:
            # As a very last resort, strip problematic characters
            return url.replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_')
    else:
        return url.split('/')[-1]
