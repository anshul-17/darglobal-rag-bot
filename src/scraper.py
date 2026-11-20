import os
import json
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

WASALT_URLS = [
    "https://wasalt.sa/en",
    "https://wasalt.sa/en/corporate",
    "https://wasalt.sa/en/properties-for-daily-rental-in-saudi-arabia",
    "https://blog.wasalt.sa/en/top-5-darglobal-real-estate-investment-projects/",
]

DARGLOBAL_URLS = [
    "https://darglobal.co.uk/",
    "https://darglobal.co.uk/projects/properties-in-saudi-arabia",
    "https://darglobal.co.uk/projects/properties-in-oman",
    "https://darglobal.co.uk/invest-in-aida",
    "https://darglobal.co.uk/the-astera",
    "https://darglobal.co.uk/partners/pagani",
    "https://darglobal.co.uk/blog/Whats-Next-for-DarGlobal-A-Sneak-Peek-into-Our-Upcoming-Projects",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def chunk_and_append(documents, url, title, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    blocks = [
        el.get_text(" ", strip=True)
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"])
        if len(el.get_text(strip=True)) > 35
    ]
    clean_text = "\n".join(dict.fromkeys(blocks))

    chunk_size, overlap = 800, 100
    for start in range(0, len(clean_text), chunk_size - overlap):
        chunk = clean_text[start: start + chunk_size].strip()
        if len(chunk) > 80:
            documents.append({
                "source": url,
                "title": title,
                "content": chunk,
            })
    return len(clean_text)


def run_scraper():
    documents = []

    # 1. Scrape Wasalt via requests
    for url in WASALT_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            chars = chunk_and_append(documents, url, title, resp.text)
            print(f"[OK - Wasalt] {url} -> {chars} chars extracted")
            time.sleep(1)
        except Exception as e:
            print(f"[WARN] Failed {url}: {e}")

    # 2. Scrape DarGlobal via headless Chromium (bypasses JS/bot shell)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = context.new_page()

        for url in DARGLOBAL_URLS:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait 3s for React content to render
                page.wait_for_timeout(3000)
                html = page.content()
                title = page.title() or url
                chars = chunk_and_append(documents, url, title, html)
                print(f"[OK - DarGlobal] {url} -> {chars} chars extracted")
            except Exception as e:
                print(f"[WARN] Failed {url}: {e}")

        browser.close()

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"\nDone! Saved {len(documents)} total chunks to {output_path}")


if __name__ == "__main__":
    run_scraper()
