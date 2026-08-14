import os
import json
import time
import random
import urllib.request
import urllib.parse
from dotenv import load_dotenv
from brand_config import BRANDS
from analyzer.validator import summarize
import cache

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_ID = os.getenv("NAVER_ID")
NAVER_PW = os.getenv("NAVER_PW")

N_SAMPLES = 3


def _search_total(query, api_type="blog"):
    url = (f"https://openapi.naver.com/v1/search/{api_type}"
           f"?query={urllib.parse.quote(query)}&display=1")
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        time.sleep(random.uniform(0.3, 0.6))
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8")).get("total", 0)
    except Exception as e:
        print(f"    [Naver API 오류] {api_type}/{query}: {e}")
        return 0


def fetch_naver_counts(run_id, collected_at):
    cached = cache.get("naver_counts", {"brands": [b["name"] for b in BRANDS]})
    if cached:
        print("  [Naver] 캐시 사용")
        return cached

    print(f"  [Naver] {N_SAMPLES}회 샘플링 시작...")
    brand_samples = {b["name"]: [] for b in BRANDS}

    for i in range(N_SAMPLES):
        print(f"    샘플 {i + 1}/{N_SAMPLES}")
        for b in BRANDS:
            blog = _search_total(b["naver_kw"], "blog")
            news = _search_total(b["naver_kw"], "news")
            brand_samples[b["name"]].append(blog + news)

    stats_map = {}
    for name, samples in brand_samples.items():
        stats_map[name] = summarize(samples)

    base = stats_map.get("시몬스", {}).get("median", 1) or 1
    normalized = {}
    for name, stats in stats_map.items():
        normalized[name] = round(stats["median"] / base * 100, 1)

    print("\n  [Naver 검색 지수] 시몬스=100 기준")
    for name, idx in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
        conf = stats_map[name]["confidence"]
        print(f"    {name}: {idx} (CV={stats_map[name]['cv']}, {conf})")

    output = {"normalized": normalized, "stats": stats_map}
    cache.set("naver_counts", {"brands": [b["name"] for b in BRANDS]}, output, ttl_hours=12)
    return output


COOKIE_FILE = os.path.join(os.path.dirname(__file__), "..", "naver_cookies.json")


