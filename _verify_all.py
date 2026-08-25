import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('data/latest.json', encoding='utf-8') as f:
    d = json.load(f)

issues = []
ok = []

print("=" * 60)
print("  데이터 전체 검증 리포트")
print("=" * 60)

# ── 1. 메타 정보
print("\n[1] 메타 정보")
meta = d.get('meta', {})
print(f"  수집일: {meta.get('collected_at','없음')}")
print(f"  run_id: {meta.get('run_id','없음')}")
print(f"  신뢰도: {meta.get('confidence_score','없음')}점")
print(f"  미완결월: {meta.get('is_partial_month', False)}")

# ── 2. Google Trends
print("\n[2] Google Trends (시몬스=100 기준)")
google = d.get('google', {}).get('linked', {})
if not google:
    issues.append("Google 데이터 없음")
else:
    total = sum(google.values())
    simmons = google.get('시몬스', 0)
    print(f"  브랜드 수: {len(google)}개")
    for b, v in sorted(google.items(), key=lambda x: x[1], reverse=True):
        flag = ""
        if v < 0: flag = " ⚠ 음수!"
        if v > 1000: flag = " ⚠ 과도한 값"
        print(f"  {b}: {v}{flag}")
    if simmons != 100.0:
        issues.append(f"Google 시몬스 기준값 비정상: {simmons} (100이어야 함)")
    else:
        ok.append("Google 시몬스 정규화 정상 (100.0)")
    if len(google) != 12:
        issues.append(f"Google 브랜드 수 비정상: {len(google)}개 (12개여야 함)")
    else:
        ok.append(f"Google 12개 브랜드 모두 수집됨")

# ── 3. Naver Search
print("\n[3] Naver 블로그+뉴스 (시몬스=100 기준)")
naver_search = d.get('naver_search', {})
if not naver_search:
    issues.append("Naver Search 데이터 없음")
else:
    print(f"  브랜드 수: {len(naver_search)}개")
    for b, v in sorted(naver_search.items(), key=lambda x: x[1].get('blog_news_total',0), reverse=True):
        raw = v.get('blog_news_total', 0)
        norm = v.get('normalized', 0)
        flag = ""
        if raw < 100 and raw > 0: flag = " ⚠ 너무 낮은 값 (API 미작동 의심)"
        if raw == 0 and b not in ['이케아']: flag = " ※ 측정불가"
        print(f"  {b}: raw={raw:,} / 지수={norm}{flag}")
    simmons_raw = naver_search.get('시몬스', {}).get('blog_news_total', 0)
    if simmons_raw < 1000:
        issues.append(f"Naver 시몬스 raw값 비정상: {simmons_raw} (API 오류 의심)")
    else:
        ok.append(f"Naver 시몬스 raw값 정상: {simmons_raw:,}")

# ── 4. DataLab 트렌드
print("\n[4] DataLab 검색어트렌드")
dl_trend = d.get('naver_datalab_trend', {})
if not dl_trend:
    print("  없음 (API 권한 없음 — 정상, 섹션 숨김 처리됨)")
    ok.append("DataLab 트렌드 없음 → 섹션 숨김 처리")
else:
    print(f"  브랜드 수: {len(dl_trend)}개")

# ── 5. DataLab 성별·연령
print("\n[5] DataLab 성별·연령 (Playwright)")
dl_demo = d.get('naver_datalab', {})
if not dl_demo:
    issues.append("DataLab 인구통계 데이터 없음")
else:
    print(f"  브랜드 수: {len(dl_demo)}개")
    for b, v in dl_demo.items():
        gender = v.get('gender', {})
        age = v.get('age', {})
        g_sum = sum(gender.values())
        a_sum = sum(age.values())
        flag = ""
        # 성별 raw 지수합이 0이면 수집 실패
        if g_sum == 0: flag += " ⚠ 성별 없음"
        if a_sum == 0: flag += " ⚠ 연령 없음"
        # 정규화 후 합계 확인 (합계=100%여야 함)
        if a_sum > 0:
            a_total = sum(age.values()) or 1
            a_norm = {k: v/a_total*100 for k, v in age.items()}
            a_norm_sum = sum(a_norm.values())
            if abs(a_norm_sum - 100) > 1:
                flag += f" ⚠ 연령 정규화합={a_norm_sum:.1f}%"
        print(f"  {b}: 성별={gender} / 연령합={a_sum:.1f}{flag}")
    if len(dl_demo) < 12:
        issues.append(f"DataLab 인구통계 브랜드 수 부족: {len(dl_demo)}개")
    else:
        ok.append(f"DataLab 인구통계 12개 브랜드 수집됨")

# ── 6. 매출 (DART)
print("\n[6] 매출 데이터")
dart = d.get('dart', {})
if not dart:
    issues.append("DART 매출 데이터 없음")
else:
    for b, v in sorted(dart.items(), key=lambda x: x[1].get('revenue',0), reverse=True):
        rev = v.get('revenue', 0)
        src = v.get('source', '?')
        yr = v.get('year', '?')
        flag = ""
        if src == 'manual': flag = " (수동입력 — DART 감사보고서)"
        if rev <= 0: flag += " ⚠ 0 이하"
        if rev > 100000: flag += " ⚠ 비정상 과도한 값"
        print(f"  {b}: {rev:,}억원 ({yr}, {src}){flag}")
    ok.append(f"DART {len(dart)}개 브랜드 수집됨")

# ── 7. SoS 계산 검증
print("\n[7] SoS (Share of Search) 검증")
if google:
    total_g = sum(v for v in google.values() if v > 0)
    sos = {b: round(v/total_g*100, 1) for b, v in google.items() if v > 0}
    sos_sum = sum(sos.values())
    print(f"  SoS 합계: {sos_sum:.1f}% (100%여야 함)")
    for b, v in sorted(sos.items(), key=lambda x: x[1], reverse=True):
        print(f"  {b}: {v}%")
    if abs(sos_sum - 100) > 0.5:
        issues.append(f"SoS 합계 오류: {sos_sum:.1f}%")
    else:
        ok.append("SoS 합계 정상 (100%)")

# ── 8. Gap 계산 검증
print("\n[8] Gap (콘텐츠 과잉/부족) 검증")
if google and naver_search:
    naver_norm = {b: v.get('blog_news_total', 0) for b, v in naver_search.items()}
    naver_base = naver_norm.get('시몬스', 1) or 1
    naver_idx = {b: round(v/naver_base*100, 1) for b, v in naver_norm.items()}
    g_avg = sum(google.values()) / len(google)
    n_avg = sum(naver_idx.values()) / len(naver_idx)
    for b in sorted(naver_idx.keys()):
        g = google.get(b, 0)
        n = naver_idx.get(b, 0)
        g_reb = g / g_avg * 100 if g_avg else 0
        n_reb = n / n_avg * 100 if n_avg else 0
        gap = round(n_reb - g_reb, 0)
        flag = ""
        if abs(gap) > 500: flag = " ⚠ 극단값 (데이터 왜곡 의심)"
        print(f"  {b}: gap={gap:+.0f}{flag}")

# ── 최종 요약
print("\n" + "=" * 60)
print("  검증 결과 요약")
print("=" * 60)
print(f"\n정상 항목 ({len(ok)}개):")
for o in ok:
    print(f"  ✓ {o}")
print(f"\n이상 항목 ({len(issues)}개):")
if issues:
    for i in issues:
        print(f"  ✗ {i}")
else:
    print("  없음 — 모든 데이터 정상")
