import json
import os
from datetime import datetime, timedelta
from brand_config import BRANDS, TIER_LABELS
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
        '<div style="font-size:10px;color:#999;margin-top:8px;text-align:right;">※ 전월 스냅샷 없음 — 비교 기준월 데이터 축적 후 전월비 표시</div>'

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


def build_dashboard(data, report_month, collected_at, confidence_score):
    colors = _brand_colors()
    data_json = json.dumps(data, ensure_ascii=False)
    colors_json = json.dumps(colors, ensure_ascii=False)
    brands_cfg_json = json.dumps(BRANDS, ensure_ascii=False)
    tier_labels_json = json.dumps({str(k): v for k, v in TIER_LABELS.items()}, ensure_ascii=False)

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
.kpi-note{{font-size:10px;color:#aaa;}}

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

/* 인쇄 */
@media print {{
  #top-header,#sidebar{{display:none;}}
  #layout{{height:auto;}}
  #main{{overflow:visible;padding:0;}}
  .card{{break-inside:avoid;}}
  .kpi-strip{{break-inside:avoid;}}
  .no-print{{display:none;}}
  h2{{break-after:avoid;}}
}}
</style>
</head>
<body>

<!-- 상단 헤더 -->
<div id="top-header">
  <div class="title">시몬스 브랜드 트렌드 대시보드 · {report_month}</div>
  <div class="meta">
    <span>수집: {collected_at}</span>
    <span>대상: 11개 브랜드</span>
    <span class="conf-badge">{conf_label} {confidence_score}점</span>
  </div>
</div>

<div id="layout">

<!-- 좌측 사이드바 -->
<div id="sidebar">
  <h3>기간</h3>
  <button class="filter-btn active" onclick="setRange(this,'today 3-m')">최근 3개월</button>
  <button class="filter-btn" onclick="setRange(this,'today 6-m')">최근 6개월</button>
  <button class="filter-btn" onclick="setRange(this,'today 12-m')">최근 12개월</button>

  <h3>브랜드</h3>
  <div id="brand-list"></div>

  <h3>내보내기</h3>
  <button class="filter-btn" onclick="exportCSV()">CSV 다운로드</button>
  <button class="filter-btn" onclick="window.print()">인쇄 / PDF</button>
</div>

<!-- 메인 콘텐츠 (결론 우선 → 근거 데이터) -->
<div id="main">

  <!-- ① KPI 요약 스트립 (T1-2) -->
  <div class="chart-row">
    {kpi_strip_html}
  </div>

  <!-- ② 핵심 시사점 + 시몬스 포지셔닝 + 주요 발견 (T1-1, T1-4) -->
  <div class="chart-row">
    <div class="summary-grid">
      <div class="card">
        <div class="section-title">주요 시사점</div>
        <div id="insight-commentary" style="font-size:12px;line-height:1.7;color:#333;"></div>
        <div style="margin-top:16px;padding-top:10px;border-top:1px solid #eee;
                    font-size:11px;color:#999;">
          작성: 자동 생성 / 검수: ______
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px;">
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
    </div>
    <div class="card">
      <div class="card-title">구글 vs 네이버 갭 분석</div>
      <div class="card-sub">네이버 지수 − 구글 지수 (양수=네이버 강세 / 음수=구글 강세)</div>
      <div id="chart-gap" style="height:320px;"></div>
    </div>
  </div>

  <!-- ⑥ 구글 순위 + 네이버 콘텐츠 노출량 (T1-4 라벨 변경) -->
  <div class="chart-row col2" id="section-rank">
    <div class="card">
      <div class="card-title">구글 검색 지수 순위
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub" id="sub-google-rank">시몬스=100 기준 · 최근 3개월 한국</div>
      <div id="chart-google-rank" style="height:420px;"></div>
    </div>
    <div class="card" id="section-naver-rank">
      <div class="card-title">네이버 콘텐츠 노출량
        <span class="source-badge badge-naver">Naver Search</span>
      </div>
      <div class="card-sub" id="sub-naver-rank">시몬스=100 기준 · 블로그+뉴스 건수</div>
      <div id="chart-naver-rank" style="height:380px;"></div>
      <div style="font-size:10px;color:#999;margin-top:8px;padding-top:8px;border-top:1px solid #f0f0f0;">
        ※ 검색 수요가 아닌 콘텐츠 발행량 지표. 브랜드 자체 마케팅 활동량이 반영됨.
      </div>
    </div>
  </div>

  <!-- ⑦ 월별 추이 -->
  <div class="chart-row">
    <div class="card">
      <div class="card-title">월별 검색 트렌드 추이
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub">주요 브랜드 · 음영은 신뢰구간(CV) · 출처: Google Trends · 기준: 시몬스=100</div>
      <div id="chart-monthly" style="height:420px;"></div>
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
    </div>
  </div>

  <!-- ⑧ 성별 / 연령대 (T1-3 MoM 컬럼은 데이터 축적 후 추가) -->
  <div class="chart-row col2" id="section-demo">
    <div class="card">
      <div class="card-title">성별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div class="card-sub">브랜드별 성별 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-gender" style="height:320px;"></div>
    </div>
    <div class="card">
      <div class="card-title">연령대별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div class="card-sub">브랜드별 연령대 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-age" style="height:320px;"></div>
    </div>
  </div>

  <!-- ⑨ DART 매출 (§13, 수집 시 표시) -->
  <div class="chart-row" id="dart-row" style="display:none;">
    <div class="card">
      <div class="card-title">공시 매출 현황
        <span class="source-badge" style="background:#f3e5f5;color:#6a1b9a;">네이버 증권</span>
      </div>
      <div class="card-sub">⚠ 종합가구(한샘·현대리바트·일룸)·렌탈(코웨이) 브랜드는 침대 외 사업 포함 — 직접 비교 주의</div>
      <div id="dart-table"></div>
    </div>
  </div>

  <!-- ⑩ 부록: 데이터 신뢰도 상세 (T3-1 준비, 현재는 CV 테이블) -->
  <div class="chart-row" id="section-cv">
    <div class="card">
      <div class="card-title">부록 — 데이터 신뢰도 상세 (CV 분석)</div>
      <div class="card-sub">CV≤0.05 안정(녹) · CV≤0.15 주의(주황) · CV>0.15 불안정(빨강)
        · 출처: Naver Search API · 기준: 3회 반복 수집 중앙값
      </div>
      <div id="cv-table"></div>
    </div>
  </div>

</div><!-- /main -->

</div><!-- /layout -->

<script>
const RAW = {data_json};
const COLORS = {colors_json};
const BRANDS_CFG = {brands_cfg_json};
const TIER_LABELS = {tier_labels_json};

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

// 1. 구글 순위 바차트
function renderGoogleRank() {{
  const norm = RAW.google?.normalized || {{}};
  const sorted = Object.entries(norm).sort((a,b)=>b[1]-a[1]);
  const chart = gc('chart-google-rank');
  chart.setOption({{
    grid:{{left:90,right:20,top:10,bottom:10}},
    xAxis:{{type:'value',max:Math.max(...Object.values(norm))+10,axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:sorted.map(x=>x[0]),axisLabel:{{fontSize:11}}}},
    series:[{{
      type:'bar',
      data:sorted.map(x=>{{
        const isBase = x[0]==='시몬스';
        return {{
          value:x[1],
          itemStyle:{{
            color:COLORS[x[0]]||'#888',
            opacity: isBase ? 1 : 0.75,
            borderColor: isBase ? '#c8a96e' : 'transparent',
            borderWidth: isBase ? 2 : 0
          }}
        }};
      }}),
      label:{{show:true,position:'right',fontSize:11,formatter:p=>p.value}}
    }}],
    tooltip:{{trigger:'axis',formatter:p=>`${{p[0].name}}: ${{p[0].value}} (시몬스=100)`}}
  }});
}}

// 2. 네이버 순위 바차트
function renderNaverRank() {{
  const norm = RAW.naver?.normalized || {{}};
  const sorted = Object.entries(norm).sort((a,b)=>b[1]-a[1]);
  const chart = gc('chart-naver-rank');
  chart.setOption({{
    grid:{{left:90,right:20,top:10,bottom:10}},
    xAxis:{{type:'value',max:Math.max(...Object.values(norm))+10,axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:sorted.map(x=>x[0]),axisLabel:{{fontSize:11}}}},
    series:[{{
      type:'bar',
      data:sorted.map(x=>{{
        const isBase = x[0]==='시몬스';
        return {{
          value:x[1],
          itemStyle:{{
            color:COLORS[x[0]]||'#888',
            opacity: isBase ? 1 : 0.75,
            borderColor: isBase ? '#c8a96e' : 'transparent',
            borderWidth: isBase ? 2 : 0
          }}
        }};
      }}),
      label:{{show:true,position:'right',fontSize:11,formatter:p=>p.value}}
    }}],
    tooltip:{{trigger:'axis',formatter:p=>`${{p[0].name}}: ${{p[0].value}} (시몬스=100)`}}
  }});
}}

// 3. 월별 추이 (시몬스 마지막 렌더 = 최상단 레이어)
function renderMonthly() {{
  const ms = RAW.google?.monthly_series || {{}};
  const periods = RAW.google?.periods || [];
  if(!Object.keys(ms).length) return;
  const series = [];
  // 시몬스 제외한 브랜드 먼저
  Object.entries(ms).filter(([b]) => b !== '시몬스').forEach(([brand, pts]) => {{
    const color = COLORS[brand] || '#888';
    series.push({{
      name:brand, type:'line', data:pts.map(p=>p.value),
      lineStyle:{{color,width:1.5}},
      itemStyle:{{color}},
      symbol:'none',
      tooltip:{{formatter:(p)=>{{
        const pt = pts[p.dataIndex];
        return `${{brand}}<br>${{p.name}}: ${{pt.value}}<br>CV: ${{pt.cv}} (${{pt.confidence}})`;
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
  gc('chart-monthly').setOption({{
    legend:{{data:Object.keys(ms),bottom:0,textStyle:{{fontSize:11}},type:'scroll'}},
    grid:{{left:45,right:20,top:10,bottom:90}},
    xAxis:{{type:'category',data:pLabels,axisLabel:{{fontSize:10,rotate:45,interval:0}}}},
    yAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis'}}
  }});
}}

// 4. Share of Search 파이차트 (시몬스 강조)
function renderSoS() {{
  const sos = RAW.sos || {{}};
  const data = Object.entries(sos)
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
    tooltip:{{trigger:'item',formatter:p=>`${{p.name}}: ${{p.value}}%`}},
    legend:{{orient:'vertical',right:0,top:'center',textStyle:{{fontSize:11}}}},
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
  gc('chart-gap').setOption({{
    grid:{{left:90,right:20,top:10,bottom:10}},
    xAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:items.map(x=>x.brand),axisLabel:{{fontSize:11}}}},
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

// 6. 성별 차트 (브랜드별 100% 정규화)
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
  const series = genders.map(g=>{{
    return {{
      name:g, type:'bar', stack:'total',
      data:brands.map(b=>normalized[b][g]),
      itemStyle:{{color: g==='여성'?'#e91e63':'#1565c0'}},
      label:{{show:true,formatter:p=>p.value>0?p.value+'%':'',fontSize:10}}
    }};
  }});
  gc('chart-gender').setOption({{
    legend:{{data:genders,bottom:0}},
    grid:{{left:80,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',max:100,axisLabel:{{fontSize:11,formatter:v=>v+'%'}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis',formatter:params=>{{
      const brand = params[0].name;
      return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}}%`).join('<br>');
    }}}}
  }});
}}

// 7. 연령대 차트 (브랜드별 100% 정규화)
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
  const series = ages.map((age,i)=>{{
    return {{
      name:age, type:'bar', stack:'total',
      data:brands.map(b=>normalized[b][age]),
      itemStyle:{{color:ageColors[i]}},
      label:{{show:true,formatter:p=>p.value>0?p.value+'%':'',fontSize:10}}
    }};
  }});
  gc('chart-age').setOption({{
    legend:{{data:ages,bottom:0,textStyle:{{fontSize:10}}}},
    grid:{{left:80,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',max:100,axisLabel:{{fontSize:11,formatter:v=>v+'%'}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis',formatter:params=>{{
      const brand = params[0].name;
      return brand + '<br>' + params.map(p=>`${{p.seriesName}}: ${{p.value}}%`).join('<br>');
    }}}}
  }});
}}

// 8. CV 신뢰도 테이블 (시몬스 sticky, std=0→측정불가)
function renderCVTable() {{
  const stats = RAW.naver?.stats || {{}};
  // 시몬스 먼저
  const allNames = ['시몬스', ...Object.keys(stats).filter(n=>n!=='시몬스')];
  const rows = allNames.filter(n=>stats[n]).map(name=>{{
    const s = stats[name];
    const isBase = name === '시몬스';
    const isMeasurable = !(s.std === 0 && s.cv === 0);
    let cvCell, confCell;
    if (!isMeasurable) {{
      cvCell = '<span class="cv-na">측정 불가</span>';
      confCell = '<span class="cv-na">—</span>';
    }} else {{
      const cls = s.confidence==='stable'?'cv-stable':s.confidence==='warning'?'cv-warning':'cv-unstable';
      const label = s.confidence==='stable'?'안정':s.confidence==='warning'?'주의':'불안정';
      cvCell = `<span class="${{cls}}">${{(s.cv*100).toFixed(1)}}%</span>`;
      confCell = `<span class="${{cls}}">${{label}}</span>`;
    }}
    return `<tr class="${{isBase?'simmons-sticky':''}}">
      <td>${{name}}${{isBase?' <span style="font-size:9px;color:#c8a96e;">●기준</span>':''}}</td>
      <td>${{s.median}}</td>
      <td>${{cvCell}}</td>
      <td>${{confCell}}</td>
      <td>${{s.outliers_removed}}개</td>
    </tr>`;
  }}).join('');
  document.getElementById('cv-table').innerHTML = `
    <table class="data-table">
      <thead><tr>
        <th>브랜드</th><th>중앙값</th><th>CV</th><th>신뢰도</th><th>이상치 제거</th>
      </tr></thead>
      <tbody>${{rows}}</tbody>
    </table>`;
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
  gc('chart-datalab').setOption({{
    legend: {{data: Object.keys(ms), bottom: 0, textStyle: {{fontSize: 11}}, type: 'scroll'}},
    grid: {{left: 45, right: 20, top: 10, bottom: 90}},
    xAxis: {{type: 'category', data: pLabels, axisLabel: {{fontSize: 10, rotate: 45, interval: 0}}}},
    yAxis: {{type: 'value', axisLabel: {{fontSize: 11}}}},
    series,
    tooltip: {{trigger: 'axis'}}
  }});
}}

// 10. DART 매출 테이블 (§13)
function renderDart() {{
  const dart = RAW.dart || {{}};
  if (!Object.keys(dart).length) return;

  document.getElementById('dart-row').style.display = '';
  const sorted = Object.entries(dart).sort((a, b) => b[1].amount - a[1].amount);
  const rows = sorted.map(([brand, d]) => {{
    const amountB = Math.round(d.amount / 100_000_000).toLocaleString();
    const caution = d.caution ? ' <span style="color:#e65100;font-size:10px;">⚠</span>' : '';
    return `<tr>
      <td>${{brand}}${{caution}}</td>
      <td style="text-align:right;">${{amountB}}억원</td>
      <td>${{d.year}}년</td>
      <td style="color:#888;font-size:11px;">${{d.note || ''}}</td>
    </tr>`;
  }}).join('');
  document.getElementById('dart-table').innerHTML = `
    <table class="data-table">
      <thead><tr><th>브랜드</th><th>매출액</th><th>기준연도</th><th>비고</th></tr></thead>
      <tbody>${{rows}}</tbody>
    </table>`;
}}

// 11. AI 코멘터리
function renderCommentary() {{
  const text = RAW.commentary || '';
  const el = document.getElementById('insight-commentary');
  if (!text) {{
    el.innerHTML = '<div class="insight-item" style="color:#999;font-size:11px;">ANTHROPIC_API_KEY 설정 시 자동 생성</div>';
    return;
  }}
  // 마침표·느낌표 뒤 공백으로 문장 분리
  const sentences = text.split(/(?<=[.!?])\\s+/).filter(s => s.trim());
  el.innerHTML = sentences.map(s => `<div class="insight-item">${{s}}</div>`).join('');
}}

// 12. 인사이트 패널
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
  document.getElementById('insight-changes').innerHTML = changes.length
    ? changes.slice(0,5).map(c=>`
        <div class="insight-item ${{c.direction==='급등'?'good':'warn'}}">
          ${{c.brand}} · ${{c.period}}<br>
          <b>${{c.direction}} ${{c.pct_change > 0?'+':''}}${{c.pct_change}}%</b>
        </div>`).join('')
    : '<div class="insight-item">급등/급락 없음</div>';
}}

function setRange(btn, range) {{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
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
renderDart();
renderCommentary();
renderInsights();

window.addEventListener('resize', ()=>{{
  ['chart-google-rank','chart-naver-rank','chart-monthly','chart-datalab',
   'chart-sos','chart-gap','chart-gender','chart-age']
  .forEach(id=>{{const el=document.getElementById(id);if(el){{const inst=echarts.getInstanceByDom(el);if(inst)inst.resize();}}}});
}});
</script>
</body>
</html>"""
    return html
