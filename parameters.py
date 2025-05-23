# Calculate the date of the Friday of the current week
#%%
import datetime
import requests
import shutil

current_date = datetime.datetime.now()
days_until_friday = (6 - (current_date.weekday() + 2) % 7) % 7  # 6 represents Friday in this system
friday_date = (current_date + datetime.timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
errorkeywords=["微信，是一个生活方式","参数错误","LinkReader","微信输入法"]
sector_list=['商业落地','核心技术','政策监管','企业战略','硬件设备','数据与地图','资本动向']#%%


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
def get_filename(url,source):
    if source == 'wechat':
        return url.split('/')[-1]
    elif source == 'rss':
        return url.split('sn=')[-1].replace('=','').replace('&','')
    else:
        return url.split('/')[-1]