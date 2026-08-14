"""
체인 링킹 모듈 -배치 간 스케일 통합

Google Trends / Naver DataLab은 요청 단위 상대값(0-100)을 반환합니다.
같은 브랜드라도 어떤 배치에 포함됐는지에 따라 값이 달라지므로,
배치 간 공통 브리지 브랜드를 통해 단일 스케일로 통합해야 비교가 성립합니다.
"""
import statistics


def chain_link(batch_avgs, bridges):
    """
    batch_avgs: list of {brand: avg_value}, 각 배치의 브랜드 평균값
    bridges:    list of bridge brand names (배치 i → i+1 사이 공통 브랜드)
    Returns:    단일 스케일로 통합된 {brand: value}
    Raises:     ValueError if bridge value is missing or too small (<5)
    """
    if len(batch_avgs) != len(bridges) + 1:
        raise ValueError(f"배치 {len(batch_avgs)}개에 브리지 {len(bridges)}개 필요 (현재 {len(bridges)}개)")

    merged = dict(batch_avgs[0])
    cumulative_scale = 1.0

    for i in range(1, len(batch_avgs)):
        bridge = bridges[i - 1]
        prev_v = merged.get(bridge)
        curr_v = batch_avgs[i].get(bridge)

        if prev_v is None or prev_v == 0:
            raise ValueError(f"브리지 '{bridge}' 이전 배치 값 누락")
        if curr_v is None or curr_v == 0:
            raise ValueError(f"브리지 '{bridge}' 현재 배치 값 누락 (0 또는 None)")
        # bridge < 5: 반올림 오차 증폭 경고, 하지만 계속 진행 (경고는 validate_batches가 담당)
        # bridge == 0 일 때만 Raise (이미 위에서 처리)

        scale = prev_v / curr_v
        for brand, v in batch_avgs[i].items():
            if brand not in merged:
                merged[brand] = round(v * scale, 3)

    return merged


def rebase_to_simmons(merged, baseline="시몬스"):
    """시몬스=100 기준으로 재정규화"""
    base = merged.get(baseline)
    if not base:
        raise ValueError(f"앵커 브랜드 '{baseline}' 값 없음 -수집 실패로 처리")
    return {brand: round(v / base * 100, 1) for brand, v in merged.items()}


def validate_batches(batch_avgs, bridges, brand_count):
    """
    배치 품질 검증. 경고 문자열 리스트 반환 (빈 리스트 = 이상 없음).
    실패 조건은 Raise하지 않고 경고로만 기록한다 (급등 같은 정상 이벤트 보존 목적).
    """
    warnings = []

    for i, batch in enumerate(batch_avgs):
        label = f"배치{chr(65 + i)}"
        vals = [v for v in batch.values() if v and v > 0]
        if not vals:
            warnings.append(f"{label}: 수집값 없음")
            continue

        ratio = max(vals) / max(min(vals), 0.01)
        if ratio > 20:
            warnings.append(f"{label}: max/min={ratio:.1f}x > 20 (배치 재구성 권장)")

        if i < len(bridges):
            bv = batch.get(bridges[i], 0)
            if bv < 5:
                warnings.append(f"{label}: 브리지 '{bridges[i]}' 값 {bv:.1f} < 5 (유효숫자 부족)")

    # 전체 브랜드 수 확인
    if len(batch_avgs) > 0:
        total_brands = len(set(b for batch in batch_avgs for b in batch))
        if total_brands < brand_count:
            warnings.append(f"브랜드 {brand_count}개 중 {total_brands}개만 수집됨")

    return warnings


def compute_scale_factors(batch_avgs, bridges):
    """
    각 배치에 속한 브랜드의 체인 링킹 스케일 계수 반환.
    monthly series 계산에 사용: unified = raw * scale_factor
    Returns: {brand: (batch_index, scale_factor)}
    """
    merged = dict(batch_avgs[0])
    scale_factors = {brand: (0, 1.0) for brand in batch_avgs[0]}
    cumulative_scale = 1.0

    for i in range(1, len(batch_avgs)):
        bridge = bridges[i - 1]
        prev_v = merged.get(bridge)
        curr_v = batch_avgs[i].get(bridge)
        if not prev_v or not curr_v:
            break
        scale = prev_v / curr_v
        cumulative_scale *= scale

        for brand, v in batch_avgs[i].items():
            if brand not in merged:
                merged[brand] = round(v * scale, 3)
                scale_factors[brand] = (i, cumulative_scale)

    return scale_factors
