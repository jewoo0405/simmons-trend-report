import json
import os
from datetime import datetime, timedelta
from brand_config import BRANDS, TIER_LABELS, TIER_NEW, BRAND_TO_TIER_NEW, KEYWORD_GROUPS
from analyzer.validator import overall_confidence_score

_SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "snapshots")

# KPI 방향성 정의 — True = 값이 높을수록 좋음, False = 낮을수록 좋음
_KPI_DIRECTION = {
    "sos":       True,   # SoS 높을수록 좋음
    "g_rank":    False,  # 순위 낮을수록(1위) 좋음
    "n_rank":    False,
    "gap_to_top": False, # 1위와 격차 작을수록 좋음
}


def _compute_kpi(data):
    """현재 월 KPI 계산 — 시몬스=100 기준"""
    sos = data.get("sos", {})
    google = data.get("google", {})
    naver = data.get("naver", {})

    sos_val = round(sos.get("시몬스", 0), 1)

    # 구글 순위: linked 정렬
    g_linked = google.get("linked", google.get("normalized", {}))
    sorted_g = sorted(g_linked.items(), key=lambda x: x[1], reverse=True)
    g_rank = next((i + 1 for i, (b, _) in enumerate(sorted_g) if b == "시몬스"), None)
    g_top = sorted_g[0] if sorted_g else ("—", 0)
    gap_to_top = round(g_top[1] - 100, 1) if g_top[0] != "시몬스" else 0.0

    # 네이버 순위: normalized 정렬
    n_norm = naver.get("normalized", {})
    sorted_n = sorted(n_norm.items(), key=lambda x: x[1], reverse=True)
    n_rank = next((i + 1 for i, (b, _) in enumerate(sorted_n) if b == "시몬스"), None)

    return {
        "sos": sos_val,
        "g_rank": g_rank,
        "n_rank": n_rank,
        "g_top_brand": g_top[0],
        "gap_to_top": gap_to_top,
        "total_brands": len(sorted_g),
    }


