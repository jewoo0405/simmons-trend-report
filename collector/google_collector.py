import time
import random
from pytrends.request import TrendReq
from brand_config import BRANDS, TREND_GROUPS, SIMMONS_TREND_KW
from analyzer.validator import summarize
import cache

N_SAMPLES = 5
TIMEFRAME = "today 12-m"


def _fetch_once(pytrends, group):
    for attempt in range(4):
        try:
            pytrends.build_payload(group, cat=0, timeframe=TIMEFRAME, geo="KR")
            df = pytrends.interest_over_time()
            return df
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                wait = (2 ** attempt) * 10 + random.uniform(2, 5)
                print(f"    [Google 429] {int(wait)}s 재시도 대기...")
                time.sleep(wait)
            else:
                print(f"    [Google 오류] {e}")
                return None
    return None


def fetch_google_trends(run_id, collected_at):
    cached = cache.get("google", {"groups": TREND_GROUPS})
    if cached:
        print("  [Google] 캐시 사용")
        return cached

    pytrends = TrendReq(hl="ko", tz=540)
    all_samples = {}  # kw -> [period -> [sample values]]

    print(f"  [Google] {N_SAMPLES}회 샘플링 시작...")
    for sample_idx in range(N_SAMPLES):
        print(f"    샘플 {sample_idx + 1}/{N_SAMPLES}")
        for group in TREND_GROUPS:
            time.sleep(random.uniform(3, 6))
            df = _fetch_once(pytrends, group)
            if df is None or df.empty:
                continue
            df.index = df.index.to_period("M")
            monthly = df.groupby(df.index).mean()
            for kw in group:
                if kw not in monthly.columns:
                    continue
                if kw not in all_samples:
                    all_samples[kw] = {}
                for period, val in monthly[kw].items():
                    p = str(period)
                    all_samples[kw].setdefault(p, []).append(round(float(val), 2))

    if not all_samples or SIMMONS_TREND_KW not in all_samples:
        print("  [Google] 데이터 없음")
        return {}

    # 기간별 중앙값 + CV 계산
    result = {}
    simmons_medians = {}
    for kw, period_samples in all_samples.items():
        result[kw] = {}
        for period, samples in period_samples.items():
            stats = summarize(samples)
            result[kw][period] = stats
            if kw == SIMMONS_TREND_KW:
                simmons_medians[period] = stats["median"]

    # 시몬스 기준 정규화
    base_avg = sum(simmons_medians.values()) / len(simmons_medians) if simmons_medians else 1
    if base_avg == 0:
        base_avg = 1

    normalized_avg = {}
    for b in BRANDS:
        kw = b["trend_kw"]
        if kw not in result:
            normalized_avg[b["name"]] = 0
            continue
        kw_avg = sum(v["median"] for v in result[kw].values()) / len(result[kw])
        normalized_avg[b["name"]] = round(kw_avg / base_avg * 100, 1)

    normalized_avg["시몬스"] = 100.0

    # 월별 시계열 (상위 5개 브랜드용)
    top_keywords = ["시몬스", "에이스침대", "한샘", "이케아", "씰리침대"]
    monthly_series = {}
    all_periods = sorted(set(p for kw in result for p in result[kw]))

    for kw in top_keywords:
        kw_key = next((b["trend_kw"] for b in BRANDS if b["name"] == kw), kw)
        if kw_key not in result:
            continue
        series = []
        for p in all_periods:
            v = result[kw_key].get(p, {}).get("median", 0)
            cv = result[kw_key].get(p, {}).get("cv", 0)
            conf = result[kw_key].get(p, {}).get("confidence", "unstable")
            series.append({"period": p, "value": v, "cv": cv, "confidence": conf})
        monthly_series[kw] = series

    output = {
        "normalized": normalized_avg,
        "monthly_series": monthly_series,
        "periods": all_periods,
        "raw_stats": {kw: {p: v for p, v in pdata.items()}
                      for kw, pdata in result.items()},
    }
    cache.set("google", {"groups": TREND_GROUPS}, output, ttl_hours=12)
    return output
