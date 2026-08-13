import time
from pytrends.request import TrendReq
from brand_config import BRANDS, TREND_GROUPS, SIMMONS_TREND_KW


def _build_with_retry(pytrends, group, retries=3):
    for attempt in range(retries):
        try:
            pytrends.build_payload(group, cat=0, timeframe='today 3-m', geo='KR')
            df = pytrends.interest_over_time()
            return df
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait = 30 * (attempt + 1)
                print(f"  [Google 429] {wait}s 대기 후 재시도...")
                time.sleep(wait)
            else:
                print(f"  [Google Trends 오류] {e}")
                return None
    return None


def fetch_rankings():
    """11개 브랜드 구글 트렌드 순위 (시몬스=100 기준 정규화)"""
    pytrends = TrendReq(hl='ko', tz=540)
    raw = {}

    for group in TREND_GROUPS:
        time.sleep(5)
        df = _build_with_retry(pytrends, group)
        if df is None or df.empty:
            continue
        for kw in group:
            if kw in df.columns:
                avg = round(float(df[kw].mean()), 1)
                if kw == SIMMONS_TREND_KW:
                    raw[kw] = max(raw.get(kw, 0), avg)
                else:
                    raw[kw] = avg

    base = raw.get(SIMMONS_TREND_KW, 0)
    if base == 0:
        print("  [Google Trends] 데이터 없음 - 네이버 데이터만 사용")
        return {b["name"]: 0 for b in BRANDS}

    normalized = {}
    for b in BRANDS:
        val = raw.get(b["trend_kw"], 0)
        normalized[b["name"]] = round((val / base) * 100, 1)

    normalized["시몬스"] = 100.0

    print("  [Google 검색 지수] 시몬스=100 기준")
    for name, idx in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {idx}")

    return normalized


def fetch_monthly_trend():
    """최근 12개월 월별 추이 - 상위 5개 브랜드"""
    pytrends = TrendReq(hl='ko', tz=540)
    keywords = ["시몬스", "에이스침대", "한샘", "이케아", "씰리침대"]

    try:
        time.sleep(5)
        df = _build_with_retry(pytrends, keywords)
        if df is None or df.empty:
            return {}, []

        df.index = df.index.to_period('M')
        monthly = df.groupby(df.index).mean()
        periods = [str(p) for p in monthly.index]

        result = {}
        for kw in keywords:
            if kw in monthly.columns:
                result[kw] = [round(float(v), 1) for v in monthly[kw]]
        return result, periods
    except Exception as e:
        print(f"  [월별 트렌드 오류] {e}")
        return {}, []
