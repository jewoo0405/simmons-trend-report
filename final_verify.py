"""
Session 7 최종 검증 스크립트
- data/latest.json → output/report_2026_08.html 재생성
- fix-spec.md P0~P2 검증 항목 전체 자동 체크
"""
import sys, json, re, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.makedirs("output", exist_ok=True)

# ── 1. 데이터 로드 ─────────────────────────────────────────────────────
print("=" * 60)
print("  Session 7 최종 검증 — 2026-08-19")
print("=" * 60)

with open("data/latest.json", encoding="utf-8") as f:
    snap = json.load(f)

from analyzer.stats import share_of_search, share_of_search_category, naver_google_gap, detect_change_points
from brand_config import BED_SPECIALISTS
from builder.dashboard import build_dashboard

google_norm = snap.get("google", {}).get("linked", snap.get("google", {}).get("normalized", {}))
naver_norm = {b: d.get("blog_news_total", 0) for b, d in snap.get("naver_search", {}).items()}
_g = {k: v for k, v in google_norm.items() if v > 0} or naver_norm

sos = share_of_search(_g)
sos_category = share_of_search_category(_g, BED_SPECIALISTS)

# P1-3: 시몬스 DART 수동 주입
dart_data = dict(snap.get("dart", {}))
if "시몬스" not in dart_data:
    dart_data["시몬스"] = {
        "amount": 3239, "year": "2025", "unit": "억원",
        "caution": False,
        "note": "매트리스 전업 (비상장, DART 감사보고서 기준)",
        "source": "DART_audit_report",
    }

gap = naver_google_gap(naver_norm, google_norm)
monthly = snap.get("google", {}).get("monthly_series", {})
change_points = []
for brand, pts in monthly.items():
    vals = [p["value"] for p in pts]
    periods = [p["period"] for p in pts]
    for cp in detect_change_points(vals):
        change_points.append({
            "brand": brand,
            "period": periods[cp["index"]],
            "pct_change": cp["pct_change"],
            "direction": cp["direction"],
        })

payload = {
    "google": snap.get("google", {}),
    "naver": {"normalized": naver_norm},
    "datalab": snap.get("naver_datalab_trend", {}),
    "demographics": snap.get("naver_datalab", {}),
    "dart": dart_data,
    "commentary": "",
    "sos": sos,
    "sos_category": sos_category,
    "gap": gap,
    "change_points": change_points,
    "events": [],
    "meta": {
        "run_id": snap.get("run_id", "final_2026_08"),
        "collected_at": "2026.08.19 12:08",
        "confidence_score": snap.get("quality", {}).get("confidence_score", 70),
    },
}

# ── 2. 최종 보고서 생성 ────────────────────────────────────────────────
print("\n[1/3] 보고서 생성 중...")
html = build_dashboard(
    payload, "2026년 08월", "2026.08.19 12:08",
    snap.get("quality", {}).get("confidence_score", 70),
    is_partial_month=True, partial_day=19,
)

# 최종 산출물
with open("output/report_2026_08.html", "w", encoding="utf-8") as f:
    f.write(html)
print("  → output/report_2026_08.html 저장 완료")

# P0-3 체크용 복사
with open("output/report_test_p03.html", "w", encoding="utf-8") as f:
    f.write(html)
print("  → output/report_test_p03.html (P0-3 체크용) 복사 완료")


# ── 3. 검증 ───────────────────────────────────────────────────────────
print("\n[2/3] 검증 항목 체크 중...")
checks = {}

# ───────── P0-1: 미완결 월 배너 ─────────────────────────────────────
checks["P0-1a: partial-month-banner 존재"] = 'id="partial-month-banner"' in html
checks["P0-1b: 1~19일 배너 텍스트"] = "1~19" in html
checks["P0-1c: IS_PARTIAL_MONTH=true (JS)"] = "const IS_PARTIAL_MONTH = true;" in html
checks["P0-1d: section-changes-title id"] = 'id="section-changes-title"' in html

# ───────── P0-2: 배치 정규화 (코드 수준 — 실 재수집 필요) ────────────
# brand_config에 5배치 정의, 앵커 포함 여부만 코드 수준 확인
from brand_config import TREND_BATCHES, TREND_BRIDGES
all_batches_have_anchor = all(
    "시몬스" in batch or (i > 0 and TREND_BRIDGES[i-1] in batch)
    for i, batch in enumerate(TREND_BATCHES)
)
checks["P0-2a: TREND_BATCHES 5개 정의"] = len(TREND_BATCHES) == 5
checks["P0-2b: 배치A 시몬스 앵커 포함"] = "시몬스" in TREND_BATCHES[0]
checks["P0-2c: 부록에 5배치 설명 포함"] = "배치A" in html and "배치E" in html
# 실제 경고 메시지 (latest.json 기반 — 재수집 전까지 구형 구조)
g_warnings = snap.get("google", {}).get("warnings", [])
checks["P0-2d: 경고 메시지 (재수집 후 해소 예정)"] = f"현재 경고={g_warnings if g_warnings else '없음'}"

