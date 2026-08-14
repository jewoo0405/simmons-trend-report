"""
네이버 증권 + Playwright 재무 스크래핑 — API 키 불필요
상장사 5개 브랜드 연간 매출액 수집

비상장(시몬스, 이케아, 씰리침대, 까사미아, 에몬스, 일룸) 수집 불가
⚠ 브랜드 = 침대 외 사업 포함으로 직접 비교 주의
"""
import re
import time
import random
import cache
from io import StringIO

import pandas as pd

STOCK_CODES = {
    "에이스침대":    "003800",  # KOSDAQ
    "한샘":          "009240",  # KOSPI
    "현대리바트":    "079430",  # KOSPI
    "지누스":        "013890",  # KOSPI
    "코웨이 비렉스": "021240",  # KOSPI (코웨이 전체)
}
CAUTION = {"한샘", "현대리바트", "코웨이 비렉스"}
NOTES = {
    "에이스침대":    "매트리스 전업",
    "한샘":          "종합 가구 포함",
    "현대리바트":    "종합 가구 포함",
    "지누스":        "매트리스 전업",
    "코웨이 비렉스": "코웨이 전체 매출 (비렉스 분리 불가)",
}


def _lookup_stock_code(keyword):
    """
    ac.stock.naver.com 자동완성 API로 종목코드 조회 (Playwright 불필요).
    STOCK_CODES에 없는 브랜드 추가 시 폴백으로 사용.
    """
    import urllib.request
    import urllib.parse
    import json

    q = urllib.parse.quote(keyword)
    url = f"https://ac.stock.naver.com/ac?q={q}&target=stock,index,marketindicator"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            items = data.get("items", [])
            for item in items:
                if isinstance(item, dict):
                    return item.get("code")
        return None
    except Exception:
        return None


def _extract_annual_revenue(df):
    """
    WiseReport 연간실적 DataFrame에서 가장 최근 연간 매출액(억원) 추출.
    MultiIndex 컬럼 처리 포함.
    """
    # 컬럼 레벨1 평탄화
    if isinstance(df.columns, pd.MultiIndex):
        col_names = [str(c[1]) if len(c) > 1 else str(c[0]) for c in df.columns]
    else:
        col_names = [str(c) for c in df.columns]

    # 매출액 행
    first_col = df.iloc[:, 0].astype(str)
    if "매출액" not in first_col.values:
        return None, None
    idx = first_col.tolist().index("매출액")
    row = df.iloc[idx]

    # 연간(YYYY/12) 비예측 컬럼 역순 탐색
    annual = [
        (ci, col)
        for ci, col in enumerate(col_names)
        if re.search(r"\d{4}/12", col) and "(E)" not in col
    ]
    annual.sort(key=lambda x: x[1], reverse=True)  # 최신 연도 우선

    for ci, col in annual:
        val = row.iloc[ci]
        try:
            amount = float(str(val).replace(",", ""))
            if amount > 0:
                year = re.search(r"(\d{4})/12", col).group(1)
                return int(amount), year
        except (ValueError, TypeError):
            continue
    return None, None


def _get_revenue(page, code, brand):
    """네이버 증권 → WiseReport iframe에서 매출액 추출"""
    page.goto(
        f"https://finance.naver.com/item/coinfo.naver?code={code}",
        timeout=30000,
    )
    page.wait_for_timeout(4000)

    for frame in page.frames:
        if "wisereport" not in frame.url:
            continue
        try:
            content = frame.content()
            tables = pd.read_html(StringIO(content), thousands=",")
            for df in tables:
                amount, year = _extract_annual_revenue(df)
                if amount:
                    return amount, year
        except Exception:
            pass
    return None, None


def fetch_dart_revenues(target_year=None):
    """
    네이버 증권에서 상장 브랜드 연간 매출액 수집.
    Returns: {brand: {amount(억원), year, unit, caution, note, source}}
    """
    cache_key = {"brands": sorted(STOCK_CODES.keys()), "v": 3}
    cached = cache.get("naver_revenue", cache_key)
    if cached:
        print("  [매출] 캐시 사용")
        return cached

    print(f"  [매출] 네이버 증권 스크래핑 ({len(STOCK_CODES)}개 상장사)")
    results = {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [매출] Playwright 없음")
        return {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900},
        )

        for brand, code in STOCK_CODES.items():
            time.sleep(random.uniform(0.5, 1.0))
            try:
                amount, year = _get_revenue(page, code, brand)
                if amount:
                    caution = brand in CAUTION
                    results[brand] = {
                        "amount": amount,
                        "year": year,
                        "unit": "억원",
                        "caution": caution,
                        "note": NOTES.get(brand, ""),
                        "source": "naver_finance",
                    }
                    mark = " ⚠" if caution else ""
                    print(f"    {brand} ({code}): {amount:,}억원 ({year}){mark}")
                else:
                    print(f"    {brand} ({code}): 매출액 파싱 실패")
            except Exception as e:
                print(f"    {brand} ({code}): 오류 - {e}")

        browser.close()

    if results:
        cache.set("naver_revenue", cache_key, results, ttl_hours=24 * 7)
    return results
