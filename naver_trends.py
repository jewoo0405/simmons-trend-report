import os
import json
import time
import urllib.request
import urllib.parse
from dotenv import load_dotenv
from brand_config import BRANDS

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def _search_total(query, api_type="blog"):
    url = (
        f"https://openapi.naver.com/v1/search/{api_type}"
        f"?query={urllib.parse.quote(query)}&display=1"
    )
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        time.sleep(0.4)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8")).get("total", 0)
    except Exception as e:
        print(f"  [Naver API 오류] {api_type}/{query}: {e}")
        return 0


def fetch_naver_counts():
    """블로그+뉴스 결과 수 합산 → 브랜드 관심도 추정"""
    counts = {}
    for b in BRANDS:
        blog = _search_total(b["query"], "blog")
        news = _search_total(b["query"], "news")
        counts[b["name"]] = blog + news
        print(f"  {b['name']}: 블로그 {blog:,} + 뉴스 {news:,} = {blog+news:,}")

    base = counts.get("시몬스", 1) or 1
    normalized = {name: round((v / base) * 100, 1) for name, v in counts.items()}
    return counts, normalized
