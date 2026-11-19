import json
import re
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

# 台灣/香港時間 (UTC+8)
tz_hk = timezone(timedelta(hours=8))
now_str = datetime.now(tz_hk).strftime("%m-%d %H:%M")
today_date = datetime.now(tz_hk).strftime("%m-%d")

# 預設資料結構
data = {
    "date": today_date,
    "update_time": now_str,
    "dam": "----",      # 零號大壩
    "grove": "----",    # 長弓溪谷
    "bakkesh": "----",  # 巴克什
    "space": "----",    # 航天基地
    "prison": "----"    # 潮汐監獄 (若有)
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_codes(text):
    patterns = {
        "dam": r"零号大坝[^\d]{0,15}(\d{4})",
        "grove": r"长弓溪谷[^\d]{0,15}(\d{4})",
        "bakkesh": r"巴克什[^\d]{0,15}(\d{4})",
        "space": r"航天基地[^\d]{0,15}(\d{4})",
        "prison": r"潮汐监狱[^\d]{0,15}(\d{4})"
    }
    found_any = False
    for key, pat in patterns.items():
        match = re.search(pat, text)
        if match:
            data[key] = match.group(1)
            found_any = True
    return found_any

# 嘗試從國服熱門攻略搜尋頁面抓取最新每日密碼
urls = [
    "https://gamersky.com",
    "https://17173.com"
]

for url in urls:
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        # 尋找包含「每日密码」或「密码门」的最新文章連結
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if ("每日密码" in title or "密码门" in title) and ("三角洲" in title or today_date.lstrip("0").replace("-0", "-") in title or True):
                article_url = a["href"]
                if not article_url.startswith("http"):
                    continue
                art_resp = requests.get(article_url, headers=headers, timeout=15)
                art_resp.encoding = "utf-8"
                art_text = BeautifulSoup(art_resp.text, "html.parser").get_text(" ", strip=True)
                if extract_codes(art_text):
                    break
        if data["dam"] != "----":
            break
    except Exception as e:
        print(f"Error fetching {url}: {e}")

with open("password.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated password.json:", data)
