"""
Google Trends 수집기 — trendspy + 배치 체인 링킹

pytrends(아카이브됨, 429 발생)를 trendspy로 교체.
배치 A/B/C → 브리지 브랜드 체인 링킹 → 시몬스=100 재정규화.
"""
import time
import random
import statistics

from brand_config import BRANDS, TREND_BATCHES, TREND_BRIDGES, SIMMONS_TREND_KW
from analyzer.validator import summarize
from analyzer.chain_link import (
    chain_link, rebase_to_simmons, validate_batches, compute_scale_factors
)
import cache

N_SAMPLES = 5        # 배치당 반복 횟수 (중앙값 안정성)
TIMEFRAME = "today 12-m"
GEO = "KR"

# trendspy 사용 시도, 실패 시 pytrends 폴백
try:
    from trendspy import Trends as _TrendsLib
    _USE_TRENDSPY = True
except ImportError:
    try:
        from pytrends.request import TrendReq as _TrendsLib
        _USE_TRENDSPY = False
    except ImportError:
        _TrendsLib = None
        _USE_TRENDSPY = False


def _make_client():
    if _TrendsLib is None:
        raise RuntimeError("trendspy 또는 pytrends가 설치되지 않았습니다.")
    if _USE_TRENDSPY:
        return _TrendsLib(hl="ko", tz=540)
    else:
        return _TrendsLib(hl="ko", tz=540)


def _fetch_once(client, keywords):
    """단일 배치 1회 수집. DataFrame 또는 None 반환."""
    try:
        if _USE_TRENDSPY:
            df = client.interest_over_time(
                keywords, timeframe=TIMEFRAME, geo=GEO
            )
        else:
            client.build_payload(keywords, cat=0, timeframe=TIMEFRAME, geo=GEO)
            df = client.interest_over_time()

        if df is None or (hasattr(df, 'empty') and df.empty):
            return None

        # isPartial 컬럼 제거 (pytrends 전용)
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        return df

    except Exception as e:
        msg = str(e)
        if "429" in msg or "Too Many Requests" in msg or "RateLimitError" in msg:
            raise RateLimitError(msg)
        print(f"    [Google 오류] {e}")
        return None


class RateLimitError(Exception):
    pass


def _fetch_with_retry(client, keywords, max_attempts=5):
    """429 대응 지수 백오프 재시도."""
    for attempt in range(max_attempts):
        try:
            df = _fetch_once(client, keywords)
            time.sleep(random.uniform(3, 7))
            return df
        except RateLimitError:
            if attempt < max_attempts - 1:
                wait = (4 ** attempt) * 4 + random.uniform(2, 8)
                print(f"    [429] {int(wait)}s 후 재시도 (시도 {attempt + 1}/{max_attempts})...")
                time.sleep(wait)
            else:
                print(f"    [429] 최대 재시도 초과")
                return None
    return None


def _collect_batch(client, batch_keywords):
    """
    배치를 N_SAMPLES회 수집.
    Returns: {keyword: {period_str: [sample_values]}}
    """
    samples = {kw: {} for kw in batch_keywords}

    for s in range(N_SAMPLES):
        print(f"      샘플 {s + 1}/{N_SAMPLES} | {batch_keywords}")
        df = _fetch_with_retry(client, batch_keywords)
        if df is None or (hasattr(df, 'empty') and df.empty):
            continue

        # 월별 집계
        try:
            df.index = df.index.to_period("M")
            monthly = df.groupby(df.index).mean()
        except Exception:
            continue

        for kw in batch_keywords:
            if kw not in monthly.columns:
                continue
            for period, val in monthly[kw].items():
                p = str(period)
                samples[kw].setdefault(p, []).append(round(float(val), 2))

    return samples


