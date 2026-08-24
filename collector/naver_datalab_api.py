"""
네이버 데이터랩 검색어트렌드 API 수집기 — §12

POST https://openapi.naver.com/v1/datalab/search
- 키워드 그룹 최대 5개, 그룹당 키워드 최대 20개
- 반환값: 요청 내 상대값 (최댓값=100)
- 시몬스를 모든 배치 첫 번째에 고정 → per-batch 정규화로 비교 성립

Search API (블로그/뉴스 절대 건수)와 혼용 금지.
"""
import os
import json
import time
import random
import urllib.request
import urllib.parse
import statistics
from datetime import datetime, timedelta

from brand_config import BRANDS, KEYWORD_GROUPS, DATALAB_BATCHES
from analyzer.validator import summarize
import cache

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
DATALAB_ENABLED = os.getenv("NAVER_DATALAB_ENABLED", "false").lower() == "true"
DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"

SIMMONS = "시몬스"
N_SAMPLES = 3  # 배치당 반복 횟수 (중앙값 안정성)

AGE_CODES = {
    "10대": "10",
    "20대": "20",
    "30대": "30",
    "40대": "40",
    "50대": "50",
    "60대+": "60",
}


# ── 저수준 API 호출 ──────────────────────────────────────────────

def _build_groups(batch_names):
    """brand names → DataLab keywordGroups 포맷 (KEYWORD_GROUPS 활용)"""
    groups = []
    for name in batch_names:
        kws = KEYWORD_GROUPS.get(name, [name])
        groups.append({"groupName": name, "keywords": kws[:20]})
    return groups