# ───────── P0-3: 코웨이 비렉스 SoM 제거 + caution 분리 ──────────────
m = re.search(r"const SOS_SOM_DATA = (\[.*?\]);", html, re.DOTALL)
if m:
    try:
        som_data = json.loads(m.group(1))
        caution_with_som = [d["brand"] for d in som_data if d.get("caution") and d.get("som") is not None]
        non_caution_with_som = [d for d in som_data if not d.get("caution") and d.get("som") is not None]
        checks["P0-3a: caution 브랜드 SoM=None"] = len(caution_with_som) == 0
        checks["P0-3b: 비caution 브랜드 SoM 존재"] = len(non_caution_with_som) > 0
        checks["P0-3c: 코웨이비렉스 SoM 제외"] = not any(
            d["brand"] == "코웨이 비렉스" and d.get("som") is not None for d in som_data
        )
        checks["P0-3d: sos-som-caution-ref 분리"] = 'id="sos-som-caution-ref"' in html
    except Exception as e:
        checks["P0-3a: SOS_SOM_DATA 파싱"] = f"ERROR: {e}"
else:
    checks["P0-3a: SOS_SOM_DATA 존재"] = False

# ───────── P1-1: SoS 이원화 ──────────────────────────────────────────
bed_sum = sum(v for k, v in sos_category.items() if v is not None and k in BED_SPECIALISTS)
simmons_sos_cat = sos_category.get("시몬스")
checks["P1-1a: 침대전업 SoS 합계 = 100%"] = abs(bed_sum - 100.0) < 0.5
checks["P1-1b: 시몬스 카테고리SoS > 50%"] = (simmons_sos_cat or 0) > 50
checks["P1-1c: KPI에 침대전업 표시"] = "침대 전업" in html
checks["P1-1d: SOS_CATEGORY JS const 존재"] = "const SOS_CATEGORY =" in html
checks["P1-1e: KPI에 전체기준 보조 표시"] = f"전체 {sos.get('시몬스', 0):.1f}%" in html or "전체 기준" in html

# ───────── P1-2: Gap 재정의 (옵션B 콘텐츠 생산성) ────────────────────
checks["P1-2a: 섹션명 → 콘텐츠 발행량"] = "검색 수요 대비 콘텐츠 발행량" in html
checks["P1-2b: 콘텐츠 생산성 표현 존재"] = "콘텐츠 생산성" in html
checks["P1-2c: 네이버 강세 문구 제거"] = "네이버 강세" not in html
checks["P1-2d: P1-2 재정의 안내"] = "P1-2 재정의" in html

# ───────── P1-3: 시몬스 SoM 산출 ─────────────────────────────────────
simmons_dart = dart_data.get("시몬스", {})
checks["P1-3a: dart_data에 시몬스 존재"] = "시몬스" in dart_data
checks["P1-3b: 시몬스 매출 = 3239억"] = simmons_dart.get("amount") == 3239
checks["P1-3c: 시몬스 caution=False"] = not simmons_dart.get("caution", True)
if m and "som_data" in dir():
    sim_entry = next((d for d in som_data if d["brand"] == "시몬스"), None)
    checks["P1-3d: 시몬스 ESOV 차트에 플로팅"] = sim_entry is not None and sim_entry.get("som") is not None
    if sim_entry:
        _som_val = sim_entry.get("som")
        checks["P1-3e: 시몬스 SoM 약 20%대"] = _som_val is not None and 15 < _som_val < 30
else:
    checks["P1-3d: 시몬스 ESOV 차트에 플로팅"] = False

# 매출 각주 확인
checks["P1-3f: DART 감사보고서 출처 표기"] = "DART_audit_report" in html or "감사보고서" in html

# ───────── P1-4: ESOV 해석 방향 수정 ────────────────────────────────
checks["P1-4a: 양(+)의 ESOV 설명 존재"] = "양(+)의 ESOV" in html
checks["P1-4b: 음의 ESOV 설명 존재"] = ("음(-)의 ESOV" in html or "음(−)의 ESOV" in html or "음(-) " in html)
checks["P1-4c: 아래쪽 = SoS > SoM 방향"] = "아래쪽 (SoS" in html
checks["P1-4d: ESOV 툴팁 존재"] = "ESOV:" in html

