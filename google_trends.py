import time
from pytrends.request import TrendReq
from brand_config import BRANDS, TREND_GROUPS, SIMMONS_KEY

def fetch_rankings():
    """11개 브랜드 구글 트렌드 순위 (시몬스=100 기준 정규화)"""
    pytrends = TrendReq(hl='ko', tz=540)
    raw = {}

    for group in TREND_GROUPS:
        time.sleep(3)
        try:
            pytrends.build_payload(group, cat=0, timeframe='today 3-m', geo='KR')
            df = pytrends.interest_over_time()
            if df.empty:
                continue
            for kw in group:
                if kw in df.columns:
                    avg = round(float(df[kw].mean()), 1)
                    if kw == SIMMONS_KEY:
                        raw[kw] = max(raw.get(kw, 0), avg)
                    else:
                        raw[kw] = avg
        except Exception as e:
            print(f"  [Google Trends 오류] {group[0]}~: {e}")

    base = raw.get(SIMMONS_KEY, 1) or 1
    normalized = {}
    for b in BRANDS:
        kw = b["query"] if b["name"] == "시몬스" else b["query"]
        # 브랜드 query와 trend group keyword 매핑
        val = raw.get(b["query"], raw.get(b["name"], 0))
        normalized[b["name"]] = round((val / base) * 100, 1)

    # 시몬스 직접 맵핑
    normalized["시몬스"] = 100.0
    return normalized


def fetch_monthly_trend():
    """최근 12개월 월별 추이 — 상위 5개 브랜드"""
    pytrends = TrendReq(hl='ko', tz=540)
    keywords = ["시몬스 침대", "에이스침대", "한샘", "이케아", "씰리침대"]
    label_map = {
        "시몬스 침대": "시몬스",
        "에이스침대": "에이스침대",
        "한샘": "한샘",
        "이케아": "이케아",
        "씰리침대": "씰리침대",
    }
    try:
        time.sleep(2)
        pytrends.build_payload(keywords, cat=0, timeframe='today 12-m', geo='KR')
        df = pytrends.interest_over_time()
        if df.empty:
            return {}, []

        df.index = df.index.to_period('M')
        monthly = df.groupby(df.index).mean()
        periods = [str(p) for p in monthly.index]

        result = {}
        for kw, label in label_map.items():
            if kw in monthly.columns:
                result[label] = [round(float(v), 1) for v in monthly[kw]]
        return result, periods
    except Exception as e:
        print(f"  [월별 트렌드 오류] {e}")
        return {}, []