def _load_cookies():
    """저장된 쿠키 파일 또는 환경변수(NAVER_COOKIES_JSON)에서 쿠키 로드"""
    # GitHub Actions: 환경변수로 주입
    env_cookies = os.getenv("NAVER_COOKIES_JSON")
    if env_cookies:
        try:
            return json.loads(env_cookies)
        except Exception:
            pass
    # 로컬: 파일에서 로드
    cookie_path = os.path.normpath(COOKIE_FILE)
    if os.path.exists(cookie_path):
        with open(cookie_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# 연령대별 체크박스 ID (DataLab trendSearch 폼 기준)
# item_age_0=전체, 1=~12, 2=13-18, 3=19-24, 4=25-29, 5=30-34, 6=35-39,
# 7=40-44, 8=45-49, 9=50-54, 10=55-59, 11=60~
AGE_GROUPS = {
    "10대":  ["item_age_2"],
    "20대":  ["item_age_3", "item_age_4"],
    "30대":  ["item_age_5", "item_age_6"],
    "40대":  ["item_age_7", "item_age_8"],
    "50대":  ["item_age_9", "item_age_10"],
    "60대+": ["item_age_11"],
}


def _datalab_query(page, keyword, gender_id=None, age_ids=None):
    """trendSearch 폼 제출 → xlsx 다운로드 → 평균 ratio 반환"""
    import openpyxl, io as _io

    page.goto("https://datalab.naver.com/keyword/trendSearch.naver", timeout=20000)
    page.wait_for_timeout(1500)

    page.fill("#item_keyword1", "")
    page.type("#item_keyword1", keyword)
    page.wait_for_timeout(200)
    page.fill("#item_sub_keyword1_1", "")
    page.type("#item_sub_keyword1_1", keyword)
    page.wait_for_timeout(300)

    if gender_id:
        page.click(f"#{gender_id}")
        page.wait_for_timeout(200)

    if age_ids:
        for aid in age_ids:
            page.click(f"#{aid}")
            page.wait_for_timeout(100)

    with page.expect_navigation(timeout=15000):
        page.click(".ca_btn_go._trend_search_detail_query")
    page.wait_for_timeout(4000)

    with page.expect_download(timeout=15000) as dl_info:
        page.click("a.sp_btn_file_down", timeout=5000)
    dl = dl_info.value

    buf = _io.BytesIO()
    path = dl.path()
    with open(path, "rb") as f:
        buf.write(f.read())
    buf.seek(0)

    wb = openpyxl.load_workbook(buf)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    # 헤더 이후 날짜+값 행 파싱 (행 형식: (날짜문자열, 숫자))
    values = []
    for r in rows:
        if r and r[0] and r[1] is not None:
            try:
                val = float(r[1])
                # 날짜 형식 행만 (YYYY-MM-DD)
                if isinstance(r[0], str) and len(r[0]) == 10 and r[0][4] == "-":
                    values.append(val)
            except (TypeError, ValueError):
                pass

    if not values:
        return None
    return round(sum(values) / len(values), 1)


def fetch_naver_demographics(run_id, collected_at):
    """DataLab API (§12) 우선, 실패 시 Playwright + xlsx 폴백"""
    # DataLab API 시도 (전 브랜드 커버, 쿠키 불필요)
    try:
        from collector.naver_datalab_api import fetch_datalab_demographics
        result = fetch_datalab_demographics(run_id, collected_at)
        if result and any(
            any(v > 0 for v in d.get("gender", {}).values()) or
            any(v > 0 for v in d.get("age", {}).values())
            for d in result.values()
        ):
            print("  [DataLab 인구통계] API 수집 성공 (Playwright 건너뜀)")
            return result
        print("  [DataLab 인구통계] API 결과 없음 - Playwright 폴백")
    except Exception as e:
        print(f"  [DataLab 인구통계] API 오류, Playwright 폴백: {e}")

    cached = cache.get("naver_demo", {"id": NAVER_ID or "cookie"})
    if cached:
        print("  [DataLab] 캐시 사용")
        return cached

    cookies = _load_cookies()
    if not cookies:
        print("  [DataLab] 쿠키 없음 - save_cookies.py 먼저 실행하세요")
        return {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [DataLab] Playwright 없음")
        return {}

    keywords = ["시몬스", "에이스침대", "한샘", "씰리침대"]
    result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        try:
            # 쿠키 유효성 확인
            page.goto("https://datalab.naver.com", timeout=20000)
            page.wait_for_timeout(1500)
            if "login" in page.url or "nidlogin" in page.url:
                print("  [DataLab] 쿠키 만료 - save_cookies.py 재실행 필요")
                browser.close()
                return {}
            print("  [DataLab] 쿠키 인증 성공")

            for keyword in keywords:
                print(f"    키워드: {keyword}")
                kw_result = {"gender": {}, "age": {}}

                # 성별
                for gender_id, gender_label in [("item_gender_1", "여성"), ("item_gender_2", "남성")]:
                    try:
                        val = _datalab_query(page, keyword, gender_id=gender_id)
                        if val is not None:
                            kw_result["gender"][gender_label] = val
                        time.sleep(random.uniform(1, 2))
                    except Exception as e:
                        print(f"      [성별 오류] {gender_label}: {e}")

                # 연령대
                for age_label, age_ids in AGE_GROUPS.items():
                    try:
                        val = _datalab_query(page, keyword, age_ids=age_ids)
                        if val is not None:
                            kw_result["age"][age_label] = val
                        time.sleep(random.uniform(1, 2))
                    except Exception as e:
                        print(f"      [연령 오류] {age_label}: {e}")

                result[keyword] = kw_result
                print(f"      성별: {kw_result['gender']}")
                print(f"      연령: {kw_result['age']}")

        except Exception as e:
            print(f"  [DataLab] 오류: {e}")
        finally:
            browser.close()

    if result:
        cache.set("naver_demo", {"id": NAVER_ID or "cookie"}, result, ttl_hours=24)
    return result
