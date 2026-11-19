import json
import re
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

# 香港時間 (UTC+8)
tz_hk = timezone(timedelta(hours=8))
now_str = datetime.now(tz_hk).strftime("%m-%d %H:%M")
today_date = datetime.now(tz_hk).strftime("%Y-%m-%d")

data = {
    "date": today_date,
    "update_time": now_str,
    "dam": "----",      # 零號大壩
    "grove": "----",    # 長弓溪谷
    "bakkesh": "----",  # 巴克什
    "space": "----",    # 航天基地
    "prison": "----",   # 潮汐監獄
    "az3": "----"       # AZ3
}

TARGET_URL = "https://orzice.com/v/index"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def parse_orzice_text(text):
    # 把多餘換行與空白壓縮成單一空格，對應「零号大坝 0211 长弓溪谷 9672...」結構
    clean_text = re.sub(r'\s+', ' ', text)
    patterns = {
        "dam": r"零号大坝\s*(\d{4})",
        "grove": r"长弓溪谷\s*(\d{4})",
        "bakkesh": r"巴克什\s*(\d{4})",
        "space": r"航天基地\s*(\d{4})",
        "prison": r"潮汐监狱\s*(\d{4})",
        "az3": r"AZ3\s*(\d{4})"
    }
    found = 0
    for key, pat in patterns.items():
        m = re.search(pat, clean_text)
        if m:
            data[key] = m.group(1)
            found += 1
            
    # 順便抓取網站上的「更新日期 2026-11-19」
    date_m = re.search(r"更新日期\s*(\d{4}-\d{2}-\d{2})", clean_text)
    if date_m:
        data["date"] = date_m.group(1)
        
    return found >= 3

# 1. 先嘗試快速 HTTP 請求抓取
success = False
try:
    resp = requests.get(TARGET_URL, headers=headers, timeout=15)
    resp.encoding = "utf-8"
    page_text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
    if parse_orzice_text(page_text):
        print("Fast HTTP scrape succeeded!")
        success = True
except Exception as e:
    print("Fast HTTP scrape error:", e)

# 2. 若網頁為動態 JS 渲染，自動啟動 Playwright 瀏覽器完整渲染後抓取
if not success:
    print("Trying Playwright headless browser rendering...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=headers["User-Agent"])
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            rendered_text = page.inner_text("body")
            if parse_orzice_text(rendered_text):
                print("Playwright scrape succeeded!")
            browser.close()
    except Exception as e:
        print("Playwright error:", e)

with open("password.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Final JSON output:", data)