def fetch_google_trends(run_id, collected_at):
    """
    메인 수집 함수.
    Returns: {
        "normalized": {brand: value (시몬스=100)},
        "monthly_series": {brand: [{period, value, cv, confidence}]},
        "periods": [period_str],
        "batches_raw": [{keywords, raw_medians}],
        "linked": {brand: unified_value},
        "warnings": [str],
    }
    """
    # 캐시 키는 배치 구성 기반
    cache_key = {"batches": TREND_BATCHES}
    cached = cache.get("google_v2", cache_key)
    if cached:
        print("  [Google] 캐시 사용")
        return cached

    if _TrendsLib is None:
        print("  [Google] 라이브러리 없음 (trendspy / pytrends)")
        return {}

    client = _make_client()
    lib_name = "trendspy" if _USE_TRENDSPY else "pytrends(폴백)"
    print(f"  [Google] {lib_name} / {N_SAMPLES}회 샘플링 / {len(TREND_BATCHES)}개 배치")

    # ── 1단계: 배치별 수집 ──────────────────────────────────────
    batch_period_data = []   # [{kw: {period: [samples]}}]
    batch_raw_medians = []   # [{kw: period_avg_median}] (체인 링킹용)

    for bi, batch in enumerate(TREND_BATCHES):
        label = chr(65 + bi)  # A, B, C
        print(f"    배치 {label}: {batch}")
        samples = _collect_batch(client, batch)

        # 기간별 중앙값
        period_medians = {}  # {kw: {period: median}}
        for kw, p_samples in samples.items():
            if not p_samples:
                continue
            period_medians[kw] = {
                p: statistics.median(vs) for p, vs in p_samples.items() if vs
            }

        # 브랜드별 기간 평균 (체인 링킹용 단일값)
        brand_avgs = {}
        for kw, periods in period_medians.items():
            if periods:
                brand_avgs[kw] = statistics.mean(periods.values())

        batch_period_data.append({"samples": samples, "period_medians": period_medians})
        batch_raw_medians.append(brand_avgs)

    # ── 2단계: 체인 링킹 ────────────────────────────────────────
    warnings = []
    linked = {}
    normalized = {}

    try:
        warn = validate_batches(batch_raw_medians, TREND_BRIDGES, len(BRANDS))
        warnings.extend(warn)

        linked = chain_link(batch_raw_medians, TREND_BRIDGES)
        normalized = rebase_to_simmons(linked, baseline=SIMMONS_TREND_KW)

        # 시몬스 검증
        assert normalized.get(SIMMONS_TREND_KW) == 100.0, "시몬스 재기준화 실패"

        print(f"\n  [Google] 체인 링킹 완료 / 시몬스=100 기준")
        for name, val in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
            print(f"    {name}: {val}")

    except (ValueError, AssertionError) as e:
        warnings.append(f"체인 링킹 실패: {e}")
        print(f"  [Google] 체인 링킹 실패: {e}")

        # 폴백: 배치 B(시몬스 포함)만으로 정규화
        batch_b = batch_raw_medians[1] if len(batch_raw_medians) > 1 else {}
        base = batch_b.get(SIMMONS_TREND_KW, 1) or 1
        for kw, v in batch_b.items():
            normalized[kw] = round(v / base * 100, 1)
        normalized[SIMMONS_TREND_KW] = 100.0

    # kw → brand name 매핑
    kw_to_brand = {b["trend_kw"]: b["name"] for b in BRANDS}
    brand_normalized = {}
    for kw, val in normalized.items():
        brand = kw_to_brand.get(kw, kw)
        brand_normalized[brand] = val

    # ── 3단계: 월별 시계열 ────────────────────────────────────────
    # 스케일 계수: linked[brand] / batch_avg[brand] * 1/simmons_linked
    simmons_linked = linked.get(SIMMONS_TREND_KW, 1) or 1

    all_periods = sorted(set(
        p
        for bd in batch_period_data
        for pm in bd["period_medians"].values()
        for p in pm
    ))

    monthly_series = {}

    # 각 배치에서 브랜드별 월별 데이터 수집
    for bi, bd in enumerate(batch_period_data):
        batch_avg = batch_raw_medians[bi]
        for kw, period_medians in bd["period_medians"].items():
            brand = kw_to_brand.get(kw, kw)
            if brand in monthly_series:
                continue  # 브리지 브랜드 중복 방지

            batch_avg_val = batch_avg.get(kw, 1) or 1
            brand_linked = linked.get(kw, batch_avg_val)
            # unified = raw * (brand_linked / batch_avg_val)
            # rebased = unified / simmons_linked * 100
            rebase_factor = brand_linked / batch_avg_val / simmons_linked * 100

            series = []
            all_kw_samples = bd["samples"].get(kw, {})
            for p in all_periods:
                p_samples = all_kw_samples.get(p, [])
                raw_med = period_medians.get(p, 0)
                rebased_val = round(raw_med * rebase_factor, 1)
                stats = summarize(p_samples) if p_samples else {"cv": 0, "confidence": "unstable"}
                series.append({
                    "period": p,
                    "value": rebased_val,
                    "cv": stats.get("cv", 0),
                    "confidence": stats.get("confidence", "unstable"),
                })
            monthly_series[brand] = series

    # 시몬스가 없으면 100 고정 시계열 추가
    if "시몬스" not in monthly_series and all_periods:
        monthly_series["시몬스"] = [
            {"period": p, "value": 100.0, "cv": 0, "confidence": "stable"}
            for p in all_periods
        ]

    # ── 4단계: 결과 조립 ────────────────────────────────────────
    output = {
        "normalized": brand_normalized,
        "monthly_series": monthly_series,
        "periods": all_periods,
        "linked": {kw_to_brand.get(k, k): v for k, v in linked.items()},
        "batches_raw": [
            {
                "label": chr(65 + i),
                "keywords": TREND_BATCHES[i],
                "bridge": TREND_BRIDGES[i] if i < len(TREND_BRIDGES) else None,
                "raw_medians": batch_raw_medians[i],
            }
            for i in range(len(TREND_BATCHES))
        ],
        "warnings": warnings,
    }

    cache.set("google_v2", cache_key, output, ttl_hours=12)
    return output
