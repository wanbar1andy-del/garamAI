
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path

# Config
TARGET_CODE = "005930" # Samsung Electronics
PAGES_TO_SCAN = 20 
DATA_DIR = Path("c:/garam/garam/GARAM_Data/sentiment")
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = Path("c:/garam/garam/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "community_sentiment.log"

def log_sentiment(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_sentiment_score(text):
    # Simple Keyword Dictionary
    propensity = 0
    # ... (rest same)

def scrape_naver_board(code=TARGET_CODE):
    log_sentiment(f"=== [Sentiment] Scanning Naver Finance Board ({code}) ===")
    
    base_url = "https://finance.naver.com/item/board.naver"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    all_posts = []
    
    for page in range(1, PAGES_TO_SCAN + 1):
        try:
            url = f"{base_url}?code={code}&page={page}"
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            rows = soup.select("table.type2 tbody tr")
            
            log_sentiment(f"Scanning page {page}...")
            
            for row in rows:
                if len(row.select("td")) < 5: continue # Skip line breaks
                
                try:
                    title_el = row.select_one(".title a")
                    date_el = row.select_one(".date")
                    views_el = row.select_one(".hit")
                    
                    if not title_el or not date_el: continue
                    
                    title = title_el.text.strip()
                    date_raw = date_el.text.strip() # YYYY.MM.DD HH:mm
                    views = int(views_el.text.strip())
                    
                    # Sentiment Analysis
                    score = get_sentiment_score(title)
                    
                    all_posts.append({
                        "date": date_raw,
                        "title": title,
                        "views": views,
                        "sentiment_score": score
                    })
                except:
                    continue
            
            time.sleep(0.2) # Polite delay
            
        except Exception as e:
            print(f"[Error] Page {page}: {e}")

    print(f"\n>> Captured {len(all_posts)} posts.")
    
    if all_posts:
        df = pd.DataFrame(all_posts)
        # Parse Dates
        df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d %H:%M')
        
        # Aggregate by Day
        df['day'] = df['date'].dt.date
        daily_sentiment = df.groupby('day').agg(
            posts_count=('title', 'count'),
            avg_sentiment=('sentiment_score', 'mean'),
            total_views=('views', 'sum')
        ).reset_index()
        
        save_path = DATA_DIR / f"{code}_daily.csv"
        daily_sentiment.to_csv(save_path, index=False)
        print(f">> Saved Daily Sentiment: {save_path}")
        print(daily_sentiment.tail())

if __name__ == "__main__":
    scrape_naver_board()