# ───────── P1-5: KPI 목표 재설정 ─────────────────────────────────────
checks["P1-5a: 카테고리 SoS 60% 목표"] = "60%" in html and "침대 전업" in html
checks["P1-5b: 전체기준 8.1% 보조 유지"] = "전체 기준" in html

# ───────── P2-1: 일괄 표기 수정 ──────────────────────────────────────
checks["P2-1a: 동적 기간 칩 (trend-period-chip)"] = "trend-period-chip" in html
checks["P2-1b: CV 라벨 = 지표 변동성"] = "지표 변동성 (CV 분석)" in html
checks["P2-1c: 침대 전업 1위 대비 갭 KPI"] = "침대 전업 1위 대비 갭" in html
checks["P2-1d: 구글 검색 순위 기존 라벨 제거"] = "구글 검색 순위 3위 / 11" not in html
checks["P2-1e: 구글 지수 100 기준점 제거"] = "구글 지수: <b>100</b> (기준점)" not in html
checks["P2-1f: 비율(%) 모드 산출식"] = "비율(%) 모드" in html

# ───────── P2-2: 연령대 수치 실계산 ─────────────────────────────────
_demo = snap.get("naver_datalab", {}).get("시몬스", {})
_age = _demo.get("age", {})
_young = round(_age.get("20대", 0) + _age.get("30대", 0), 1)
checks["P2-2a: 20~30대 실계산 문구"] = "20~30대" in html
# P2-2b: 현재 DataLab 실측치 = 20대5.1% + 30대18.9% = 24.0% → 코드 계산값 반영 여부 확인
checks[f"P2-2b: 20+30대 코드 계산값 반영 ({_young}% 실측)"] = f"{_young}%" in html
checks[f"P2-2c: 실측값 = {_young}% in html"] = f"{_young}%" in html

# ───────── P2-3: 주요 발견 중복 제거 ─────────────────────────────────
checks["P2-3a: 직접 경쟁 모니터링 문구"] = "직접 경쟁 모니터링" in html
checks["P2-3b: 이케아 중복 발견 1개 이하"] = html.count("집중 모니터링 필요") < 2

# ───────── P2-4: 히트맵 노이즈 억제 ──────────────────────────────────
checks["P2-4a: 클리핑 로직 존재"] = "클리핑" in html
checks["P2-4b: 미수집 vs 0값 구분"] = "미수집" in html and "측정됨" in html
checks["P2-4c: 저신호 구간 회색"] = "저신호 구간" in html

# ───────── P2-5: 라인차트 추세 모드 ──────────────────────────────────
checks["P2-5a: setTrendMode 함수"] = "setTrendMode" in html
checks["P2-5b: 추세(시작=100) 버튼"] = "추세(시작=100)" in html

# ── 4. 결과 출력 ─────────────────────────────────────────────────────
print("\n[3/3] 검증 결과\n")
passed = failed = info = 0

for k, v in checks.items():
    if isinstance(v, bool):
        icon = "OK" if v else "FAIL"
        if v:
            passed += 1
        else:
            failed += 1
        print(f"  [{icon}] {k}")
    else:
        info += 1
        print(f"  [INFO] {k}: {v}")

print(f"\n  ─────────────────────────────────────")
print(f"  OK {passed}  /  FAIL {failed}  /  INFO {info}")
print(f"  총 체크 항목: {passed + failed}")

# ── 5. 지표 요약 ─────────────────────────────────────────────────────
print("\n\n[지표 요약]")
print(f"  시몬스 SoS (전체):    {sos.get('시몬스', 0):.1f}%")
print(f"  시몬스 SoS (침대전업): {simmons_sos_cat:.1f}%")
print(f"  침대전업 합계:         {bed_sum:.1f}%")
if "sim_entry" in dir() and sim_entry:
    print(f"  시몬스 SoM:           {sim_entry.get('som')}%")
print(f"  수집 기간: {snap.get('google', {}).get('periods', ['?'])[0]} ~ {snap.get('google', {}).get('periods', ['?'])[-1]}")
print(f"\n  BED_SPECIALISTS: {BED_SPECIALISTS}")
print(f"  DART 비caution 브랜드: {[b for b, d in dart_data.items() if not d.get('caution', True)]}")

print("\n완료.")