def _load_prev_kpi(report_month):
    """전월 KPI 스냅샷 로드. 없으면 None 반환."""
    try:
        # "2026년 08월" → datetime
        parts = report_month.replace("년 ", "-").replace("월", "").strip()
        cur = datetime.strptime(parts, "%Y-%m")
        prev = (cur.replace(day=1) - timedelta(days=1))
        key = prev.strftime("%Y_%m")
    except Exception:
        return None
    path = os.path.join(_SNAP_DIR, f"{key}_kpi.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_monthly_kpi(kpi, report_month):
    """이번 달 KPI를 YYYY_MM_kpi.json 으로 저장 (이미 있으면 건너뜀)."""
    try:
        parts = report_month.replace("년 ", "-").replace("월", "").strip()
        cur = datetime.strptime(parts, "%Y-%m")
        key = cur.strftime("%Y_%m")
    except Exception:
        return
    path = os.path.join(_SNAP_DIR, f"{key}_kpi.json")
    if not os.path.exists(path):
        os.makedirs(_SNAP_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(kpi, f, ensure_ascii=False, indent=2)


def _delta_html(cur, prev, key, unit=""):
    """전월비 델타 HTML 문자열. prev=None 이면 '—' 반환."""
    if prev is None or key not in prev:
        return '<span style="color:#999;">— <small>비교기준 없음</small></span>'
    diff = round(cur[key] - prev[key], 1)
    if diff == 0:
        arrow, color = "→", "#888"
    elif _KPI_DIRECTION.get(key, True):
        arrow, color = ("▲", "#2e7d32") if diff > 0 else ("▼", "#c62828")
    else:
        arrow, color = ("▲", "#c62828") if diff > 0 else ("▼", "#2e7d32")
    sign = "+" if diff > 0 else ""
    return f'<span style="color:{color};font-weight:bold;">{arrow} {sign}{diff}{unit}</span>'


def _build_kpi_strip(kpi, prev_kpi, total_brands):
    """KPI 스트립 HTML 생성"""
    d = lambda k, u="": _delta_html(kpi, prev_kpi, k, u)

    cards = [
        ("Share of Search", f"{kpi['sos']}%", d("sos", "%p"),
         "브랜드별 구글 검색 점유율 합산 기준"),
        ("구글 검색 순위", f"{kpi['g_rank']}위 / {total_brands}",
         d("g_rank", "위"), "Google Trends 정규화 지수 기준"),
        ("네이버 노출 순위", f"{kpi['n_rank']}위 / {total_brands}",
         d("n_rank", "위"), "블로그+뉴스 건수 기준"),
        ("1위 브랜드 대비 갭", f"-{kpi['gap_to_top']}pt",
         d("gap_to_top", "pt"), f"vs {kpi['g_top_brand']} (구글 지수 기준)"),
    ]

    items = ""
    for title, val, delta, note in cards:
        items += f"""
      <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{val}</div>
        <div class="kpi-delta">{delta}</div>
        <div class="kpi-note">{note}</div>
      </div>"""

    footnote = "" if prev_kpi else \
        '<div style="font-size:10px;color:#767676;margin-top:8px;text-align:right;">※ 전월 스냅샷 없음 — 비교 기준월 데이터 축적 후 전월비 표시</div>'

    return f'<div class="kpi-strip">{items}</div>{footnote}'


def _build_action_table(data, kpi):
    """권고 액션 테이블 — 실제 데이터 근거 기반 자동 생성"""
    sos_val = kpi["sos"]
    g_rank = kpi["g_rank"]

    # 데이터 기반 액션 자동 생성
    actions = []

    if g_rank and g_rank > 2:
        actions.append((
            f"구글 검색 지수 상위 2위권 진입 전략 수립 (현재 {g_rank}위)",
            '<a href="#section-rank">구글 검색 지수 순위</a>',
            "브랜드팀", "2026 Q4", "높음"
        ))

    demo = data.get("demographics", {})
    simmons_demo = demo.get("시몬스", {})
    age = simmons_demo.get("age", {})
    young = round((age.get("20대", 0) + age.get("30대", 0)), 1)
    if young < 30:
        actions.append((
            f"20~30대 검색 비중 제고 (현재 {young}%, 에이스침대 대비 저조)",
            '<a href="#section-demo">연령대별 검색 관심도</a>',
            "마케팅팀", "2026 Q4", "높음"
        ))

    naver_data = data.get("naver", {})
    naver_norm = naver_data.get("normalized", {})
    ace_naver = naver_norm.get("에이스침대", 0)
    if ace_naver > 100:
        actions.append((
            f"네이버 콘텐츠 발행량 확대 (에이스침대 대비 {round(ace_naver-100,1)}pt 낮음)",
            '<a href="#section-naver-rank">네이버 콘텐츠 노출량</a>',
            "디지털마케팅팀", "2026 Q3", "중간"
        ))

    if sos_val < 10:
        actions.append((
            f"Share of Search 10% 목표 설정 (현재 {sos_val}%)",
            '<a href="#section-sos">Share of Search</a>',
            "브랜드팀", "2027 Q1", "중간"
        ))

    actions.append((
        "네이버 쿠키 만료 전 갱신 (3개월 주기 정기 점검)",
        '<a href="#section-cv">데이터 신뢰도 상세</a>',
        "CS팀", "3개월 주기", "낮음"
    ))

    rows = ""
    priority_color = {"높음": "#c62828", "중간": "#e65100", "낮음": "#2e7d32"}
    for rec, ref, owner, deadline, priority in actions:
        pc = priority_color.get(priority, "#888")
        rows += f"""
        <tr>
          <td>{rec}</td>
          <td>{ref}</td>
          <td>{owner}</td>
          <td>{deadline}</td>
          <td><span style="color:{pc};font-weight:bold;">{priority}</span></td>
        </tr>"""

    return f"""
    <table class="data-table">
      <thead><tr>
        <th>제언</th><th>근거 지표</th><th>담당</th><th>기한</th><th>우선순위</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _color(name):
    for b in BRANDS:
        if b["name"] == name:
            return b["color"]
    return "#888888"


def _brand_colors():
    return {b["name"]: b["color"] for b in BRANDS}


def _compute_sos_som(data):
    """SoS vs SoM 산점도용 계산. caution=False 브랜드만 SoM 계산."""
    sos = data.get("sos", {})
    dart = data.get("dart", {})

    # caution=False 브랜드만 SoM 계산
    valid_dart = {b: d for b, d in dart.items() if not d.get("caution", True)}
    total_sales = sum(d["amount"] for d in valid_dart.values())

    result = []
    for brand, sos_val in sos.items():
        if brand == "시몬스":
            continue  # 비상장 — SoM 없음
        brand_dart = dart.get(brand, {})
        caution = brand_dart.get("caution", True)
        tier = BRAND_TO_TIER_NEW.get(brand, "?")
        in_dart = brand in dart
        som_val = None
        if not caution and total_sales > 0 and in_dart:
            som_val = round(dart[brand]["amount"] / total_sales * 100, 1)
        result.append({
            "brand": brand,
            "sos": round(sos_val, 1),
            "som": som_val,
            "caution": caution,
            "tier": tier,
            "in_dart": in_dart,
        })
    return result


def _caption(source, collected_at, n=""):
    """통일 캡션 HTML 생성. source, collected_at, n 을 받아 표준 포맷 반환."""
    n_part = f" · N={n}" if n else ""
    return (f'<div style="font-size:10px;color:#767676;margin-top:6px;padding-top:6px;'
            f'border-top:1px solid #f0f0f0;">출처: {source} · 수집: {collected_at}'
            f' · 기준: 시몬스=100{n_part}</div>')


def _build_appendix(collected_at):
    """부록 섹션 HTML 생성 (T3-1)"""
    # ① 키워드 그룹 정의 테이블
    kw_rows = ""
    for brand, kws in KEYWORD_GROUPS.items():
        forbidden_note = ""
        if brand == "한샘":
            forbidden_note = ' <span style="color:#e65100;font-size:10px;">※ \'한샘\' 단독 금지</span>'
        elif brand == "이케아":
            forbidden_note = ' <span style="color:#e65100;font-size:10px;">※ \'이케아\' 단독 금지</span>'
        weight = "bold" if brand == "시몬스" else "normal"
        kw_rows += f"""
        <tr>
          <td style="font-weight:{weight}">{brand}{forbidden_note}</td>
          <td>{' / '.join(kws)}</td>
        </tr>"""

    # ② 동음이의어 처리 내역
    homonym_rows = """
        <tr>
          <td>한샘</td>
          <td>단독 사용 금지</td>
          <td>'한샘' 단독은 가구·인테리어·회사명 등 카테고리 오염 발생. 반드시 '한샘 침대', '한샘 매트리스' 등 복합어 사용</td>
        </tr>
        <tr>
          <td>이케아</td>
          <td>단독 사용 금지</td>
          <td>'이케아' 단독은 가구 전반 수요 혼재. 반드시 '이케아 침대', '이케아 매트리스' 등 복합어 사용</td>
        </tr>"""

    # ③ 지표 산출식
    formula_rows = """
        <tr>
          <td>Share of Search (SoS)</td>
          <td style="font-family:monospace;">SoS(B) = 지수(B) / Σ지수(전체) × 100</td>
          <td>브랜드별 구글 검색 점유율. 전체 합계=100%</td>
        </tr>
        <tr>
          <td>Google Trends 체인 링킹</td>
          <td style="font-family:monospace;">배치 간 브리지 브랜드로 정규화, 시몬스=100 고정</td>
          <td>배치A→B: 일룸 브리지, 배치B→C: 에이스침대 브리지</td>
        </tr>
        <tr>
          <td>CV (변동계수)</td>
          <td style="font-family:monospace;">CV = 표준편차 / 평균</td>
          <td>CV≤0.05 안정(녹) · CV≤0.15 주의(주황) · CV&gt;0.15 불안정(빨강)</td>
        </tr>
        <tr>
          <td>카테고리 인덱스</td>
          <td style="font-family:monospace;">인덱스(B,G) = 브랜드값(B,G) / 카테고리평균(G) × 100</td>
          <td>성별·연령 인덱스 모드. 카테고리 평균=100 기준</td>
        </tr>"""

    # ④ 데이터 소스별 한계 카드
    limit_cards = """
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #2e7d32;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Google Trends</div>
          <div style="font-size:11px;color:#555;line-height:1.6;">표본 기반 상대지수, 절대값 아님. 키워드 조합에 따라 결과 달라짐. 배치 체인 링킹으로 정규화.</div>
        </div>
        <div style="background:#f9f9f9;border-radius:6px;padding:12px;border-left:3px solid #1565c0;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Naver 콘텐츠 노출량</div>
          <div style="font-size:11px;color:#555;line-height:1.6;">검색 수요가 아닌 콘텐츠 발행량. 브랜드 마케팅 활동량 반영. 블로그+뉴스 건수 합산.</div>
        </div>
        <div style="background:#fff3e0;border-radius:6px;padding:12px;border-left:3px solid #e65100;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Google Trends 배치 체인 링킹</div>
          <div style="font-size:11px;color:#555;line-height:1.6;">배치C max/min비율이 20배 초과 시 WARNING 수준 경고 발생 가능. 수집 로그에서 확인 필요.</div>
        </div>"""

    return f"""
  <!-- 부록 섹션 (T3-1) -->
  <div class="chart-row" id="section-appendix">
    <div class="card">
      <div class="card-title">부록 — 방법론 및 데이터 소스</div>
      <div class="card-sub">수집 기준 · 산출식 · 데이터 한계 공개 / 수집: {collected_at}</div>

      <!-- ① 키워드 그룹 정의 -->
      <div class="section-title" style="margin-top:16px;">① 키워드 그룹 정의 (Naver DataLab 수집 기준)</div>
      <div style="margin-bottom:12px;font-size:11px;color:#666;">브랜드별 표기 변형을 통합한 키워드 그룹. 동일 그룹 내 키워드는 OR 조건으로 합산.</div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:130px;">브랜드</th>
          <th>수집 키워드</th>
        </tr></thead>
        <tbody>{kw_rows}
        </tbody>
      </table>

      <!-- ② 동음이의어 처리 내역 -->
      <div class="section-title" style="margin-top:16px;">② 동음이의어 처리 내역</div>
      <div style="margin-bottom:12px;font-size:11px;color:#666;">카테고리 오염 방지를 위해 단독 사용이 금지된 키워드 목록.</div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:80px;">브랜드</th>
          <th style="width:120px;">처리 방식</th>
          <th>사유</th>
        </tr></thead>
        <tbody>{homonym_rows}
        </tbody>
      </table>

      <!-- ③ 지표 산출식 -->
      <div class="section-title" style="margin-top:16px;">③ 지표 산출식</div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:160px;">지표</th>
          <th style="width:260px;">산출식</th>
          <th>설명</th>
        </tr></thead>
        <tbody>{formula_rows}
        </tbody>
      </table>

      <!-- ④ 데이터 소스별 한계 -->
      <div class="section-title" style="margin-top:16px;">④ 데이터 소스별 한계</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;">
        {limit_cards}
      </div>

      <!-- ⑤ 지표 정의집 -->
      <div class="section-title" style="margin-top:24px;">⑤ 지표 정의집</div>
      <table class="appendix-table">
        <thead>
          <tr><th>지표명</th><th>산출식</th><th>출처</th><th>갱신 주기</th><th>한계</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Share of Search (SoS)</td>
            <td>자사 검색량 ÷ 전체 브랜드 합 × 100</td>
            <td>Google Trends + Naver DataLab</td>
            <td>월 1회</td>
            <td>Tier C 종합가구 포함 시 카테고리 수요 혼재</td>
          </tr>
          <tr>
            <td>구글 검색 지수</td>
            <td>시몬스=100 기준 상대지수</td>
            <td>Google Trends (KR)</td>
            <td>월 1회</td>
            <td>표본 기반 상대값, 절대 검색량 아님</td>
          </tr>
          <tr>
            <td>네이버 콘텐츠 노출량</td>
            <td>블로그 건수 + 뉴스 건수</td>
            <td>Naver 검색 API</td>
            <td>월 1회</td>
            <td>마케팅 물량 반영, 검색 수요 아님</td>
          </tr>
          <tr>
            <td>성별·연령 인덱스</td>
            <td>(브랜드 비율 ÷ 카테고리 평균) × 100</td>
            <td>Naver DataLab</td>
            <td>월 1회</td>
            <td>DataLab 관심도 기준, 실구매 반영 안 됨</td>
          </tr>
          <tr>
            <td>CV (변동계수)</td>
            <td>표준편차 ÷ 평균 (Google Trends 월별값 기준)</td>
            <td>Google Trends 월별 시계열</td>
            <td>매월 갱신</td>
            <td>최소 3개월 필요, 초기 운영 중 표본 부족</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>"""


def build_dashboard(data, report_month, collected_at, confidence_score):
    colors = _brand_colors()
    data_json = json.dumps(data, ensure_ascii=False)
    colors_json = json.dumps(colors, ensure_ascii=False)
    brands_cfg_json = json.dumps(BRANDS, ensure_ascii=False)
    tier_labels_json = json.dumps({str(k): v for k, v in TIER_LABELS.items()}, ensure_ascii=False)
    tier_new_json = json.dumps(TIER_NEW, ensure_ascii=False)
    brand_to_tier_json = json.dumps(BRAND_TO_TIER_NEW, ensure_ascii=False)
    sos_som_json = json.dumps(_compute_sos_som(data), ensure_ascii=False)
    sample_count = data.get('quality', {}).get('sample_count', 3)
    sample_count_label = f"{sample_count}회 수집"

    conf_color = "#2e7d32" if confidence_score >= 70 else "#e65100" if confidence_score >= 40 else "#c62828"
    conf_label = "안정" if confidence_score >= 70 else "주의" if confidence_score >= 40 else "불안정"

    # KPI 계산 및 전월 비교
    kpi = _compute_kpi(data)
    prev_kpi = _load_prev_kpi(report_month)
    _save_monthly_kpi(kpi, report_month)
    total_brands = kpi.get("total_brands", 11)
    kpi_strip_html = _build_kpi_strip(kpi, prev_kpi, total_brands)
    action_table_html = _build_action_table(data, kpi)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>시몬스 브랜드 트렌드 대시보드 — {report_month}</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Malgun Gothic',Arial,sans-serif;background:#f0f2f5;color:#222;min-width:1280px;}}

/* 상단 헤더 */
#top-header{{
  position:sticky;top:0;z-index:100;
  background:#0b0b0b;color:#fff;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;height:52px;
  border-bottom:2px solid #c8a96e;
}}
#top-header .title{{font-size:16px;font-weight:bold;}}
#top-header .meta{{display:flex;gap:20px;align-items:center;font-size:12px;color:#aaa;}}
.conf-badge{{
  padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;
  background:{conf_color};color:#fff;
}}

/* 레이아웃 — 사이드바 + main 2열 */
#layout{{display:flex;height:calc(100vh - 52px);}}

/* 좌측 사이드바 */
#sidebar{{
  width:220px;min-width:220px;background:#fff;
  border-right:1px solid #e0e0e0;overflow-y:auto;padding:16px 12px;
}}
#sidebar h3{{font-size:12px;color:#888;text-transform:uppercase;
             letter-spacing:1px;margin:16px 0 8px;padding-bottom:4px;
             border-bottom:1px solid #eee;}}
.tier-header{{
  font-size:10px;color:#999;font-weight:600;letter-spacing:0.5px;
  padding:8px 4px 4px;text-transform:uppercase;
}}
.brand-item{{
  display:flex;align-items:center;gap:8px;padding:5px 4px;
  border-radius:4px;cursor:pointer;font-size:13px;transition:background 0.15s;
}}
.brand-item:hover{{background:#f5f5f5;}}
.brand-item.active{{background:#e8eaf6;font-weight:bold;}}
.brand-item--baseline{{
  background:#fafafa;border:1px solid #e0e0e0;
  border-radius:6px;margin-bottom:6px;
}}
.brand-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
.baseline-badge{{
  margin-left:auto;font-size:9px;font-weight:700;
  background:#0b0b0b;color:#c8a96e;
  padding:2px 5px;border-radius:3px;letter-spacing:0.5px;
}}
.filter-btn{{
  display:block;width:100%;padding:6px 10px;margin-bottom:6px;
  border:1px solid #ddd;border-radius:4px;background:#fff;
  font-size:12px;cursor:pointer;text-align:left;transition:all 0.15s;
}}
.filter-btn:hover,.filter-btn.active{{background:#0b0b0b;color:#fff;border-color:#0b0b0b;}}

/* 중앙 차트 영역 */
#main{{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:16px;}}

/* KPI 스트립 */
.kpi-strip{{
  display:grid;grid-template-columns:repeat(4,1fr);gap:12px;
  margin-bottom:0;
}}
.kpi-card{{
  background:#fff;border-radius:8px;border:1px solid #e0e0e0;
  padding:14px 16px;border-top:3px solid #c8a96e;
}}
.kpi-label{{font-size:11px;color:#666;font-weight:600;text-transform:uppercase;
            letter-spacing:0.5px;margin-bottom:6px;}}
.kpi-value{{font-size:22px;font-weight:bold;color:#0b0b0b;margin-bottom:4px;}}
.kpi-delta{{font-size:13px;margin-bottom:4px;}}
.kpi-note{{font-size:10px;color:#767676;}}

/* 섹션 구분선 */
.section-divider{{
  display:flex;align-items:center;gap:12px;margin:8px 0;
  color:#888;font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;
}}
.section-divider::before,.section-divider::after{{
  content:'';flex:1;height:1px;background:#e0e0e0;
}}

/* 요약 카드 그리드 */
.summary-grid{{display:grid;grid-template-columns:1fr 2fr;gap:16px;}}
.summary-col{{display:flex;flex-direction:column;gap:12px;}}

/* 인사이트 아이템 */
.insight-item{{
  padding:10px;border-radius:6px;background:#f9f9f9;
  margin-bottom:8px;font-size:12px;line-height:1.6;
}}
.insight-item.warn{{background:#fff3e0;border-left:3px solid #e65100;}}
.insight-item.good{{background:#e8f5e9;border-left:3px solid #2e7d32;}}

/* 섹션 타이틀 */
.section-title{{
  font-size:13px;font-weight:bold;color:#0b0b0b;
  border-left:3px solid #c8a96e;padding-left:8px;margin-bottom:12px;
}}

/* 차트 카드 */
.chart-row{{display:grid;gap:16px;}}
.chart-row.col2{{grid-template-columns:1fr 1fr;}}
.chart-row.col3{{grid-template-columns:1fr 1fr 1fr;}}
.card{{background:#fff;border-radius:8px;border:1px solid #e0e0e0;padding:16px;}}
.card-title{{font-size:13px;font-weight:bold;color:#0b0b0b;margin-bottom:4px;}}
.card-sub{{font-size:11px;color:#888;margin-bottom:12px;}}
.source-badge{{
  display:inline-block;font-size:10px;padding:2px 6px;border-radius:4px;
  margin-left:6px;font-weight:normal;
}}
.badge-google{{background:#e8f5e9;color:#2e7d32;}}
.badge-naver{{background:#e3f2fd;color:#1565c0;}}
.badge-no-demo{{background:#fff3e0;color:#e65100;}}

/* CV 신뢰도 색상 */
.cv-stable{{color:#2e7d32;font-weight:bold;}}
.cv-warning{{color:#e65100;font-weight:bold;}}
.cv-unstable{{color:#c62828;font-weight:bold;}}
.cv-na{{color:#999;font-style:italic;}}

/* 데이터 테이블 */
.data-table{{width:100%;border-collapse:collapse;font-size:12px;}}
.data-table th{{background:#0b0b0b;color:#fff;padding:7px 10px;text-align:left;}}
.data-table td{{padding:7px 10px;border-bottom:1px solid #f0f0f0;}}
.data-table tr:hover td{{background:#f9f9f9;}}
.simmons-sticky td{{background:#fafafa;font-weight:bold;position:sticky;top:0;z-index:1;}}

/* 인구통계 없음 */
.no-data{{text-align:center;padding:30px;color:#aaa;font-size:13px;}}

/* 인구통계 인덱스 토글 버튼 */
.demo-toggle {{
  padding:4px 10px;border:1px solid #ddd;border-radius:4px;
  background:#fff;font-size:11px;cursor:pointer;transition:all 0.15s;
  font-family:'Malgun Gothic',Arial,sans-serif;
}}
.demo-toggle:hover,.demo-toggle.active {{
  background:#0b0b0b;color:#fff;border-color:#0b0b0b;
}}

/* ── 산출 근거 캡션 ─────────────────────────── */
.chart-caption {{
  font-size: 11px;
  color: #767676;
  margin-top: 12px;
  padding: 6px 8px;
  border-top: 1px solid #eee;
  line-height: 1.7;
  word-break: keep-all;
  white-space: normal;
  position: static;
}}
.chart-caption .cap-formula {{ font-style: italic; }}
.chart-caption .cap-source {{ }}
.chart-caption .cap-drill {{
  color: #3498db;
  cursor: pointer;
  text-decoration: underline;
  font-size: 10px;
  margin-left: 6px;
}}
.drill-detail {{
  display: none;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px 10px;
  margin-top: 4px;
  font-size: 11px;
  line-height: 1.8;
  font-family: monospace;
}}

/* 지표 정의집 테이블 */
.appendix-table {{ width:100%; border-collapse:collapse; font-size:12px; margin-top:12px; }}
.appendix-table th {{ background:#2c3e50; color:#fff; padding:8px; text-align:left; }}
.appendix-table td {{ padding:7px 8px; border-bottom:1px solid #eee; vertical-align:top; }}
.appendix-table tr:nth-child(even) td {{ background:#f9f9f9; }}

/* ── 인쇄 전용 ─────────────────────────────── */
.print-only {{ display: none; }}          /* 화면: 숨김 */
.no-print {{ }}                           /* 화면: 정상 */

@media print {{
  /* 표지 표시 */
  .print-only {{ display: block !important; }}
  #cover-page {{ page-break-after: always; }}

  /* 인터랙티브 요소 숨김 */
  .no-print,
  #filter-banner,
  .tier-filter,
  .toggle-btn,
  button,
  .export-btn {{ display: none !important; }}

  /* 페이지 분할 제어 */
  .chart-block,
  .kpi-strip,
  table,
  .section-card {{ page-break-inside: avoid; }}

  h2, h3 {{ page-break-after: avoid; }}

  /* 여백 */
  @page {{ margin: 20mm 15mm; }}

  /* 링크 URL 숨김 */
  a[href]::after {{ content: none; }}

  /* 흑백 출력 보조: 색상 정보 보완 */
  .delta-up::before {{ content: "▲ "; }}
  .delta-down::before {{ content: "▼ "; }}

  /* 사이드바 숨김, 메인 전체폭 */
  .sidebar {{ display: none !important; }}
  #sidebar {{ display: none !important; }}
  #top-header {{ display: none !important; }}
  #filter-changed-banner {{ display: none !important; }}
  #layout {{ height: auto; }}
  #main {{ overflow: visible; padding: 0; width: 100% !important; margin-left: 0 !important; }}

  /* 폰트 크기 최소 10pt */
  body {{ font-size: 10pt; }}

  .card {{ break-inside: avoid; }}
  h2 {{ break-after: avoid; }}
}}

/* 표지 스타일 (화면·인쇄 공통) */
.cover-inner {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  gap: 20px;
}}
.cover-confidential {{
  color: #c0392b;
  font-weight: 700;
  font-size: 14px;
  border: 2px solid #c0392b;
  padding: 4px 16px;
  border-radius: 4px;
}}
.cover-title {{
  font-size: 32px;
  font-weight: 800;
  color: #1a1a2e;
  margin: 0;
}}
.cover-month {{
  font-size: 22px;
  color: #2c3e50;
  font-weight: 600;
}}
.cover-meta {{
  font-size: 13px;
  color: #555;
  line-height: 1.8;
  margin-top: 20px;
}}
</style>
</head>
<body>

<!-- PHASE 4 표지 (T4-1) -->
<div id="cover-page" class="print-only">
  <div class="cover-inner">
    <p class="cover-confidential">대외비 (CONFIDENTIAL)</p>
    <h1 class="cover-title">시몬스 브랜드 트렌드 월간 리포트</h1>
    <p class="cover-month">{report_month}</p>
    <div class="cover-meta">
      <p>작성부서: 고객서비스(CS) 전략팀</p>
      <p>수집일시: {collected_at}</p>
      <p>작성: 자동 생성 시스템 · 검수: ___________</p>
    </div>
  </div>
</div>

<!-- 기본값 변경 배너 (T3-3) -->
<div id="filter-changed-banner" style="display:none; background:#fff3e0; border-bottom:2px solid #e65100; padding:6px 24px; font-size:12px; color:#e65100; position:sticky; top:52px; z-index:99;">
  ※ 기본 보고 기준(최근 3개월 · 전체 브랜드)에서 변경됨 — 인쇄 시 표지에 자동 기록됩니다
</div>

<!-- 상단 헤더 -->
<div id="top-header">
  <div class="title">시몬스 브랜드 트렌드 대시보드 · {report_month}</div>
  <div class="meta">
    <span style="font-size:11px;color:#c8a96e;font-weight:600;">보고 기준: 최근 3개월 · 전체 11개 브랜드</span>
    <span>수집: {collected_at}</span>
    <span>대상: 11개 브랜드</span>
    <span class="conf-badge">{conf_label} {confidence_score}점</span>
  </div>
</div>

<div id="layout">

<!-- 좌측 사이드바 -->
<div id="sidebar">
  <h3>기간</h3>
  <button class="filter-btn active" data-range="today 3-m" onclick="setRange(this,'today 3-m')">최근 3개월</button>
  <button class="filter-btn" data-range="today 6-m" onclick="setRange(this,'today 6-m')">최근 6개월</button>
  <button class="filter-btn" data-range="today 12-m" onclick="setRange(this,'today 12-m')">최근 12개월</button>

  <h3>티어 필터</h3>
  <button class="filter-btn tier-filter active" data-tier="ALL" onclick="setTierFilter(this,'ALL')">전체</button>
  <button class="filter-btn tier-filter" data-tier="A" onclick="setTierFilter(this,'A')">Tier A — 프리미엄</button>
  <button class="filter-btn tier-filter" data-tier="B" onclick="setTierFilter(this,'B')">Tier B — 매스 침대</button>
  <button class="filter-btn tier-filter" data-tier="C" onclick="setTierFilter(this,'C')">Tier C — 종합가구</button>
  <button class="filter-btn tier-filter" data-tier="D" onclick="setTierFilter(this,'D')">Tier D — 렌탈</button>

  <h3>브랜드</h3>
  <div id="brand-list"></div>

  <h3>내보내기</h3>
  <button class="filter-btn" onclick="exportCSV()">CSV 다운로드</button>
  <button class="filter-btn" onclick="exportPrint()">인쇄 / PDF</button>
</div>

<!-- 메인 콘텐츠 (결론 우선 → 근거 데이터) -->
<div id="main">

  <!-- ① KPI 요약 스트립 (T1-2) -->
  <div class="chart-row" id="section-kpi">
    {kpi_strip_html}
  </div>

  <!-- ② 시몬스 포지셔닝 + 주요 발견 (T1-1, T1-4) -->
  <div class="chart-row" id="section-summary">
    <div class="chart-row col2">
      <div class="card">
        <div class="section-title">시몬스 포지셔닝</div>
        <div id="insight-simmons"></div>
      </div>
      <div class="card">
        <div class="section-title">주요 발견</div>
        <div id="insight-findings"></div>
      </div>
    </div>
  </div>

  <!-- ③ 이번 달 변화점 (T1-1) -->
  <div class="chart-row">
    <div class="card">
      <div class="section-title">이번 달 변화점</div>
      <div id="insight-changes"
           style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">
      </div>
    </div>
  </div>

  <!-- ④ 권고 액션 테이블 (T1-5) -->
  <div class="chart-row" id="section-action">
    <div class="card" style="border-top:3px solid #0b0b0b;">
      <div class="card-title">권고 액션
        <span style="font-size:11px;font-weight:normal;color:#888;margin-left:6px;">
          근거 지표 클릭 → 해당 섹션으로 이동
        </span>
      </div>
      {action_table_html}
    </div>
  </div>

  <!-- 근거 데이터 구분선 -->
  <div class="section-divider">근거 데이터</div>

  <!-- ⑤ Share of Search (T1-3 순서 앞으로) -->
  <div class="chart-row col2" id="section-sos">
    <div class="card">
      <div class="card-title">Share of Search
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub">브랜드별 구글 검색 점유율 (%) · SoS = 브랜드 지수 ÷ 전체 합계 × 100</div>
      <div id="chart-sos" style="height:320px;"></div>
      {_caption("Google Trends 파생", collected_at)}
    </div>
    <div class="card" id="section-gap">
      <div class="card-title">구글 vs 네이버 갭 분석</div>
      <div class="card-sub">네이버 지수 − 구글 지수 (양수=네이버 강세 / 음수=구글 강세)</div>
      <div id="chart-gap" style="height:320px;"></div>
      {_caption("Google+Naver 파생", collected_at)}
    </div>
  </div>

  <!-- ⑥ 구글 순위 + 네이버 콘텐츠 노출량 (T1-4 라벨 변경) -->
  <div class="chart-row col2" id="section-rank">
    <div class="card">
      <div class="card-title">구글 검색 지수 순위
        <span class="source-badge badge-google">Google Trends</span>
        <span class="source-badge" style="background:#fff3e0;color:#e65100;" title="Tier C(종합가구)·D(렌탈) 브랜드는 가구·렌탈 수요 혼재로 직접 비교 주의">⚠ Tier C·D 비교 주의</span>
      </div>
      <div class="card-sub" id="sub-google-rank">시몬스=100 기준 · 최근 3개월 한국</div>
      <div id="chart-google-rank" style="min-height:200px;"></div>
      {_caption("Google Trends", collected_at, sample_count_label)}
    </div>
    <div class="card" id="section-naver-rank">
      <div class="card-title">네이버 콘텐츠 노출량
        <span class="source-badge badge-naver">Naver Search</span>
        <span class="source-badge" style="background:#fff3e0;color:#e65100;" title="Tier C(종합가구)·D(렌탈) 브랜드는 가구·렌탈 수요 혼재로 직접 비교 주의">⚠ Tier C·D 비교 주의</span>
      </div>
      <div class="card-sub" id="sub-naver-rank">시몬스=100 기준 · 블로그+뉴스 건수</div>
      <div id="chart-naver-rank" style="min-height:200px;"></div>
      <div style="font-size:10px;color:#999;margin-top:8px;padding-top:8px;border-top:1px solid #f0f0f0;">
        ※ 검색 수요가 아닌 콘텐츠 발행량 지표. 브랜드 자체 마케팅 활동량이 반영됨.
      </div>
      {_caption("Naver Search API", collected_at, "블로그+뉴스 3회 수집 중앙값")}
    </div>
  </div>

  <!-- ⑦ 월별 추이 -->
  <div class="chart-row" id="section-trend">
    <div class="card">
      <div class="card-title">월별 검색 트렌드 추이
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub">주요 브랜드 · 음영은 신뢰구간(CV) · 출처: Google Trends · 기준: 시몬스=100</div>
      <div id="chart-monthly" style="height:420px;"></div>
      {_caption("Google Trends", collected_at, sample_count_label)}
    </div>
  </div>

  <!-- DataLab 트렌드 (§12, API 수집 시 표시) -->
  <div class="chart-row" id="datalab-row" style="display:none;">
    <div class="card">
      <div class="card-title">네이버 데이터랩 검색어트렌드
        <span class="source-badge badge-naver">Naver DataLab API</span>
      </div>
      <div class="card-sub">시몬스=100 기준 · 월별 추이 (키워드 그룹 통합)</div>
      <div id="chart-datalab" style="height:360px;"></div>
      {_caption("Naver DataLab (Playwright)", collected_at, "단회 수집")}
    </div>
  </div>

  <!-- ⑧ 성별 / 연령대 (T2-6: 인덱스화 토글) -->
  <div class="chart-row col2" id="section-demo">
    <div class="card">
      <div class="card-title">성별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <button class="demo-toggle active" id="gender-toggle-norm" onclick="setGenderMode('norm')">브랜드 내 비율</button>
        <button class="demo-toggle" id="gender-toggle-idx" onclick="setGenderMode('idx')">카테고리 인덱스</button>
      </div>
      <div class="card-sub" id="gender-sub">브랜드별 성별 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-gender" style="height:320px;"></div>
      {_caption("Naver DataLab (Playwright)", collected_at, "단회 수집")}
    </div>
    <div class="card">
      <div class="card-title">연령대별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <button class="demo-toggle active" id="age-toggle-norm" onclick="setAgeMode('norm')">브랜드 내 비율</button>
        <button class="demo-toggle" id="age-toggle-idx" onclick="setAgeMode('idx')">카테고리 인덱스</button>
      </div>
      <div class="card-sub" id="age-sub">브랜드별 연령대 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-age" style="height:320px;"></div>
      {_caption("Naver DataLab (Playwright)", collected_at, "단회 수집")}
    </div>
  </div>

  <!-- T2-3: SoS vs SoM 산점도 -->
  <div class="chart-row" id="section-sos-som" style="display:none;">
    <div class="card">
      <div class="card-title">Share of Search vs Share of Market (ESOV 분석)</div>
      <div class="card-sub">시몬스 비상장으로 제외 · 한샘·현대리바트·코웨이는 침대 외 사업 포함 (참고용)</div>
      <div id="chart-sos-som" style="height:400px;"></div>
      <div style="font-size:10px;color:#999;margin-top:8px;padding-top:8px;border-top:1px solid #f0f0f0;">
        ※ SoM = DART 공시 매출 기준 (caution=false 브랜드만). 대각선 위 = 검색 과소 → 검색 투자 여력. 대각선 아래 = 검색 과잉.
      </div>
      {_caption("Google Trends + 네이버 증권", collected_at)}
    </div>
  </div>

  <!-- ⑩ 부록: 데이터 신뢰도 상세 (CV 분석) -->
  <div class="chart-row" id="section-cv">
    <div class="card">
      <div class="card-title">부록 — 데이터 신뢰도 상세 (CV 분석)</div>
      <div class="card-sub">CV≤0.05 안정(녹) · CV≤0.15 주의(주황) · CV&gt;0.15 불안정(빨강)
        · 출처: Google Trends 월별 지수 · 기준: monthly_series 기반 변동계수
      </div>
      <div id="cv-table"></div>
      {_caption("Google Trends monthly_series", collected_at)}
    </div>
  </div>

  {_build_appendix(collected_at)}

</div><!-- /main -->

</div><!-- /layout -->

<script>
/* ── 공통 축 유틸리티 ─────────────────────────────── */

// 사람이 읽기 좋은 눈금 간격 계산
// 허용 배수: 1, 2, 5, 10, 20, 25, 50, 100 의 배수
function niceInterval(range, targetCount) {{
  const rough = range / targetCount;
  const mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const steps = [1, 2, 5, 10, 20, 25, 50, 100];
  let best = steps[steps.length - 1] * mag;
  for (const s of steps) {{
    const candidate = s * mag;
    if (candidate >= rough) {{ best = candidate; break; }}
  }}
  return best;
}}

// 축 최댓값: 데이터 최댓값의 1.1배를 niceInterval 배수로 올림
function niceMax(dataMax, interval) {{
  return Math.ceil(dataMax * 1.1 / interval) * interval;
}}

// 전체 축 옵션 반환 (value 축용)
// unit: '' | '%' | '억'
function axisOption(dataMax, unit, targetCount) {{
  targetCount = targetCount || 5;
  if (!dataMax || dataMax <= 0) dataMax = 100;
  const interval = niceInterval(dataMax * 1.1, targetCount);
  const max = niceMax(dataMax, interval);
  const formatter = v => {{
    if (unit === '%') return v.toFixed(1) + '%';
    if (unit === '억') return (v >= 1000 ? (v/1000).toFixed(1)+'천억' : v+'억');
    // 지수: 소수점 1자리, 천단위 쉼표
    return v >= 1000 ? v.toLocaleString('ko-KR', {{maximumFractionDigits:0}})
                     : v % 1 === 0 ? v.toString() : v.toFixed(1);
  }};
  return {{ type:'value', min:0, max, interval, axisLabel:{{ fontSize:12, formatter }} }};
}}

// 가장 긴 Y축 레이블 길이 기준으로 left 마진 계산
function leftMargin(labels) {{
  const maxLen = Math.max(...labels.map(l => String(l).length));
  return Math.max(60, maxLen * 8);
}}

// 날짜 축 포맷: "2026-03" → "26.03"
function dateAxisOption(periods) {{
  return {{
    type: 'category',
    data: periods,
    axisLabel: {{
      fontSize: 12,
      rotate: 0,
      interval: 'auto',
      formatter: v => {{
        const p = String(v);
        if (p.length >= 7) return p.substring(2,4) + '.' + p.substring(5,7);
        return p;
      }}
    }}
  }};
}}
/* ── 공통 축 유틸리티 끝 ────────────────────────────── */

/* ── 산출 근거 캡션 유틸리티 ────────────────────────── */
function buildCaption(opts) {{
  // opts: {{ formula, source, collected, n, note, drillId, drillContent }}
  const parts = [];
  if (opts.formula)   parts.push(`<span class="cap-formula">산출식: ${{opts.formula}}</span>`);
  if (opts.source)    parts.push(`출처: ${{opts.source}}`);
  if (opts.collected) parts.push(`수집: ${{opts.collected}}`);
  if (opts.n)         parts.push(`표본: n=${{opts.n}}`);

  let drillHtml = '';
  if (opts.drillId && opts.drillContent) {{
    drillHtml = `
      <span class="cap-drill" onclick="toggleDrill('${{opts.drillId}}')">계산 내역 ▾</span>
      <div id="${{opts.drillId}}" class="drill-detail">${{opts.drillContent}}</div>`;
  }}

  return `<div class="chart-caption">${{parts.join(' · ')}}${{opts.note ? '<br>' + opts.note : ''}}${{drillHtml}}</div>`;
}}

function toggleDrill(id) {{
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === 'block' ? 'none' : 'block';
}}
/* ── 산출 근거 캡션 유틸리티 끝 ─────────────────────── */

const RAW = {data_json};
const COLORS = {colors_json};
const BRANDS_CFG = {brands_cfg_json};
const TIER_LABELS = {tier_labels_json};
const TIER_NEW = {tier_new_json};
const BRAND_TO_TIER = {brand_to_tier_json};
const SOS_SOM_DATA = {sos_som_json};

// 현재 티어 필터 상태
let _activeTier = 'ALL';

// 기준 브랜드 서브타이틀 생성
function baselineCaption(source) {{
  const base = BRANDS_CFG.find(b => b.baseline);
  if (!base) return '';
  return base.name + '=100 기준 · ' + source;
}}

// 사이드바: 티어별 그룹 렌더
(function renderSidebar() {{
  const list = document.getElementById('brand-list');
  const tiers = [...new Set(BRANDS_CFG.map(b => b.tier))].sort();
  tiers.forEach(tier => {{
    const header = document.createElement('div');
    header.className = 'tier-header';
    header.textContent = TIER_LABELS[tier] || ('Tier ' + tier);
    list.appendChild(header);
    BRANDS_CFG.filter(b => b.tier === tier).forEach(b => {{
      const el = document.createElement('div');
      el.className = 'brand-item' + (b.baseline ? ' brand-item--baseline' : '');
      el.innerHTML = `<div class="brand-dot" style="background:${{b.color}}"></div>
        <span>${{b.name}}</span>
        ${{b.baseline ? '<span class="baseline-badge">기준</span>' : ''}}`;
      list.appendChild(el);
    }});
  }});
}})();

// 서브타이틀 업데이트
document.getElementById('sub-google-rank').textContent = baselineCaption('최근 3개월 한국');
document.getElementById('sub-naver-rank').textContent = baselineCaption('블로그+뉴스 건수');

// 차트 초기화
const gc = (id) => echarts.init(document.getElementById(id));

// B-4: 겹침 검증 루틴 (window.__devMode = true 로 활성화)
function checkOverlap(chartDom, label) {{
  if (!window.__devMode) return;
  const rects = [];
  chartDom.querySelectorAll('.chart-caption, text').forEach(el => {{
    rects.push({{ el, r: el.getBoundingClientRect(), name: el.className || el.tagName }});
  }});
  for (let i = 0; i < rects.length; i++) {{
    for (let j = i + 1; j < rects.length; j++) {{
      const a = rects[i].r, b = rects[j].r;
      if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) {{
        console.warn(`[겹침 경고] ${{label}}: ${{rects[i].name}} ↔ ${{rects[j].name}}`);
      }}
    }}
  }}
}}
// window.__devMode = true;  // 개발 시 활성화

// 티어 필터: 브랜드 목록을 현재 활성 티어로 필터링 (시몬스 항상 포함)
function _filterByTier(entries) {{
  if (_activeTier === 'ALL') return entries;
  return entries.filter(([brand]) => brand === '시몬스' || BRAND_TO_TIER[brand] === _activeTier);
}}

// 티어 필터 버튼 클릭
function setTierFilter(btn, tier) {{
  document.querySelectorAll('.tier-filter').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  _activeTier = tier;
  renderGoogleRank();
  renderNaverRank();
  renderSoS();
  renderGap();
  renderMonthly();
  _updateFilterBanner();
}}

/* ── 막대 차트 높이 동적 계산 ───────────────────────── */
const BAR_HEIGHT = 28;
const BAR_GAP = 10;
const AXIS_AREA = 40;
const TOP_PAD = 10;
function calcBarChartHeight(n) {{
  return n * BAR_HEIGHT + (n - 1) * BAR_GAP + AXIS_AREA + TOP_PAD;
}}
/* ── 막대 차트 높이 동적 계산 끝 ──────────────────────── */

// 1. 구글 순위 바차트
function renderGoogleRank() {{
  const norm = RAW.google?.normalized || {{}};
  let entries = Object.entries(norm);
  entries = _filterByTier(entries);
  const sorted = entries.sort((a,b)=>b[1]-a[1]);
  if (!sorted.length) return;
  const chartDom = document.getElementById('chart-google-rank');
  const h = calcBarChartHeight(sorted.length);
  chartDom.style.height = h + 'px';
  const chart = echarts.init(chartDom);
  const vals = sorted.map(x=>x[1]).filter(v=>v!=null);
  const brandNames = sorted.map(x=>x[0]);
  const dataMax = vals.length ? Math.max(...vals) : 100;
  const xOpt = axisOption(dataMax, '', 5);
  const lm = leftMargin(brandNames);
  chart.setOption({{
    grid:{{left:lm,right:100,top:TOP_PAD,bottom:AXIS_AREA,containLabel:false}},
    xAxis:xOpt,
    yAxis:{{type:'category',data:brandNames,axisLabel:{{fontSize:12,margin:8}},axisTick:{{alignWithLabel:true}},boundaryGap:true}},
    series:[{{
      type:'bar',
      barMaxWidth:BAR_HEIGHT,
      data:sorted.map(x=>{{
        const isBase = x[0]==='시몬스';
        const tier = BRAND_TO_TIER[x[0]];
        const isCautionTier = tier === 'C' || tier === 'D';
        return {{
          value:x[1],
          itemStyle:{{
            color:COLORS[x[0]]||'#888',
            opacity: isBase ? 1 : (isCautionTier ? 0.45 : 0.75),
            borderColor: isBase ? '#c8a96e' : 'transparent',
            borderWidth: isBase ? 2 : 0
          }}
        }};
      }}),
      label:{{show:true,position:'right',fontSize:11,formatter:p=>p.value}}
    }}],
    tooltip:{{trigger:'axis',formatter:p=>{{
      const t = BRAND_TO_TIER[p[0].name] || '?';
      return `${{p[0].name}} [Tier ${{t}}]<br>${{p[0].value}} (시몬스=100)`;
    }}}}
  }});
  setTimeout(() => checkOverlap(chartDom, 'GoogleRank'), 300);
}}

// 2. 네이버 순위 바차트
function renderNaverRank() {{
  const norm = RAW.naver?.normalized || {{}};
  let entries = Object.entries(norm);
  entries = _filterByTier(entries);
  const sorted = entries.sort((a,b)=>b[1]-a[1]);
  if (!sorted.length) return;
  const chartDom = document.getElementById('chart-naver-rank');
  const h = calcBarChartHeight(sorted.length);
  chartDom.style.height = h + 'px';
  const chart = echarts.init(chartDom);
  const vals = sorted.map(x=>x[1]).filter(v=>v!=null);
  const brandNames = sorted.map(x=>x[0]);
  const dataMax = vals.length ? Math.max(...vals) : 100;
  const xOpt = axisOption(dataMax, '', 5);
  const lm = leftMargin(brandNames);
  chart.setOption({{
    grid:{{left:lm,right:100,top:TOP_PAD,bottom:AXIS_AREA,containLabel:false}},
    xAxis:xOpt,
    yAxis:{{type:'category',data:brandNames,axisLabel:{{fontSize:12,margin:8}},axisTick:{{alignWithLabel:true}},boundaryGap:true}},
    series:[{{
      type:'bar',
      barMaxWidth:BAR_HEIGHT,
      data:sorted.map(x=>{{
        const isBase = x[0]==='시몬스';
        const tier = BRAND_TO_TIER[x[0]];
        const isCautionTier = tier === 'C' || tier === 'D';
        return {{
          value:x[1],
          itemStyle:{{
            color:COLORS[x[0]]||'#888',
            opacity: isBase ? 1 : (isCautionTier ? 0.45 : 0.75),
            borderColor: isBase ? '#c8a96e' : 'transparent',
            borderWidth: isBase ? 2 : 0
          }}
        }};
      }}),
      label:{{show:true,position:'right',fontSize:11,formatter:p=>p.value}}
    }}],
    tooltip:{{trigger:'axis',formatter:p=>{{
      const t = BRAND_TO_TIER[p[0].name] || '?';
      return `${{p[0].name}} [Tier ${{t}}]<br>${{p[0].value}} (시몬스=100)`;
    }}}}
  }});
  setTimeout(() => checkOverlap(chartDom, 'NaverRank'), 300);
}}

// 이벤트 타입별 색상
const EVENT_COLORS = {{
  campaign: '#2196f3',
  product: '#4caf50',
  issue: '#f44336',
  competitor: '#ff9800',
  auto_detected: '#9e9e9e',
}};

// 3. 월별 추이 (시몬스 마지막 렌더 = 최상단 레이어) + 이벤트 마커 (T2-1)
function renderMonthly() {{
  const ms = RAW.google?.monthly_series || {{}};
  const periods = RAW.google?.periods || [];
  if(!Object.keys(ms).length) {{
    const chart = gc('chart-monthly');
    chart.setOption({{
      title: {{
        text: '월별 데이터 수집 중',
        subtext: '다음 Actions 실행 후 12개월 추이가 표시됩니다',
        left: 'center', top: 'center',
        textStyle: {{ color: '#999', fontSize: 14 }},
        subtextStyle: {{ color: '#bbb', fontSize: 12 }}
      }}
    }});
    return;
  }}
  const series = [];

  // 티어 필터 적용
  const allowedBrands = _activeTier === 'ALL'
    ? null
    : Object.entries(ms).filter(([b]) => b === '시몬스' || BRAND_TO_TIER[b] === _activeTier).map(([b])=>b);

  // 시몬스 제외한 브랜드 먼저
  Object.entries(ms).filter(([b]) => b !== '시몬스').forEach(([brand, pts]) => {{
    if (allowedBrands && !allowedBrands.includes(brand)) return;
    const color = COLORS[brand] || '#888';
    const tier = BRAND_TO_TIER[brand];
    const isCautionTier = tier === 'C' || tier === 'D';
    series.push({{
      name:brand, type:'line', data:pts.map(p=>p.value),
      lineStyle:{{color,width:1.5,opacity: isCautionTier ? 0.45 : 1}},
      itemStyle:{{color,opacity: isCautionTier ? 0.45 : 1}},
      symbol:'none',
      tooltip:{{formatter:(p)=>{{
        const pt = pts[p.dataIndex];
        return `${{brand}} [Tier ${{BRAND_TO_TIER[brand]||'?'}}]<br>${{p.name}}: ${{pt.value}}<br>CV: ${{pt.cv}} (${{pt.confidence}})`;
      }}}}
    }});
  }});
  // 시몬스 마지막 (z:10 최상단)
  if(ms['시몬스']) {{
    const pts = ms['시몬스'];
    series.push({{
      name:'시몬스', type:'line', data:pts.map(p=>p.value),
      lineStyle:{{color:'#0b0b0b',width:3}},
      itemStyle:{{color:'#0b0b0b'}},
      symbol:'circle', symbolSize:5,
      z:10,
      tooltip:{{formatter:(p)=>{{
        const pt = pts[p.dataIndex];
        return `시몬스<br>${{p.name}}: ${{pt.value}}<br>CV: ${{pt.cv}} (${{pt.confidence}})`;
      }}}}
    }});
  }}
  const pLabels = periods.map(p=>p.substring(0,7));

  // 이벤트 마커 (T2-1) — RAW.events 배열 기반 markLine
  const events = RAW.events || [];
  const markLineData = [];
  events.forEach(ev => {{
    const evPeriod = (ev.date || '').substring(0, 7);
    const xIdx = pLabels.indexOf(evPeriod);
    if (xIdx < 0) return;
    const color = EVENT_COLORS[ev.type] || '#9e9e9e';
    const isDashed = ev.type === 'auto_detected';
    markLineData.push({{
      xAxis: evPeriod,
      lineStyle: {{color, type: isDashed ? 'dashed' : 'solid', width: 1.5}},
      label: {{
        show: true,
        formatter: `${{ev.brand}} ${{ev.label}}`,
        fontSize: 9,
        color,
        position: 'insideEndTop',
        rotate: 90,
      }},
      tooltip: {{
        formatter: `${{ev.brand}}<br>${{ev.type}}<br>${{ev.label}}<br>출처: ${{ev.source}}`
      }}
    }});
  }});

  // markLine을 시몬스 시리즈 또는 별도 더미 시리즈에 추가
  const markLineSeries = {{
    type: 'line',
    name: '__events__',
    data: [],
    silent: false,
    markLine: {{
      symbol: ['none','none'],
      silent: false,
      data: markLineData,
    }}
  }};
  if (markLineData.length > 0) series.push(markLineSeries);

  const visibleBrands = series.filter(s=>s.name !== '__events__').map(s=>s.name);
  // y축 최댓값 계산
  const allMonthlyVals = Object.values(ms).flatMap(pts => pts.map(p => p.value || 0));
  const monthlyMax = allMonthlyVals.length ? Math.max(...allMonthlyVals) : 100;
  gc('chart-monthly').setOption({{
    legend:{{data:visibleBrands,bottom:0,textStyle:{{fontSize:11}},type:'scroll'}},
    grid:{{left:55,right:20,top:10,bottom:40}},
    xAxis:dateAxisOption(pLabels),
    yAxis:axisOption(monthlyMax, '', 5),
    series,
    tooltip:{{trigger:'axis'}}
  }});
}}

// 4. Share of Search 파이차트 (시몬스 강조)
function renderSoS() {{
  const sos = RAW.sos || {{}};
  let entries = Object.entries(sos);
  if (_activeTier !== 'ALL') {{
    entries = entries.filter(([name]) => name === '시몬스' || BRAND_TO_TIER[name] === _activeTier);
  }}
  const data = entries
    .sort((a,b)=>b[1]-a[1])
    .map(([name,val])=>{{
      const isBase = name === '시몬스';
      return {{
        name, value: val,
        itemStyle:{{color:COLORS[name]||'#888'}},
        selected: isBase,
        selectedOffset: isBase ? 12 : 0
      }};
    }});
  gc('chart-sos').setOption({{
    tooltip:{{trigger:'item',formatter:p=>`${{p.name}} [Tier ${{BRAND_TO_TIER[p.name]||'기준'}}]: ${{p.value}}%`}},
    legend:{{orient:'vertical',right:0,top:'center',textStyle:{{fontSize:12}}}},
    series:[{{
      type:'pie',radius:['40%','70%'],center:['40%','50%'],
      label:{{show:false}},data
    }}]
  }});
}}

// 5. 갭 분석 (시몬스 항상 포함, markLine 기준선)
function renderGap() {{
  const gaps = RAW.gap || [];
  let items = gaps.slice(0, 8);
  // 시몬스가 없으면 강제 추가 (gap=0)
  if (!items.find(x => x.brand === '시몬스')) {{
    items = [{{brand:'시몬스', gap:0}}, ...items];
  }}
  const brandNames = items.map(x=>x.brand);
  const lm = leftMargin(brandNames);
  const absMax = Math.max(...items.map(x => Math.abs(x.gap)), 1);
  const gapInterval = niceInterval(absMax * 2 * 1.1, 5);
  const halfMax = niceMax(absMax, gapInterval);
  gc('chart-gap').setOption({{
    grid:{{left:lm,right:70,top:10,bottom:10}},
    xAxis:{{type:'value',min:-halfMax,max:halfMax,interval:gapInterval,axisLabel:{{fontSize:12,formatter:v=>v>0?'+'+v:String(v)}}}},
    yAxis:{{type:'category',data:brandNames,axisLabel:{{fontSize:12}}}},
    series:[{{
      type:'bar',
      data:items.map(x=>{{
        const color = x.brand==='시몬스' ? '#0b0b0b' : x.gap > 0 ? '#1565c0' : '#c62828';
        return {{value:x.gap,itemStyle:{{color}}}};
      }}),
      label:{{show:true,position:'right',fontSize:11,
              formatter:p=>p.value>0?`+${{p.value}}`:`${{p.value}}`}},
      markLine:{{
        silent:true,
        lineStyle:{{type:'dashed',color:'#999',width:1}},
        data:[{{xAxis:0}}],
        label:{{show:false}}
      }}
    }}],
    tooltip:{{formatter:p=>`${{p.name}}<br>네이버-구글: ${{p.value>0?'+':''}}${{p.value}}`}}
  }});
}}

// T2-6: 성별 차트 — 정규화 / 인덱스 모드 토글
let _genderMode = 'norm';  // 'norm' | 'idx'
let _ageMode = 'norm';

function setGenderMode(mode) {{
  _genderMode = mode;
  document.getElementById('gender-toggle-norm').classList.toggle('active', mode === 'norm');
  document.getElementById('gender-toggle-idx').classList.toggle('active', mode === 'idx');
  document.getElementById('gender-sub').textContent = mode === 'norm'
    ? '브랜드별 성별 비율 (브랜드 내 합계=100%)'
    : '카테고리 평균=100 기준 인덱스 (138 = 카테고리 평균 대비 38% 과대색인)';
  renderGender();
}}

function setAgeMode(mode) {{
  _ageMode = mode;
  document.getElementById('age-toggle-norm').classList.toggle('active', mode === 'norm');
  document.getElementById('age-toggle-idx').classList.toggle('active', mode === 'idx');
  document.getElementById('age-sub').textContent = mode === 'norm'
    ? '브랜드별 연령대 비율 (브랜드 내 합계=100%)'
    : '카테고리 평균=100 기준 인덱스 (138 = 카테고리 평균 대비 38% 과대색인)';
  renderAge();
}}

// 인덱스 계산 헬퍼: normalized[brand][dim] → index[brand][dim] (카테고리 평균=100)
function _toIndex(brands, dims, normalized) {{
  const catAvg = {{}};
  dims.forEach(d => {{
    const vals = brands.map(b => normalized[b][d] || 0);
    catAvg[d] = vals.reduce((s,v)=>s+v, 0) / (vals.length || 1);
  }});
  const idx = {{}};
  brands.forEach(b => {{
    idx[b] = {{}};
    dims.forEach(d => {{
      idx[b][d] = catAvg[d] > 0 ? Math.round(normalized[b][d] / catAvg[d] * 100) : 0;
    }});
  }});
  return {{idx, catAvg}};
}}

// 6. 성별 차트
function renderGender() {{
  const demo = RAW.demographics || {{}};
  const brands = Object.keys(demo).filter(b=>demo[b].gender && Object.keys(demo[b].gender).length);
  if(!brands.length) {{
    document.getElementById('chart-gender').innerHTML =
      '<div class="no-data">데이터 수집 불가<br><small>DataLab 로그인 필요</small></div>';
    return;
  }}
  const genders = ['여성','남성'];
  // 브랜드별 100% 정규화
  const normalized = {{}};
  brands.forEach(b => {{
    const total = genders.reduce((s,g) => s + (demo[b].gender[g]||0), 0);
    normalized[b] = {{}};
    genders.forEach(g => {{
      normalized[b][g] = total > 0 ? Math.round(demo[b].gender[g]/total*1000)/10 : 0;
    }});
  }});

  let displayData = normalized;
  let xMax = 100;
  let xFmt = v => v + '%';
  let stackMode = 'total';
  let labelFmt = p => p.value > 0 ? p.value + '%' : '';
  let tooltipFmt = params => {{
    const brand = params[0].name;
    return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}}%`).join('<br>');
  }};

  if (_genderMode === 'idx') {{
    const {{idx}} = _toIndex(brands, genders, normalized);
    displayData = idx;
    xMax = null;
    xFmt = v => v;
    stackMode = null;  // 인덱스 모드는 스택 해제
    labelFmt = p => p.value > 0 ? p.value : '';
    tooltipFmt = params => {{
      const brand = params[0].name;
      return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}} (평균=100)`).join('<br>');
    }};
  }}

  const series = genders.map(g=>{{
    return {{
      name:g, type:'bar',
      ...(stackMode ? {{stack: stackMode}} : {{}}),
      data:brands.map(b=>displayData[b][g]),
      itemStyle:{{color: g==='여성'?'#e91e63':'#1565c0'}},
      label:{{show:true,formatter:labelFmt,fontSize:10}}
    }};
  }});
  const lmGender = leftMargin(brands);
  const chartOpt = {{
    legend:{{data:genders,bottom:0,textStyle:{{fontSize:12}}}},
    grid:{{left:lmGender,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',max:xMax||undefined,interval:xMax===100?25:undefined,axisLabel:{{fontSize:12,formatter:xFmt}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:12}}}},
    series,
    tooltip:{{trigger:'axis',formatter:tooltipFmt}}
  }};
  gc('chart-gender').setOption(chartOpt);
}}

// 7. 연령대 차트
function renderAge() {{
  const demo = RAW.demographics || {{}};
  const brands = Object.keys(demo).filter(b=>demo[b].age && Object.keys(demo[b].age).length);
  if(!brands.length) {{
    document.getElementById('chart-age').innerHTML =
      '<div class="no-data">데이터 수집 불가<br><small>DataLab 로그인 필요</small></div>';
    return;
  }}
  const ages = ['10대','20대','30대','40대','50대','60대+'];
  const ageColors = ['#9c27b0','#3f51b5','#2196f3','#4caf50','#ff9800','#795548'];
  // 브랜드별 100% 정규화
  const normalized = {{}};
  brands.forEach(b => {{
    const total = ages.reduce((s,a) => s + (demo[b].age[a]||0), 0);
    normalized[b] = {{}};
    ages.forEach(a => {{
      normalized[b][a] = total > 0 ? Math.round(demo[b].age[a]/total*1000)/10 : 0;
    }});
  }});

  let displayData = normalized;
  let xMax = 100;
  let xFmt = v => v + '%';
  let stackMode = 'total';
  let labelFmt = p => p.value > 0 ? p.value + '%' : '';
  let tooltipFmt = params => {{
    const brand = params[0].name;
    return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}}%`).join('<br>');
  }};

  if (_ageMode === 'idx') {{
    const {{idx}} = _toIndex(brands, ages, normalized);
    displayData = idx;
    xMax = null;
    xFmt = v => v;
    stackMode = null;
    labelFmt = p => p.value > 0 ? p.value : '';
    tooltipFmt = params => {{
      const brand = params[0].name;
      return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}} (평균=100)`).join('<br>');
    }};
  }}

  const series = ages.map((age,i)=>{{
    return {{
      name:age, type:'bar',
      ...(stackMode ? {{stack: stackMode}} : {{}}),
      data:brands.map(b=>displayData[b][age]),
      itemStyle:{{color:ageColors[i]}},
      label:{{show:true,formatter:labelFmt,fontSize:10}}
    }};
  }});
  const lmAge = leftMargin(brands);
  const chartOpt = {{
    legend:{{data:ages,bottom:0,textStyle:{{fontSize:12}}}},
    grid:{{left:lmAge,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',max:xMax||undefined,interval:xMax===100?25:undefined,axisLabel:{{fontSize:12,formatter:xFmt}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:12}}}},
    series,
    tooltip:{{trigger:'axis',formatter:tooltipFmt}}
  }};
  gc('chart-age').setOption(chartOpt);
}}

// 8. CV 신뢰도 테이블 — Google Trends monthly_series 기반
function renderCVTable() {{
  const ms = RAW.google?.monthly_series || {{}};
  const brands = Object.keys(ms);

  if (!brands.length) {{
    document.getElementById('cv-table').innerHTML = `
      <table class="data-table">
        <thead><tr>
          <th>브랜드</th><th>평균 지수</th><th>표준편차</th><th>CV</th><th>기간</th><th>안정성</th>
        </tr></thead>
        <tbody id="cv-table-body">
          <tr><td colspan="6" style="text-align:center;color:#999;padding:20px">데이터 축적 중 — monthly_series 수집 후 표시됩니다</td></tr>
        </tbody>
      </table>
      <span id="cv-caption" style="font-size:10px;color:#767676;display:block;margin-top:6px;padding-top:6px;border-top:1px solid #f0f0f0;"></span>`;
    return;
  }}

  // 시몬스 먼저, 나머지는 브랜드명 순
  const ordered = ['시몬스', ...brands.filter(b => b !== '시몬스')];

  const rows = ordered.map(brand => {{
    const pts = ms[brand] || [];
    const vals = pts.map(p => p.value).filter(v => v != null && !isNaN(v));
    const n = vals.length;
    const isBase = brand === '시몬스';

    if (n < 3) {{
      return `<tr class="${{isBase ? 'simmons-sticky' : ''}}">
        <td>${{isBase ? '<strong>' + brand + '</strong> <span style="font-size:9px;color:#c8a96e;">●기준</span>' : brand}}</td>
        <td colspan="5" style="color:#999;font-size:12px;">표본 부족 (${{n}}개월, 최소 3개월 필요)</td>
      </tr>`;
    }}

    const mean = vals.reduce((a, b) => a + b, 0) / n;
    const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1));
    const cv = mean > 0 ? std / mean : 0;

    let status, statusColor, cvCls;
    if (cv <= 0.05) {{ status = '안정'; statusColor = '#27ae60'; cvCls = 'cv-stable'; }}
    else if (cv <= 0.15) {{ status = '주의'; statusColor = '#f39c12'; cvCls = 'cv-warning'; }}
    else {{ status = '불안정'; statusColor = '#e74c3c'; cvCls = 'cv-unstable'; }}

    return `<tr class="${{isBase ? 'simmons-sticky' : ''}}">
      <td>${{isBase ? '<strong>' + brand + '</strong> <span style="font-size:9px;color:#c8a96e;">●기준</span>' : brand}}</td>
      <td>${{mean.toFixed(1)}}</td>
      <td>${{std.toFixed(2)}}</td>
      <td><span class="${{cvCls}}">${{(cv * 100).toFixed(1)}}%</span></td>
      <td>${{n}}개월</td>
      <td style="color:${{statusColor}};font-weight:600">${{status}}</td>
    </tr>`;
  }}).join('');

  const nMonths = Math.max(...ordered.map(b => {{
    const pts = ms[b] || [];
    return pts.map(p => p.value).filter(v => v != null && !isNaN(v)).length;
  }}), 0);

  document.getElementById('cv-table').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>브랜드</th><th>평균 지수</th><th>표준편차</th><th>CV</th><th>기간</th><th>안정성</th>
      </tr></thead>
      <tbody id="cv-table-body">${{rows}}</tbody>
    </table>
    <span id="cv-caption" style="font-size:10px;color:#767676;display:block;margin-top:6px;padding-top:6px;border-top:1px solid #f0f0f0;">산출식: CV = 표준편차 ÷ 평균 · 기준: Google Trends 월별 지수 최근 ${{nMonths}}개월 · 판정: ≤5% 안정 / ≤15% 주의 / &gt;15% 불안정</span>`;
}}

// 9. DataLab 트렌드 차트 (§12)
function renderDatalab() {{
  const dl = RAW.datalab || {{}};
  const ms = dl.monthly_series || {{}};
  const periods = dl.periods || [];
  if (!Object.keys(ms).length) return;

  document.getElementById('datalab-row').style.display = '';

  const series = [];
  Object.entries(ms).filter(([b]) => b !== '시몬스').forEach(([brand, pts]) => {{
    const color = COLORS[brand] || '#888';
    series.push({{
      name: brand, type: 'line', data: pts.map(p => p.value),
      lineStyle: {{color, width: 1.5}}, itemStyle: {{color}}, symbol: 'none'
    }});
  }});
  if (ms['시몬스']) {{
    const pts = ms['시몬스'];
    series.push({{
      name: '시몬스', type: 'line', data: pts.map(p => p.value),
      lineStyle: {{color: '#0b0b0b', width: 3}}, itemStyle: {{color: '#0b0b0b'}},
      symbol: 'circle', symbolSize: 5, z: 10
    }});
  }}
  const pLabels = periods.map(p => p.substring(0, 7));
  const allDlVals = Object.values(ms).flatMap(pts => pts.map(p => p.value || 0));
  const dlMax = allDlVals.length ? Math.max(...allDlVals) : 100;
  gc('chart-datalab').setOption({{
    legend: {{data: Object.keys(ms), bottom: 0, textStyle: {{fontSize: 11}}, type: 'scroll'}},
    grid: {{left: 55, right: 20, top: 10, bottom: 40}},
    xAxis: dateAxisOption(pLabels),
    yAxis: axisOption(dlMax, '', 5),
    series,
    tooltip: {{trigger: 'axis'}}
  }});
}}

// T2-3: SoS vs SoM 산점도
function renderSoSSoM() {{
  const data = SOS_SOM_DATA;
  const validData = data.filter(d => d.som !== null && d.som !== undefined);
  if (!validData.length) return;

  document.getElementById('section-sos-som').style.display = '';

  // 대각선 기준선 (SoS = SoM)
  const allVals = validData.map(d => Math.max(d.sos, d.som || 0));
  const maxVal = Math.max(...allVals) * 1.2;

  const scatterData = validData.map(d => {{
    const isCautionTier = d.tier === 'C' || d.tier === 'D';
    return {{
      name: d.brand,
      value: [d.sos, d.som],
      itemStyle: {{
        color: COLORS[d.brand] || '#888',
        opacity: isCautionTier ? 0.45 : 0.9,
      }},
      symbol: isCautionTier ? 'triangle' : 'circle',
      symbolSize: 14,
      label: {{
        show: true,
        formatter: d.brand,
        position: 'top',
        fontSize: 10,
        color: COLORS[d.brand] || '#333',
      }},
    }};
  }});

  const sosSomMaxX = Math.max(...validData.map(d => d.sos), 1);
  const sosSomMaxY = Math.max(...validData.map(d => d.som || 0), 1);
  const xOptSoSSoM = Object.assign(axisOption(sosSomMaxX, '%', 5), {{name:'SoS (%)',nameLocation:'middle',nameGap:30}});
  const yOptSoSSoM = Object.assign(axisOption(sosSomMaxY, '%', 5), {{name:'SoM (%)',nameLocation:'middle',nameGap:40}});
  gc('chart-sos-som').setOption({{
    grid: {{left: 60, right: 30, top: 30, bottom: 50}},
    xAxis: xOptSoSSoM,
    yAxis: yOptSoSSoM,
    series: [
      {{
        type: 'scatter',
        data: scatterData,
        label: {{show: true}},
        markLine: {{
          silent: true,
          symbol: ['none', 'none'],
          lineStyle: {{type: 'dashed', color: '#aaa', width: 1}},
          data: [
            [
              {{coord: [0, 0], label: {{show: false}}}},
              {{coord: [maxVal, maxVal], label: {{show: true, formatter: 'SoS = SoM', fontSize: 10, color: '#aaa'}}}},
            ]
          ],
        }},
      }}
    ],
    tooltip: {{
      formatter: p => {{
        const d = validData.find(x => x.brand === p.name);
        if (!d) return p.name;
        return `${{p.name}} [Tier ${{d.tier}}]<br>SoS: ${{d.sos}}%<br>SoM: ${{d.som}}%<br>${{d.caution ? '⚠ 침대 외 사업 포함' : ''}}`;
      }}
    }},
  }});
}}

// 11. 인사이트 패널
function renderInsights() {{
  const norm_g = RAW.google?.normalized || {{}};
  const norm_n = RAW.naver?.normalized || {{}};
  const g_rank = Object.entries(norm_g).sort((a,b)=>b[1]-a[1]);
  const n_rank = Object.entries(norm_n).sort((a,b)=>b[1]-a[1]);
  const g_pos = g_rank.findIndex(x=>x[0]==='시몬스')+1;
  const n_pos = n_rank.findIndex(x=>x[0]==='시몬스')+1;
  const g_top = g_rank[0]?.[0] || '-';
  const n_top = n_rank[0]?.[0] || '-';

  document.getElementById('insight-simmons').innerHTML = `
    <div class="insight-item ${{g_pos<=3?'good':'warn'}}">
      구글 순위: <b>${{g_pos}}위 / 11개</b><br>
      1위: ${{g_top}}
    </div>
    <div class="insight-item ${{n_pos<=3?'good':'warn'}}">
      네이버 순위: <b>${{n_pos}}위 / 11개</b><br>
      1위: ${{n_top}}
    </div>
    <div class="insight-item">
      구글 지수: <b>100</b> (기준점)<br>
      네이버 지수: <b>${{norm_n['시몬스']||0}}</b>
    </div>`;

  const gaps = RAW.gap || [];
  const findings = [];
  const sGap = gaps.find(x=>x.brand==='시몬스');
  if(sGap) {{
    if(sGap.gap > 20) findings.push({{type:'good',text:`시몬스는 네이버에서 구글보다 ${{sGap.gap}}pt 높음 → 네이버 강세`}});
    else if(sGap.gap < -20) findings.push({{type:'warn',text:`시몬스는 구글에서 네이버보다 ${{Math.abs(sGap.gap)}}pt 높음 → 네이버 보강 필요`}});
  }}
  if(g_top !== '시몬스') findings.push({{type:'warn',text:`구글 1위 ${{g_top}} 집중 모니터링 필요`}});
  if(n_top !== '시몬스') findings.push({{type:'warn',text:`네이버 1위 ${{n_top}} 집중 모니터링 필요`}});

  document.getElementById('insight-findings').innerHTML = findings.length
    ? findings.map(f=>`<div class="insight-item ${{f.type}}">${{f.text}}</div>`).join('')
    : '<div class="insight-item">특이사항 없음</div>';

  const changes = RAW.change_points || [];
  const changeEl = document.getElementById('insight-changes');
  if (!changes.length) {{
    // 절대값 순위로 대체 표시
    const norm = RAW.google?.normalized || {{}};
    const sorted = Object.entries(norm)
      .filter(([,v]) => v > 0)
      .sort(([,a],[,b]) => b - a);
    const top3 = sorted.slice(0, 3);
    const bot3 = sorted.slice(-3).reverse();

    changeEl.innerHTML = `
      <div style="grid-column:1/-1">
        <p style="color:#888;font-size:12px;margin-bottom:8px">전월 비교 데이터 없음 — 이번 달 검색 지수 현황</p>
        <div style="display:flex;gap:24px">
          <div>
            <p style="font-size:11px;font-weight:600;color:#27ae60;margin-bottom:4px">▲ 상위 브랜드</p>
            ${{top3.map(([b,v],i) => `<p style="font-size:13px">${{i+1}}위 ${{b === '시몬스' ? '<strong>'+b+'</strong>' : b}} <span style="color:#888">${{v.toFixed(1)}}</span></p>`).join('')}}
          </div>
          <div>
            <p style="font-size:11px;font-weight:600;color:#e74c3c;margin-bottom:4px">▼ 하위 브랜드</p>
            ${{bot3.map(([b,v],i) => `<p style="font-size:13px">${{i+1}}위 ${{b}} <span style="color:#888">${{v.toFixed(1)}}</span></p>`).join('')}}
          </div>
        </div>
        <p style="font-size:11px;color:#aaa;margin-top:8px">다음 달부터 전월 대비 변화점 자동 탐지 시작</p>
      </div>`;
  }} else {{
    changeEl.innerHTML = changes.slice(0,5).map(c=>`
        <div class="insight-item ${{c.direction==='급등'?'good':'warn'}}">
          ${{c.brand}} · ${{c.period}}<br>
          <b>${{c.direction}} ${{c.pct_change > 0?'+':''}}${{c.pct_change}}%</b>
        </div>`).join('');
  }}
}}

// T3-3: 기본값 변경 배너 로직
function _updateFilterBanner() {{
  const rangeBtn = document.querySelector('.filter-btn.active[data-range]');
  const tierBtn = document.querySelector('.tier-filter.active');
  const banner = document.getElementById('filter-changed-banner');
  if (!banner) return;
  const rangeDefault = (rangeBtn?.dataset?.range === 'today 3-m') || (!rangeBtn);
  const tierDefault = tierBtn?.dataset?.tier === 'ALL' || !tierBtn;
  banner.style.display = (rangeDefault && tierDefault) ? 'none' : 'block';
}}

function setRange(btn, range) {{
  document.querySelectorAll('.filter-btn[data-range]').forEach(b=>b.classList.remove('active'));
  btn.dataset.range = range;
  btn.classList.add('active');
  _updateFilterBanner();
}}

// T3-3: PDF 인쇄 표지 자동 기록
function exportPrint() {{
  const cover = document.getElementById('cover-page');
  const rangeBtn = document.querySelector('.filter-btn.active[data-range]');
  const tierBtn = document.querySelector('.tier-filter.active');
  const rangeLabel = rangeBtn?.textContent || '최근 3개월';
  const tierLabel = tierBtn?.textContent || '전체';
  if (cover) {{
    const stateEl = cover.querySelector('#print-filter-state');
    if (stateEl) stateEl.textContent = `보고 기준: ${{rangeLabel}} · ${{tierLabel}}`;
  }}
  window.print();
}}

// CSV 내보내기 (시몬스 첫 행, 헤더 주석)
function exportCSV() {{
  const norm_g = RAW.google?.normalized || {{}};
  const norm_n = RAW.naver?.normalized || {{}};
  const sos = RAW.sos || {{}};
  const allNames = Object.keys({{...norm_g,...norm_n}});
  const others = allNames.filter(n => n !== '시몬스');
  const ordered = ['시몬스', ...others];
  const rows = [
    ['# 시몬스 브랜드 트렌드 리포트', '', '', ''],
    ['브랜드','구글 지수(시몬스=100)','네이버 지수(시몬스=100)','SoS(%)']
  ];
  ordered.forEach(name=>{{
    rows.push([name, norm_g[name]||0, norm_n[name]||0, sos[name]||0]);
  }});
  const csv = rows.map(r=>r.join(',')).join('\\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,\\uFEFF' + encodeURIComponent(csv);
  a.download = 'simmons_trend_{report_month}.csv';
  a.click();
}}

// 전체 렌더
renderGoogleRank();
renderNaverRank();
renderMonthly();
renderDatalab();
renderSoS();
renderGap();
renderGender();
renderAge();
renderCVTable();
renderSoSSoM();
renderInsights();

// ── C-2: 섹션별 산출 근거 캡션 삽입 ──────────────────
(function insertCaptions() {{
  const collected = RAW.meta?.collected_at || '';

  // Share of Search 캡션
  const sosDrillContent = (() => {{
    const sos = RAW.sos || {{}};
    return Object.entries(sos).map(([b,v]) => `${{b}}: ${{v.toFixed(2)}}%`).join('<br>') || '데이터 없음';
  }})();
  const sosCaption = buildCaption({{
    formula: 'SoS = 자사 검색량 ÷ 전체 브랜드 합 × 100',
    source: 'Google Trends / Naver DataLab',
    collected,
    n: Object.keys(RAW.sos || {{}}).length + '개 브랜드',
    note: '분모: 11개 브랜드 전체 합산. Tier C(종합가구) 브랜드 포함으로 직접 비교 주의.',
    drillId: 'drill-sos',
    drillContent: sosDrillContent
  }});
  document.getElementById('section-sos')?.insertAdjacentHTML('beforeend', sosCaption);

  // 구글 검색 지수 순위 캡션 (section-rank 카드 첫 번째 자식)
  const googleCaption = buildCaption({{
    formula: '시몬스=100 기준 상대지수 = (브랜드값 ÷ 시몬스값) × 100',
    source: 'Google Trends (지역: KR)',
    collected,
    note: '검색 표본 기반 상대지수. 절대 검색량이 아님. <a href="#section-appendix">키워드 정의 →</a>'
  }});
  const rankSection = document.getElementById('section-rank');
  if (rankSection) {{
    const firstCard = rankSection.querySelector('.card');
    if (firstCard) firstCard.insertAdjacentHTML('beforeend', googleCaption);
  }}

  // 네이버 콘텐츠 노출량 캡션
  const naverCaption = buildCaption({{
    formula: '블로그 건수 + 뉴스 건수',
    source: 'Naver 검색 API (blog + news)',
    collected,
    note: '⚠ 검색 수요가 아닌 콘텐츠 발행량 지표. 브랜드 자체 마케팅 물량에 직접 좌우됨.'
  }});
  document.getElementById('section-naver-rank')?.insertAdjacentHTML('beforeend', naverCaption);

  // 월별 검색 트렌드 추이 캡션
  const warnings = RAW.google?.warnings || [];
  const monthlyCaption = buildCaption({{
    formula: '시몬스=100 기준 월별 정규화 지수',
    source: 'Google Trends (지역: KR)',
    collected,
    note: '결측월: ' + (warnings.length ? warnings.join(', ') : '없음')
  }});
  document.getElementById('section-trend')?.querySelector('.card')?.insertAdjacentHTML('beforeend', monthlyCaption);

  // 구글 vs 네이버 갭 캡션
  const gapCaption = buildCaption({{
    formula: 'Gap = Google 정규화 지수 − Naver 정규화 지수 (양수: 구글 우세)',
    source: 'Google Trends + Naver 검색 API',
    collected
  }});
  document.getElementById('section-gap')?.insertAdjacentHTML('beforeend', gapCaption);

  // 성별·연령 인덱스 캡션
  const demoCaption = buildCaption({{
    formula: '인덱스 = (브랜드 비율 ÷ 카테고리 평균) × 100 (100 초과: 해당 세그먼트 과대색인)',
    source: 'Naver DataLab',
    collected,
    note: '카테고리 평균 = 11개 브랜드 단순 평균'
  }});
  document.getElementById('section-demo')?.insertAdjacentHTML('beforeend', demoCaption);
}})();
// ── C-2 캡션 삽입 끝 ──────────────────────────────────

window.addEventListener('resize', ()=>{{
  ['chart-google-rank','chart-naver-rank','chart-monthly','chart-datalab',
   'chart-sos','chart-gap','chart-gender','chart-age','chart-sos-som']
  .forEach(id=>{{const el=document.getElementById(id);if(el){{const inst=echarts.getInstanceByDom(el);if(inst)inst.resize();}}}});
}});
</script>
</body>
</html>"""
    return html
