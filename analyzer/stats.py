def share_of_search(brand_medians):
    """브랜드별 검색 점유율 (%) 계산"""
    total = sum(brand_medians.values())
    if total == 0:
        return {k: 0.0 for k in brand_medians}
    return {k: round(v / total * 100, 1) for k, v in brand_medians.items()}


def detect_change_points(series, threshold=20):
    """전월 대비 급등/급락 시점 탐지"""
    changes = []
    for i in range(1, len(series)):
        prev = series[i - 1]
        curr = series[i]
        if prev == 0:
            continue
        pct = (curr - prev) / prev * 100
        if abs(pct) >= threshold:
            changes.append({"index": i, "pct_change": round(pct, 1),
                            "direction": "급등" if pct > 0 else "급락"})
    return changes


def stl_decompose(values):
    """간단한 추세/계절성 분리 (이동평균 기반)"""
    n = len(values)
    if n < 6:
        return {"trend": values, "seasonal": [0] * n, "residual": [0] * n}

    window = min(5, n // 2 * 2 + 1)
    half = window // 2
    trend = []
    for i in range(n):
        start = max(0, i - half)
        end = min(n, i + half + 1)
        trend.append(round(sum(values[start:end]) / (end - start), 2))

    residual = [round(values[i] - trend[i], 2) for i in range(n)]
    seasonal = [0.0] * n

    return {"trend": trend, "seasonal": seasonal, "residual": residual}


def naver_google_gap(naver_norm, google_norm):
    """네이버 vs 구글 순위/지수 차이 분석"""
    all_brands = set(naver_norm) | set(google_norm)
    gaps = []
    for brand in all_brands:
        n_val = naver_norm.get(brand, 0)
        g_val = google_norm.get(brand, 0)
        diff = round(n_val - g_val, 1)
        gaps.append({"brand": brand, "naver": n_val, "google": g_val, "gap": diff})
    return sorted(gaps, key=lambda x: abs(x["gap"]), reverse=True)