def _datalab_request(batch_names, gender="", ages=None, timeframe_months=12):
    """
    DataLab API 단일 호출.
    Returns: {groupName: [{period: "YYYY-MM-DD", ratio: float}]}
    Raises: ValueError on API error or missing credentials.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID/SECRET 환경변수 없음")

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=timeframe_months * 30)

    body = {
        "startDate": start_dt.strftime("%Y-%m-%d"),
        "endDate": end_dt.strftime("%Y-%m-%d"),
        "timeUnit": "month",
        "keywordGroups": _build_groups(batch_names),
        "device": "",
        "ages": ages or [],
        "gender": gender,
    }

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(DATALAB_URL, data=data, method="POST")
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    req.add_header("Content-Type", "application/json; charset=utf-8")

    time.sleep(random.uniform(0.3, 0.7))
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            result = json.loads(res.read().decode("utf-8"))
            return {item["title"]: item["data"] for item in result.get("results", [])}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        if e.code == 401:
            raise ValueError(
                "DataLab API 권한 없음 (401) — 네이버 개발자 센터에서 "
                "'데이터랩(검색어트렌드)' API 권한 신청 필요. "
                "https://developers.naver.com/apps/#/register"
            )
        raise ValueError(f"DataLab API HTTP {e.code}: {body_text[:200]}")
    except Exception as e:
        raise ValueError(f"DataLab API 오류: {e}")


def _normalize_to_simmons(batch_result, batch_names):
    """
    배치 결과를 시몬스=100 기준으로 정규화.
    Returns: {brand: {period: normalized_ratio}}
    """
    simmons_data = batch_result.get(SIMMONS, [])
    simmons_by_period = {item["period"]: item["ratio"] for item in simmons_data}

    result = {}
    for name in batch_names:
        if name not in batch_result:
            continue
        norm_series = {}
        for item in batch_result[name]:
            period = item["period"][:7]  # YYYY-MM
            raw = item["ratio"]
            s_raw = simmons_by_period.get(item["period"], 0)
            if s_raw > 0:
                norm_series[period] = round(raw / s_raw * 100, 2)
        result[name] = norm_series

    return result


# ── 트렌드 수집 ────────────────────────────────────────────────

def fetch_datalab_trends(run_id, collected_at):
    """
    데이터랩 검색어트렌드 수집.
    NAVER_DATALAB_ENABLED=true 일 때만 실행.
    """
    if not DATALAB_ENABLED:
        print("  [DataLab 트렌드] 비활성화 (NAVER_DATALAB_ENABLED=false)")
        return {}

    cache_key = {"batches": DATALAB_BATCHES, "n": N_SAMPLES}
    cached = cache.get("naver_datalab_trend", cache_key)
    if cached:
        print("  [DataLab 트렌드] 캐시 사용")
        return cached

    print(f"  [DataLab 트렌드] {N_SAMPLES}회 샘플링 / {len(DATALAB_BATCHES)}개 배치")

    brand_period_samples = {}  # {brand: {period: [samples]}}

    for s in range(N_SAMPLES):
        for bi, batch in enumerate(DATALAB_BATCHES):
            print(f"    샘플 {s+1}/{N_SAMPLES} 배치{chr(65+bi)}: {batch}")
            try:
                raw = _datalab_request(batch)
                normalized = _normalize_to_simmons(raw, batch)
                for brand, periods in normalized.items():
                    brand_period_samples.setdefault(brand, {})
                    for period, val in periods.items():
                        brand_period_samples[brand].setdefault(period, []).append(val)
            except ValueError as e:
                print(f"    [DataLab 오류] {e}")
                return {}

    if not brand_period_samples or SIMMONS not in brand_period_samples:
        print("  [DataLab 트렌드] 데이터 없음")
        return {}

    # 기간별 중앙값 + CV
    all_periods = sorted(set(p for ps in brand_period_samples.values() for p in ps))
    monthly_series = {}
    normalized_avg = {}

    for brand, period_samples in brand_period_samples.items():
        series = []
        brand_vals = []
        for p in all_periods:
            samples = period_samples.get(p, [])
            if samples:
                med = round(statistics.median(samples), 1)
                stats = summarize(samples)
                series.append({"period": p, "value": med,
                               "cv": stats["cv"], "confidence": stats["confidence"]})
                brand_vals.append(med)
        if series:
            monthly_series[brand] = series
            normalized_avg[brand] = round(statistics.mean(brand_vals), 1)

    normalized_avg[SIMMONS] = 100.0

    output = {
        "normalized": normalized_avg,
        "monthly_series": monthly_series,
        "periods": all_periods,
        "source": "datalab_api",
    }
    cache.set("naver_datalab_trend", cache_key, output, ttl_hours=12)
    return output


# ── 인구통계 수집 ─────────────────────────────────────────────

def _collect_demographics_for_batch(batch_names):
    """
    배치에 포함된 브랜드의 성별/연령 분포 수집.
    각 성별/연령 요청에서 시몬스=100 기준 정규화 후 비율 계산.
    Returns: {brand: {gender: {여성: %, 남성: %}, age: {10대: %, ...}}}
    """
    result = {name: {"gender": {}, "age": {}} for name in batch_names if name != SIMMONS}

    # 성별
    try:
        female_raw = _datalab_request(batch_names, gender="f")
        male_raw = _datalab_request(batch_names, gender="m")
        female_norm = _normalize_to_simmons(female_raw, batch_names)
        male_norm = _normalize_to_simmons(male_raw, batch_names)

        for brand in batch_names:
            if brand == SIMMONS:
                continue
            f_vals = list(female_norm.get(brand, {}).values())
            m_vals = list(male_norm.get(brand, {}).values())
            if not f_vals or not m_vals:
                continue
            f_avg = statistics.mean(f_vals)
            m_avg = statistics.mean(m_vals)
            total = f_avg + m_avg or 1
            result[brand]["gender"]["여성"] = round(f_avg / total * 100, 1)
            result[brand]["gender"]["남성"] = round(m_avg / total * 100, 1)
    except ValueError as e:
        print(f"    [DataLab 성별 오류] {e}")

    # 연령대
    age_norm_by_code = {}  # {age_label: {brand: avg}}
    for age_label, age_code in AGE_CODES.items():
        try:
            raw = _datalab_request(batch_names, ages=[age_code])
            norm = _normalize_to_simmons(raw, batch_names)
            age_norm_by_code[age_label] = {
                brand: round(statistics.mean(list(ps.values())), 2)
                for brand, ps in norm.items()
                if ps
            }
        except ValueError as e:
            print(f"    [DataLab 연령 오류] {age_label}: {e}")

    for brand in batch_names:
        if brand == SIMMONS:
            continue
        age_vals = {label: age_norm_by_code.get(label, {}).get(brand, 0)
                    for label in AGE_CODES}
        total = sum(age_vals.values()) or 1
        result[brand]["age"] = {
            label: round(v / total * 100, 1) for label, v in age_vals.items()
        }

    return result


def fetch_datalab_demographics(run_id, collected_at):
    """
    성별·연령대 인구통계 수집 (DataLab API).
    NAVER_DATALAB_ENABLED=true 일 때만 실행.
    """
    if not DATALAB_ENABLED:
        print("  [DataLab 인구통계] 비활성화 (NAVER_DATALAB_ENABLED=false)")
        return {}

    cache_key = {"batches": DATALAB_BATCHES, "type": "demo"}
    cached = cache.get("naver_datalab_demo", cache_key)
    if cached:
        print("  [DataLab 인구통계] 캐시 사용")
        return cached

    print(f"  [DataLab 인구통계] {len(DATALAB_BATCHES)}개 배치")
    result = {}

    for bi, batch in enumerate(DATALAB_BATCHES):
        print(f"    배치{chr(65+bi)}: {batch}")
        batch_result = _collect_demographics_for_batch(batch)
        result.update(batch_result)

    # 시몬스 자체 성별/연령 (단독 배치로 수집)
    try:
        simmons_batch = [SIMMONS, "에이스침대"]  # 에이스침대 더미 앵커
        raw = _datalab_request(simmons_batch, gender="f")
        raw_m = _datalab_request(simmons_batch, gender="m")
        # 시몬스 단독 비율 계산
        s_f = statistics.mean([d["ratio"] for d in raw.get(SIMMONS, [])] or [0])
        s_m = statistics.mean([d["ratio"] for d in raw_m.get(SIMMONS, [])] or [0])
        total = s_f + s_m or 1
        result[SIMMONS] = {
            "gender": {"여성": round(s_f / total * 100, 1), "남성": round(s_m / total * 100, 1)},
            "age": {}
        }
        # 연령대
        age_vals = {}
        for age_label, age_code in AGE_CODES.items():
            raw_a = _datalab_request([SIMMONS], ages=[age_code])
            age_vals[age_label] = statistics.mean(
                [d["ratio"] for d in raw_a.get(SIMMONS, [])] or [0]
            )
        total_age = sum(age_vals.values()) or 1
        result[SIMMONS]["age"] = {l: round(v / total_age * 100, 1) for l, v in age_vals.items()}
    except ValueError as e:
        print(f"    [DataLab 시몬스 오류] {e}")

    # 실제 수집 데이터(0보다 큰 값)가 있을 때만 캐시 저장
    def _has_real(d):
        return (any(v > 0 for v in d.get("gender", {}).values()) or
                any(v > 0 for v in d.get("age", {}).values()))

    has_data = any(_has_real(d) for d in result.values())
    if has_data:
        cache.set("naver_datalab_demo", cache_key, result, ttl_hours=24)
        return result
    return {}
