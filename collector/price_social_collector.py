"""
가격·소셜·리뷰 수집기
- 3. 네이버 쇼핑: 브랜드별 최저가 + 상품 수 + 리뷰 수/평점 (쿠키 인증)
- 4. 유튜브: 공식 채널 구독자 수
- 5. 네이버 쇼핑 리뷰: 상위 상품 리뷰 수·평점
"""
import os, re, time, random, json, urllib.parse
from dotenv import load_dotenv
from brand_config import BRANDS

load_dotenv()

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "..", "naver_cookies.json")


def _load_cookies():
    env_c = os.getenv("NAVER_COOKIES_JSON")
    if env_c:
        try:
            return json.loads(env_c)
        except Exception:
            pass
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def _parse_price(text):
    m = re.search(r'([\d,]{3,})', text.replace(' ', ''))
    if not m:
        return None
    val = int(m.group(1).replace(',', ''))
    return val if 10000 <= val <= 100000000 else None


def _parse_count(text):
    text = text.strip()
    if '만' in text:
        m = re.search(r'([\d.]+)만', text)
        if m:
            return int(float(m.group(1)) * 10000)
    m = re.search(r'[\d,]+', text)
    return int(m.group(0).replace(',', '')) if m else 0


# ── Naver Shopping (가격 + 리뷰) ──────────────────────────────
def fetch_price_data(run_id, collected_at):
    """네이버 쇼핑에서 브랜드별 최저가 + 리뷰 수집 (로그인 쿠키 사용)"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [가격] Playwright 없음")
        return {}

    cookies = _load_cookies()
    results = {}
    print("  [가격·리뷰] 네이버 쇼핑 수집...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        if cookies:
            ctx.add_cookies(cookies)
        page = ctx.new_page()

        for b in BRANDS:
            name = b["name"]
            kw   = b.get("shop_kw", name + " 매트리스")
            enc  = urllib.parse.quote(kw)
            url  = (f"https://search.shopping.naver.com/search/all"
                    f"?query={enc}&sort=price_asc")
            try:
                page.goto(url, timeout=25000)
                # 로그인 리다이렉트 감지
                if "nidlogin" in page.url:
                    print(f"  [가격] 로그인 필요 — 쿠키 만료. save_cookies.py 재실행 후 다시 시도.")
                    browser.close()
                    return results
                page.wait_for_timeout(3000)

                body_text = page.locator("body").inner_text(timeout=8000)

                # 가격 패턴: "890,000원" 형태를 본문에서 추출
                raw_prices = re.findall(r'([\d,]{4,})\s*원', body_text)
                prices = []
                for rp in raw_prices:
                    v = _parse_price(rp + "원")
                    if v:
                        prices.append(v)

                # 총 상품 수: "총 N개" 또는 "N개의 상품"
                count_m = re.search(r'총\s*([\d,]+)\s*개', body_text)
                if not count_m:
                    count_m = re.search(r'([\d,]+)\s*개의?\s*(?:상품|검색결과)', body_text)
                product_count = _parse_count(count_m.group(1)) if count_m else len(prices)

                # 리뷰 수: "리뷰 N개" 또는 "N개 리뷰"
                rev_m = re.search(r'리뷰\s*([\d,]+)', body_text)
                review_count = _parse_count(rev_m.group(1)) if rev_m else 0

                # 별점: "4.8점" 또는 "평점 4.8"
                star_m = re.search(r'(?:평점|별점|★|☆)\s*(\d+\.\d+)', body_text)
                if not star_m:
                    star_m = re.search(r'(\d+\.\d+)\s*점', body_text)
                rating = float(star_m.group(1)) if star_m and 0 < float(star_m.group(1)) <= 5 else None

                min_price = min(prices) if prices else None
                avg_price = round(sum(prices) / len(prices)) if prices else None

                results[name] = {
                    "min_price": min_price,
                    "avg_price": avg_price,
                    "product_count": product_count,
                    "review_count": review_count,
                    "rating": rating,
                    "keyword": kw,
                }
                if min_price:
                    print(f"    {name}: 최저 {min_price:,}원 | {product_count}개 상품 | 리뷰 {review_count}")
                else:
                    print(f"    {name}: 가격 파싱 실패 (상품수={product_count})")
                time.sleep(random.uniform(1.2, 2.0))

            except Exception as e:
                print(f"    {name}: 오류 — {e}")
                results[name] = {"min_price": None, "avg_price": None,
                                 "product_count": 0, "review_count": 0, "rating": None, "keyword": kw}

        browser.close()
    return results


# ── YouTube 구독자 수 ──────────────────────────────────────────
def _parse_subscribers(text):
    """'12.3만명 구독' → 123000"""
    text = text.replace(' ', '').replace(',', '')
    if '만' in text:
        m = re.search(r'([\d.]+)만', text)
        if m:
            return int(float(m.group(1)) * 10000)
    if '천' in text:
        m = re.search(r'([\d.]+)천', text)
        if m:
            return int(float(m.group(1)) * 1000)
    # K/M suffixes (영문)
    if 'M' in text:
        m = re.search(r'([\d.]+)M', text)
        if m:
            return int(float(m.group(1)) * 1000000)
    if 'K' in text:
        m = re.search(r'([\d.]+)K', text)
        if m:
            return int(float(m.group(1)) * 1000)
    m = re.search(r'\d+', text)
    return int(m.group(0)) if m else 0


# 브랜드별 YouTube 검색 키워드 (공식 채널 찾기 최적화)
_YT_SEARCH_OVERRIDE = {
    "시몬스":       "시몬스침대 공식",
    "에이스침대":   "에이스침대 공식채널",
    "씰리침대":     "씰리침대 SEALY Korea",
    "지누스":       "지누스 Zinus Korea",
    "코웨이 비렉스":"코웨이 공식",
    "한샘":         "한샘 공식채널",
    "현대리바트":   "현대리바트 공식",
    "까사미아":     "까사미아 CASAMIA",
    "일룸":         "일룸 공식채널",
    "에몬스":       "에몬스가구 공식",
    "이케아":       "IKEA Korea 이케아",
}


def fetch_social_data(run_id, collected_at):
    """YouTube 공식 채널 구독자 수 수집"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [소셜] Playwright 없음")
        return {}

    results = {}
    print("  [소셜] YouTube 구독자 수 수집...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            locale="ko-KR",
        )
        page = ctx.new_page()

        for b in BRANDS:
            name = b["name"]
            kw   = _YT_SEARCH_OVERRIDE.get(name, b.get("youtube", name))
            enc  = urllib.parse.quote(kw)
            # 채널 필터 (sp=EgIQAg%3D%3D)
            url  = f"https://www.youtube.com/results?search_query={enc}&sp=EgIQAg%3D%3D"
            subs = None
            try:
                page.goto(url, timeout=20000)
                page.wait_for_timeout(3000)
                body_text = page.locator("body").inner_text(timeout=8000)

                # 구독자 패턴: "구독자 12.3만명" / "구독자 123,456명" / "123K subscribers"
                patterns = [
                    r'구독자\s*([\d.,]+\s*[만천명KMk]*)',
                    r'([\d.,]+\s*[만천])\s*명?\s*구독',
                    r'([\d.,]+[KM])\s*subscribers',
                    r'subscribers\s*([\d.,]+[KM]?)',
                ]
                for pat in patterns:
                    m = re.search(pat, body_text)
                    if m:
                        v = _parse_subscribers(m.group(1))
                        # 1명은 오탐 — 최소 100명 이상만 유효
                        if v and v >= 100:
                            subs = v
                            break

                results[name] = {
                    "youtube_subscribers": subs,
                    "youtube_search_kw": kw,
                }
                print(f"    {name}: {subs:,}명" if subs else f"    {name}: 수집 실패")
                time.sleep(random.uniform(1.5, 2.5))

            except Exception as e:
                print(f"    {name}: 오류 — {e}")
                results[name] = {"youtube_subscribers": None, "youtube_search_kw": kw}

        browser.close()
    return results
