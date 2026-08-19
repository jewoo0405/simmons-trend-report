import json
import os
from datetime import datetime, timedelta
from brand_config import BRANDS, TIER_LABELS, TIER_NEW, BRAND_TO_TIER_NEW, KEYWORD_GROUPS, KEYWORD_VERSION
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
    sos_category = data.get("sos_category", {})
    google = data.get("google", {})
    naver = data.get("naver", {})

    sos_val = round(sos.get("시몬스", 0), 1)
    # P1-1: 침대 전업 카테고리 기준 SoS
    sos_cat_raw = sos_category.get("시몬스")
    sos_cat_val = round(sos_cat_raw, 1) if sos_cat_raw is not None else None

    # 구글 순위: normalized 기준 (시몬스=100 보장)
    g_norm = google.get("normalized", {})
    sorted_g = sorted(g_norm.items(), key=lambda x: x[1], reverse=True)
    g_rank = next((i + 1 for i, (b, _) in enumerate(sorted_g) if b == "시몬스"), None)
    g_top = sorted_g[0] if sorted_g else ("—", 0)
    simmons_val = g_norm.get("시몬스", 100)
    gap_to_top = round(g_top[1] - simmons_val, 1) if g_top[0] != "시몬스" else 0.0

    # 침대 전업 내 순위 (시몬스, 에이스침대, 씰리침대, 지누스)
    from brand_config import BED_SPECIALISTS
    bed_norm = {b: v for b, v in g_norm.items() if b in BED_SPECIALISTS}
    sorted_bed = sorted(bed_norm.items(), key=lambda x: x[1], reverse=True)
    g_rank_bed = next((i + 1 for i, (b, _) in enumerate(sorted_bed) if b == "시몬스"), None)

    # 네이버 순위: normalized 정렬
    n_norm = naver.get("normalized", {})
    sorted_n = sorted(n_norm.items(), key=lambda x: x[1], reverse=True)
    n_rank = next((i + 1 for i, (b, _) in enumerate(sorted_n) if b == "시몬스"), None)

    return {
        "sos": sos_val,
        "sos_cat": sos_cat_val,
        "g_rank": g_rank,
        "g_rank_bed": g_rank_bed,
        "n_rank": n_rank,
        "g_top_brand": g_top[0],
        "gap_to_top": gap_to_top,
        "total_brands": len(sorted_g),
        "bed_brands": len(sorted_bed),
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

    # P1-1: SoS 카테고리 기준이 있으면 주(主) 지표로 표시, 전체 기준은 보조
    _sos_cat = kpi.get("sos_cat")
    _sos_display = f"{_sos_cat}%" if _sos_cat else f"{kpi['sos']}%"
    _sos_note = (
        f"침대 전업 기준 {_sos_cat}% · 전체 기준 {kpi['sos']}%"
        if _sos_cat else "브랜드별 구글 검색 점유율 합산 기준"
    )
    _g_rank_bed = kpi.get("g_rank_bed")
    _bed_brands = kpi.get("bed_brands", 4)
    _rank_display = (
        f"{kpi['g_rank']}위 / {total_brands}"
        if not _g_rank_bed
        else f"전체 {kpi['g_rank']}위 / {total_brands}"
    )
    _rank_note = (
        f"침대 전업 {_g_rank_bed}위 / {_bed_brands} · Google Trends 기준"
        if _g_rank_bed else "Google Trends 정규화 지수 기준"
    )
    cards = [
        ("📊", "SoS — 침대 전업", _sos_display, d("sos_cat", "%p") if _sos_cat else d("sos", "%p"),
         _sos_note),
        ("🔍", "구글 검색 순위", _rank_display,
         d("g_rank", "위"), _rank_note),
        ("🌐", "네이버 노출 순위", f"{kpi['n_rank']}위 / {total_brands}",
         d("n_rank", "위"), "블로그+뉴스 건수 기준"),
        ("📈", "1위 브랜드 대비 갭", f"-{kpi['gap_to_top']}pt" if kpi['gap_to_top'] > 0 else "1위",
         d("gap_to_top", "pt"), f"vs {kpi['g_top_brand']} (구글 지수 기준)"),
    ]

    items = ""
    for icon, title, val, delta, note in cards:
        items += f"""
      <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
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

    # P1-5: SoS 목표를 침대 전업 카테고리 기준으로 재설정
    sos_cat_val = kpi.get("sos_cat")
    if sos_cat_val is not None and sos_cat_val < 60:
        actions.append((
            f"침대 전업 카테고리 SoS 60% 목표 설정 (현재 {sos_cat_val}% · 보조: 전체 SoS {sos_val}% 유지)",
            '<a href="#section-sos">Share of Search</a>',
            "브랜드팀", "2027 Q1", "중간"
        ))
    elif sos_val < 10:
        actions.append((
            f"침대 전업 카테고리 SoS 60% 목표 설정 (현재 전체 기준 {sos_val}%)",
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
    """SoS vs SoM 산점도용 계산.
    P0-3: SoM 분모를 침대 전업(non-caution) 브랜드 매출 합계로 한정.
    P1-1: SoS는 카테고리 기준(sos_category) 우선 사용, 없으면 전체 기준(sos) 폴백.
    P1-3: 시몬스 포함 — DART 감사보고서 수동 입력값 사용.
          지누스 주의: 글로벌 매출 기준 → SoS(국내)와 지역 범위 불일치.
    """
    sos_cat = data.get("sos_category", {})
    sos_total = data.get("sos", {})
    dart = data.get("dart", {})

    # SoM 분모 = 침대 전업(non-caution) 브랜드 매출 합계 (시몬스 포함)
    total_sales = sum(d["amount"] for d in dart.values()
                      if d.get("amount") and not d.get("caution", True))

    # 시몬스는 sos_total에만 있고 sos_category에도 있어야 정상
    all_brands = set(sos_total) | set(dart)

    result = []
    for brand in all_brands:
        sos_val_cat = sos_cat.get(brand)   # None이면 비전업 or 데이터 없음
        sos_val_total = sos_total.get(brand, 0)
        # ESOV에 사용할 SoS: 카테고리 기준 우선
        sos_val = sos_val_cat if sos_val_cat is not None else sos_val_total

        brand_dart = dart.get(brand, {})
        caution = brand_dart.get("caution", True)
        tier = BRAND_TO_TIER_NEW.get(brand, "?")
        in_dart = brand in dart
        som_val = None

        # caution 브랜드는 SoM 미산출
        if not caution and in_dart and brand_dart.get("amount") and total_sales > 0:
            som_val = round(brand_dart["amount"] / total_sales * 100, 1)

        # 지누스 SoM 지역 불일치 경고
        zinus_note = "글로벌 매출 기준 — SoS(국내)와 지역 범위 불일치" if brand == "지누스" else None

        result.append({
            "brand": brand,
            "sos": round(sos_val, 1),
            "sos_total": round(sos_val_total, 1),
            "sos_cat": round(sos_val_cat, 1) if sos_val_cat is not None else None,
            "som": som_val,
            "caution": caution,
            "tier": tier,
            "in_dart": in_dart,
            "is_simmons": brand == "시몬스",
            "data_source": brand_dart.get("source"),
            "som_note": zinus_note,
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
    keyword_version = KEYWORD_VERSION  # 버전 문자열 로컬 바인딩 (f-string 에서 사용)
    # ① 키워드 그룹 정의 테이블 (v2 확장 포함)
    # v1 기준 초기 키워드 세트 — v2에서 추가된 항목 표시용
    _v1_keywords = {
        "시몬스":       {"시몬스", "시몬스침대", "시몬스 침대", "시몬스 매트리스", "SIMMONS", "뷰티레스트"},
        "에이스침대":   {"에이스침대", "에이스 침대", "에이스 매트리스", "ACE침대"},
        "씰리침대":     {"씰리침대", "씰리 침대", "씰리 매트리스", "SEALY"},
        "지누스":       {"지누스", "지누스 매트리스", "Zinus"},
        "코웨이 비렉스":{"코웨이 비렉스", "비렉스", "코웨이 매트리스"},
        "한샘":         {"한샘 침대", "한샘 매트리스"},
        "현대리바트":   {"현대리바트 침대", "리바트 침대", "리바트 매트리스"},
        "까사미아":     {"까사미아 침대", "까사미아 매트리스"},
        "일룸":         {"일룸 침대", "일룸 매트리스"},
        "에몬스":       {"에몬스", "에몬스 가구", "에몬스 침대"},
        "이케아":       {"이케아 침대", "이케아 매트리스"},
    }
    # 제외된 키워드 (동음이의 위험)
    _excluded = {
        "에이스침대": ["에이스 (단독) — 에이스 크래커·스포츠 용어·인명 등 동음이의 위험",
                      "ACE (단독) — ACE 억제제·학원명 등 노이즈 위험"],
        "한샘":       ["HANSEM — IT회사 한샘과 혼동 가능 (위험도 중간, 수집 후 노이즈 검토 필요)"],
    }

    kw_rows = ""
    for brand, kws in KEYWORD_GROUPS.items():
        forbidden_note = ""
        if brand == "한샘":
            forbidden_note = ' <span style="color:#e65100;font-size:10px;">※ \'한샘\' 단독 금지</span>'
        elif brand == "이케아":
            forbidden_note = ' <span style="color:#e65100;font-size:10px;">※ \'이케아\' 단독 금지</span>'
        weight = "bold" if brand == "시몬스" else "normal"

        v1_set = _v1_keywords.get(brand, set())
        kw_parts = []
        for kw in kws:
            if kw not in v1_set:
                kw_parts.append(f'<code style="background:#e8f5e9;color:#2e7d32;">{kw}</code>'
                                 f'<sup style="color:#2e7d32;font-size:9px;">신규(v2)</sup>')
            else:
                kw_parts.append(f'<code>{kw}</code>')
        kw_str = ' / '.join(kw_parts)

        exc = _excluded.get(brand, [])
        exc_str = ""
        if exc:
            exc_items = "".join(
                f'<div style="color:#e74c3c;font-size:10px;"><s>{e}</s> '
                f'<span style="color:#888;">(제외 — 동음이의 위험)</span></div>'
                for e in exc
            )
            exc_str = f'<div style="margin-top:4px;">{exc_items}</div>'

        kw_rows += f"""
        <tr>
          <td style="font-weight:{weight}">{brand}{forbidden_note}</td>
          <td>{kw_str}{exc_str}</td>
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
        </tr>
        <tr>
          <td>에이스침대</td>
          <td>단독어 제외</td>
          <td>'에이스' 단독 — 에이스 크래커·스포츠 용어·인명 등 동음이의 위험 높음. 'ACE' 단독 — ACE 억제제·학원명 등 노이즈 위험. 조합형(에이스침대·에이스 매트리스·ACE침대)만 허용.</td>
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
          <td>배치A→B: 시몬스 브리지, B→C: 시몬스 브리지, C→D: 에몬스 브리지, D→E: 씰리침대 브리지 (P0-2 체인 재설계)</td>
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
        </tr>
        <tr>
          <td>구글 vs 네이버 갭</td>
          <td style="font-family:monospace;">G_cat = G_지수 / avg(G전체) × 100<br>N_cat = N_지수 / avg(N전체) × 100<br>Gap = N_cat − G_cat</td>
          <td>11개 브랜드 카테고리 평균=100 기준 재정규화 후 차이 산출. 양수=네이버 강세, 음수=구글 강세. 시몬스도 의미 있는 갭 표시.</td>
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
        <div style="background:#f0f9ff;border-radius:6px;padding:12px;border-left:3px solid #0369a1;">
          <div style="font-weight:bold;font-size:12px;margin-bottom:6px;">Google Trends 배치 구성 (P0-2 재설계)</div>
          <div style="font-size:11px;color:#555;line-height:1.6;">
            배치A [시몬스·일룸·까사미아·에이스침대·지누스] max/min≈3x ✓<br>
            배치B [시몬스·이케아·한샘] max/min≈7x ✓<br>
            배치C [시몬스·에몬스] max/min≈7x ✓<br>
            배치D [에몬스·현대리바트·씰리침대] max/min≈4x ✓<br>
            배치E [씰리침대·코웨이 비렉스] max/min≈34x ⚠ 측정 해상도 한계 — P0-3 키워드 재검증 예정
          </div>
        </div>"""

    return f"""
  <!-- 부록 섹션 (T3-1) -->
  <div class="chart-row" id="section-appendix">
    <div class="card">
      <div class="card-title">부록 — 방법론 및 데이터 소스</div>
      <div class="card-sub">수집 기준 · 산출식 · 데이터 한계 공개 / 수집: {collected_at}</div>

      <!-- ① 키워드 그룹 정의 -->
      <div class="section-title" style="margin-top:16px;">① 키워드 그룹 정의 (Naver DataLab 수집 기준)</div>
      <h4 style="font-size:12px;font-weight:600;color:#555;margin-bottom:6px;">키워드 그룹 정의 (v{keyword_version})</h4>
      <p style="font-size:11px;color:#e67e22;margin-bottom:8px;">
        ⚠ 키워드 정의 변경됨 (2026-08-v2) — 다음 수집분부터 반영
      </p>
      <div style="margin-bottom:12px;font-size:11px;color:#666;">브랜드별 표기 변형을 통합한 키워드 그룹. 동일 그룹 내 키워드는 OR 조건으로 합산.
      <span style="color:#2e7d32;">■ 초록 배경 = 신규 추가 (v2)</span>&nbsp;&nbsp;
      <span style="color:#e74c3c;"><s>취소선</s> = 제외 (동음이의 위험)</span>
      </div>
      <table class="data-table" style="margin-bottom:20px;">
        <thead><tr>
          <th style="width:130px;">브랜드</th>
          <th>수집 키워드 / 제외 키워드</th>
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


def build_dashboard(data, report_month, collected_at, confidence_score,
                    is_partial_month=False, partial_day=None):
    colors = _brand_colors()
    data_json = json.dumps(data, ensure_ascii=False)
    colors_json = json.dumps(colors, ensure_ascii=False)
    brands_cfg_json = json.dumps(BRANDS, ensure_ascii=False)
    tier_labels_json = json.dumps({str(k): v for k, v in TIER_LABELS.items()}, ensure_ascii=False)
    tier_new_json = json.dumps(TIER_NEW, ensure_ascii=False)
    brand_to_tier_json = json.dumps(BRAND_TO_TIER_NEW, ensure_ascii=False)
    sos_som_data = _compute_sos_som(data)
    sos_som_json = json.dumps(sos_som_data, ensure_ascii=False)
    sos_category_json = json.dumps(data.get("sos_category", {}), ensure_ascii=False)
    _simmons_sos_total = round(data.get("sos", {}).get("시몬스", 0), 1)
    _simmons_sos_cat = round(data.get("sos_category", {}).get("시몬스") or 0, 1)
    _simmons_som_entry = next((d for d in sos_som_data if d["brand"] == "시몬스"), {})
    _simmons_som = _simmons_som_entry.get("som")
    simmons_sos_note = (
        f'시몬스 SoS: <strong>{_simmons_sos_cat}%</strong> (침대 전업 기준)'
        f' / {_simmons_sos_total}% (전체)'
        + (f' · SoM: <strong>{_simmons_som}%</strong> (DART 감사보고서)' if _simmons_som else ' · SoM 산출 불가')
    )
    sample_count = data.get('quality', {}).get('sample_count', 3)
    sample_count_label = f"{sample_count}회 수집"

    conf_color = "#2e7d32" if confidence_score >= 70 else "#e65100" if confidence_score >= 40 else "#c62828"
    conf_label = "안정" if confidence_score >= 70 else "주의" if confidence_score >= 40 else "불안정"

    # P0-1: 미완결 월 배너 HTML
    _partial_banner_html = ""
    if is_partial_month and partial_day:
        # 직전 완결 월 계산
        _rm_date = datetime.strptime(report_month, "%Y년 %m월")
        _prev_ym = (_rm_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        _partial_banner_html = (
            f'<div id="partial-month-banner" style="background:#fff3cd;border-bottom:2px solid #e6a817;'
            f'padding:8px 24px;font-size:12px;color:#856404;position:sticky;top:52px;z-index:100;">'
            f'⚠ {report_month}은 1~{partial_day}일 부분 집계 데이터입니다. '
            f'전월비 증감률 해석에 주의하십시오. '
            f'아래 &ldquo;변화점&rdquo; 섹션은 직전 완결 월({_prev_ym}) 기준으로 표시됩니다.'
            f'</div>'
        )
    _is_partial_js = "true" if is_partial_month else "false"

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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
/* ═══════════════════════════════════════════
   시몬스 브랜드 트렌드 대시보드 — UI v3
   Design: Modern Korean Business Dashboard
   ═══════════════════════════════════════════ */

:root {{
  --simmons:        #C8102E;
  --simmons-light:  #fff1f2;
  --primary:        #1e3a8a;
  --primary-mid:    #2563eb;
  --primary-light:  #eff6ff;
  --primary-border: #bfdbfe;
  --bg:             #f0f4f8;
  --surface:        #ffffff;
  --surface-2:      #f8fafc;
  --border:         #e2e8f0;
  --border-light:   #f1f5f9;
  --tx1:            #0f172a;
  --tx2:            #475569;
  --tx3:            #94a3b8;
  --green:          #15803d;
  --green-light:    #dcfce7;
  --orange:         #c2410c;
  --orange-light:   #fff7ed;
  --red:            #dc2626;
  --red-light:      #fee2e2;
  --kpi-1:          #2563eb;
  --kpi-2:          #7c3aed;
  --kpi-3:          #059669;
  --kpi-4:          #d97706;
  --header-h:       58px;
  --sidebar-w:      220px;
  --r-s:  6px;
  --r:    10px;
  --r-l:  14px;
  --shadow-s:  0 1px 2px rgba(15,23,42,.05);
  --shadow:    0 1px 3px rgba(15,23,42,.08), 0 4px 16px rgba(15,23,42,.04);
  --shadow-m:  0 4px 24px rgba(15,23,42,.10);
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Noto Sans KR', 'Malgun Gothic', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--tx1);
  min-width: 1280px;
  font-size: 13px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* ── 상단 헤더 ──────────────────────────────── */
#top-header {{
  position: sticky; top: 0; z-index: 200;
  height: var(--header-h);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  box-shadow: var(--shadow-s);
}}
.header-brand {{ display: flex; align-items: center; gap: 12px; }}
.header-logo {{
  width: 36px; height: 36px;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--simmons) 0%, #8b0d1f 100%);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 15px; font-weight: 800; flex-shrink: 0;
}}
.header-title-group {{ display: flex; flex-direction: column; gap: 1px; }}
.header-title {{ font-size: 15px; font-weight: 700; color: var(--tx1); letter-spacing: -.3px; }}
.header-sub {{ font-size: 11px; color: var(--tx3); }}
.header-right {{ display: flex; align-items: center; gap: 8px; }}
.header-chip {{
  display: inline-flex; align-items: center;
  height: 28px; padding: 0 12px;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 20px; font-size: 11px; color: var(--tx2); white-space: nowrap;
}}
.conf-badge {{
  display: inline-flex; align-items: center;
  height: 28px; padding: 0 12px;
  border-radius: 20px; font-size: 11px; font-weight: 600;
  background: {conf_color}; color: #fff;
}}

/* ── 레이아웃 ──────────────────────────────── */
#layout {{ display: flex; height: calc(100vh - var(--header-h)); overflow: hidden; }}

/* ── 사이드바 ──────────────────────────────── */
#sidebar {{
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  display: flex; flex-direction: column;
}}
#sidebar::-webkit-scrollbar {{ width: 4px; }}
#sidebar::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

.nav-section {{ padding: 14px 14px 12px; border-bottom: 1px solid var(--border-light); }}
.nav-section:last-child {{ border-bottom: none; }}

.nav-label {{
  font-size: 10px; font-weight: 700; color: var(--tx3);
  text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px;
}}

/* 기간 필터 pills */
.period-pills {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px; }}
.period-pill {{
  padding: 6px 2px;
  border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); font-size: 11px;
  font-family: inherit; color: var(--tx2);
  cursor: pointer; text-align: center; transition: all .15s;
}}
.period-pill:hover {{ background: var(--primary-light); border-color: var(--primary-mid); color: var(--primary-mid); }}
.period-pill.active {{ background: var(--primary-mid); border-color: var(--primary-mid); color: #fff; font-weight: 600; }}

/* 티어 필터 pills */
.tier-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
.tier-pill {{
  padding: 6px 4px;
  border: 1px solid var(--border); border-radius: var(--r-s);
  background: var(--surface); font-size: 11px;
  font-family: inherit; color: var(--tx2);
  cursor: pointer; text-align: center; transition: all .15s; white-space: nowrap;
}}
.tier-pill:hover {{ background: var(--primary-light); border-color: var(--primary-mid); color: var(--primary-mid); }}
.tier-pill.active {{ background: var(--primary-mid); border-color: var(--primary-mid); color: #fff; font-weight: 600; }}
.tier-pill[data-tier="ALL"] {{ grid-column: 1 / -1; }}
/* 하위 호환 */
.filter-btn {{ display: block; width: 100%; padding: 6px 10px; margin-bottom: 4px; border: 1px solid var(--border); border-radius: var(--r-s); background: var(--surface); font-size: 12px; font-family: inherit; cursor: pointer; text-align: left; transition: all .15s; color: var(--tx2); }}
.filter-btn:hover, .filter-btn.active {{ background: var(--primary-mid); color: #fff; border-color: var(--primary-mid); }}

/* 브랜드 리스트 */
.tier-header {{ font-size: 9px; color: var(--tx3); font-weight: 700; letter-spacing: 0.5px; padding: 8px 8px 3px; text-transform: uppercase; }}
.brand-item {{
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: var(--r-s);
  cursor: pointer; font-size: 12px; color: var(--tx2); transition: background .12s;
}}
.brand-item:hover {{ background: var(--surface-2); }}
.brand-item.active {{ background: var(--primary-light); color: var(--primary-mid); font-weight: 600; }}
.brand-item--baseline {{
  background: var(--simmons-light); border: 1px solid #fca5a5;
  border-radius: var(--r-s); margin-bottom: 6px;
}}
.brand-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.baseline-badge {{
  margin-left: auto; font-size: 9px; font-weight: 700;
  background: var(--simmons); color: #fff;
  padding: 1px 5px; border-radius: 3px;
}}

/* 사이드바 액션 버튼 */
.action-btn {{
  display: block; width: 100%; padding: 7px 12px; margin-bottom: 5px;
  border: 1px solid var(--border); border-radius: var(--r-s);
  background: var(--surface); font-size: 12px; font-family: inherit;
  color: var(--tx2); cursor: pointer; text-align: left; transition: all .15s;
}}
.action-btn:hover {{ background: var(--primary-light); border-color: var(--primary-mid); color: var(--primary-mid); }}

/* ── 메인 콘텐츠 ──────────────────────────── */
#main {{
  flex: 1; overflow-y: auto;
  padding: 20px 24px;
  display: flex; flex-direction: column; gap: 20px;
}}
#main::-webkit-scrollbar {{ width: 6px; }}
#main::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

/* ── KPI 스트립 ──────────────────────────── */
.kpi-strip {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }}
.kpi-card {{
  background: var(--surface);
  border-radius: var(--r);
  border: 1px solid var(--border);
  padding: 16px 18px;
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
  transition: box-shadow .2s, transform .2s;
}}
.kpi-card:hover {{ box-shadow: var(--shadow-m); transform: translateY(-1px); }}
.kpi-card::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 3px; border-radius: var(--r) var(--r) 0 0;
}}
.kpi-card:nth-child(1)::before {{ background: var(--kpi-1); }}
.kpi-card:nth-child(2)::before {{ background: var(--kpi-2); }}
.kpi-card:nth-child(3)::before {{ background: var(--kpi-3); }}
.kpi-card:nth-child(4)::before {{ background: var(--kpi-4); }}
.kpi-icon {{
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; margin-bottom: 10px; flex-shrink: 0;
}}
.kpi-card:nth-child(1) .kpi-icon {{ background: #dbeafe; }}
.kpi-card:nth-child(2) .kpi-icon {{ background: #ede9fe; }}
.kpi-card:nth-child(3) .kpi-icon {{ background: #d1fae5; }}
.kpi-card:nth-child(4) .kpi-icon {{ background: #fef3c7; }}
.kpi-label {{ font-size: 11px; color: var(--tx3); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.kpi-value {{ font-size: 26px; font-weight: 700; color: var(--tx1); letter-spacing: -.5px; margin-bottom: 5px; line-height: 1.2; }}
.kpi-delta {{ font-size: 12px; margin-bottom: 4px; font-weight: 500; }}
.kpi-note {{ font-size: 10px; color: var(--tx3); line-height: 1.4; }}

/* ── 섹션 구분선 ──────────────────────────── */
.section-divider {{
  display: flex; align-items: center; gap: 12px;
  color: var(--tx3); font-size: 10px; font-weight: 700;
  letter-spacing: 1.2px; text-transform: uppercase;
}}
.section-divider::before, .section-divider::after {{
  content: ''; flex: 1; height: 1px; background: var(--border);
}}

/* ── 요약 그리드 ──────────────────────────── */
.summary-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 16px; }}
.summary-col {{ display: flex; flex-direction: column; gap: 12px; }}

/* ── 인사이트 ──────────────────────────────── */
.insight-item {{
  padding: 10px 12px;
  border-radius: var(--r-s);
  background: var(--surface-2);
  border: 1px solid var(--border-light);
  margin-bottom: 8px; font-size: 12px; line-height: 1.6;
}}
.insight-item.warn {{ background: var(--orange-light); border-left: 3px solid var(--orange); }}
.insight-item.good {{ background: var(--green-light); border-left: 3px solid var(--green); }}

/* ── 섹션 타이틀 ──────────────────────────── */
.section-title {{
  font-size: 13px; font-weight: 700; color: var(--tx1);
  border-left: 3px solid var(--primary-mid);
  padding-left: 10px; margin-bottom: 12px;
}}

/* ── 차트 그리드 / 카드 ───────────────────── */
.chart-row {{ display: grid; gap: 16px; }}
.chart-row.col2 {{ grid-template-columns: 1fr 1fr; }}
.chart-row.col3 {{ grid-template-columns: 1fr 1fr 1fr; }}
.card {{
  background: var(--surface);
  border-radius: var(--r);
  border: 1px solid var(--border);
  padding: 18px 20px;
  box-shadow: var(--shadow);
  height: auto !important; overflow: visible;
  transition: box-shadow .2s;
}}
.card:hover {{ box-shadow: var(--shadow-m); }}
.card-title {{
  font-size: 14px; font-weight: 700; color: var(--tx1);
  margin-bottom: 3px;
  display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
}}
.card-sub {{ font-size: 11px; color: var(--tx3); margin-bottom: 14px; line-height: 1.5; }}

/* ── 뱃지 ──────────────────────────────────── */
.source-badge {{
  display: inline-flex; align-items: center;
  height: 18px; padding: 0 7px;
  border-radius: 4px; font-size: 10px; font-weight: 600;
}}
.badge-google {{ background: #dcfce7; color: #15803d; }}
.badge-naver {{ background: #dbeafe; color: #1d4ed8; }}
.badge-no-demo {{ background: var(--orange-light); color: var(--orange); }}

/* ── CV 신뢰도 ──────────────────────────────── */
.cv-stable {{ color: var(--green); font-weight: 600; }}
.cv-warning {{ color: var(--orange); font-weight: 600; }}
.cv-unstable {{ color: var(--red); font-weight: 600; }}
.cv-na {{ color: var(--tx3); font-style: italic; }}

/* ── 데이터 테이블 ──────────────────────────── */
.data-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.data-table th {{
  background: #1e293b; color: #fff;
  padding: 8px 12px; text-align: left;
  font-size: 11px; font-weight: 600; letter-spacing: 0.3px;
}}
.data-table th:first-child {{ border-radius: var(--r-s) 0 0 0; }}
.data-table th:last-child {{ border-radius: 0 var(--r-s) 0 0; }}
.data-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border-light); }}
.data-table tr:last-child td {{ border-bottom: none; }}
.data-table tr:hover td {{ background: var(--surface-2); }}
.data-table tr:nth-child(even) td {{ background: #fafbfc; }}
.simmons-sticky td {{
  background: var(--simmons-light) !important;
  font-weight: 700; position: sticky; top: 0; z-index: 1;
}}

/* ── 없음 상태 ──────────────────────────────── */
.no-data {{ text-align: center; padding: 40px; color: var(--tx3); font-size: 13px; }}

/* ── 인구통계 토글 ──────────────────────────── */
.demo-toggle {{
  padding: 5px 12px;
  border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); font-size: 11px;
  font-family: inherit; cursor: pointer; color: var(--tx2); transition: all .15s;
}}
.demo-toggle:hover {{ background: var(--primary-light); border-color: var(--primary-mid); color: var(--primary-mid); }}
.demo-toggle.active {{ background: var(--primary-mid); border-color: var(--primary-mid); color: #fff; }}

/* ── 캡션 ──────────────────────────────────── */
.chart-caption {{
  font-size: 11px; color: var(--tx3);
  margin-top: 12px; padding: 8px 10px;
  background: var(--surface-2);
  border-radius: var(--r-s); border: 1px solid var(--border-light);
  line-height: 1.7; word-break: keep-all;
  overflow: visible; position: static;
}}
.chart-caption .cap-formula {{ font-style: italic; }}
.chart-caption .cap-drill {{
  color: var(--primary-mid); cursor: pointer;
  text-decoration: underline; font-size: 10px; margin-left: 6px;
}}
.cap-note {{ display: block; margin-top: 4px; color: #92400e; }}
.drill-detail {{
  display: none;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--r-s); padding: 8px 10px;
  margin-top: 4px; font-size: 11px; line-height: 1.8; font-family: monospace;
}}

/* ── 부록 테이블 ──────────────────────────── */
.appendix-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 12px; }}
.appendix-table th {{ background: #1e293b; color: #fff; padding: 8px; text-align: left; }}
.appendix-table td {{ padding: 7px 8px; border-bottom: 1px solid var(--border-light); vertical-align: top; }}
.appendix-table tr:nth-child(even) td {{ background: var(--surface-2); }}

/* ── 수집기간 칩 ────────────────────────────── */
.period-chip {{
  display: inline-flex; align-items: center;
  height: 16px; padding: 0 6px;
  background: #f1f5f9; border: 1px solid #e2e8f0;
  border-radius: 10px; font-size: 10px; color: #64748b;
  white-space: nowrap; font-weight: 500; margin-left: 6px;
  vertical-align: middle;
}}

/* ── 소스 뱃지 ──────────────────────────────── */
.src-badge {{ display: inline-block; font-size: 9px; font-weight: 700; padding: 1px 4px; border-radius: 3px; margin-left: 3px; vertical-align: middle; }}
.src-badge.gt {{ background: #4285f4; color: #fff; }}
.src-badge.ns {{ background: #03c75a; color: #fff; }}
.src-badge.nd {{ background: #0ea5e9; color: #fff; }}
.src-badge.dt {{ background: #e53e3e; color: #fff; }}

/* ── 순위 테이블 ──────────────────────────── */
.rank-detail-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
.rank-detail-table th {{ background: var(--surface-2); padding: 5px 8px; text-align: left; border-bottom: 2px solid var(--border); font-size: 10px; color: var(--tx3); font-weight: 600; }}
.rank-detail-table td {{ padding: 5px 8px; border-bottom: 1px solid var(--border-light); }}
.rank-detail-table .simmons-row td {{ background: var(--simmons-light); font-weight: 600; }}
.formula-text {{ font-family: monospace; font-size: 10px; }}

/* ── 필터 변경 배너 ──────────────────────────── */
#filter-changed-banner {{
  background: var(--orange-light); border-bottom: 2px solid #ea580c;
  padding: 6px 24px; font-size: 12px; color: #c2410c;
  position: sticky; top: var(--header-h); z-index: 99;
}}

/* ── 표지 ──────────────────────────────────── */
.print-only {{ display: none; }}
.cover-inner {{
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100vh; text-align: center; gap: 20px;
}}
.cover-confidential {{
  color: var(--red); font-weight: 700; font-size: 14px;
  border: 2px solid var(--red); padding: 4px 16px; border-radius: var(--r-s);
}}
.cover-title {{ font-size: 32px; font-weight: 800; color: var(--tx1); }}
.cover-month {{ font-size: 22px; color: var(--tx2); font-weight: 600; }}
.cover-meta {{ font-size: 13px; color: var(--tx2); line-height: 1.8; margin-top: 20px; }}

/* ── 인쇄 ──────────────────────────────────── */

/* 배경색·이미지 강제 출력 (크롬/사파리/파이어폭스) */
* {{
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  color-adjust: exact !important;
}}

@media print {{
  /* 배경색 강제 출력 */
  * {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }}

  .print-only {{ display: block !important; }}
  #cover-page {{ page-break-after: always; }}
  .no-print, #filter-banner, .tier-filter, .toggle-btn, button, .action-btn {{ display: none !important; }}
  .chart-block, .kpi-strip, table, .section-card {{ page-break-inside: avoid; }}
  h2, h3 {{ page-break-after: avoid; }}
  @page {{ margin: 15mm 12mm; size: A4 landscape; }}
  a[href]::after {{ content: none; }}
  #sidebar {{ display: none !important; }}
  #top-header {{ display: none !important; }}
  #filter-changed-banner {{ display: none !important; }}
  #layout {{ height: auto; display: block !important; }}
  #main {{
    overflow: visible !important;
    padding: 0 !important;
    width: 100% !important;
    margin-left: 0 !important;
    height: auto !important;
    display: block !important;
  }}
  body {{ font-size: 10pt; background: #fff !important; }}
  .card {{
    break-inside: avoid;
    box-shadow: none !important;
    border: 1px solid #ddd !important;
    background: #fff !important;
  }}
  .chart-row {{ break-inside: avoid; }}
  h2 {{ break-after: avoid; }}
  .detail-cell {{ display: table-cell !important; }}

  /* 히트맵·KPI·갭 등 배경색 셀 강제 출력 */
  td, th, div, span {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  /* ECharts 캔버스 크기 유지 */
  canvas {{ max-width: 100% !important; }}

  /* 섹션 간 여백 */
  .chart-row {{ margin-bottom: 12px !important; }}
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
{_partial_banner_html}

<!-- 상단 헤더 -->
<div id="top-header">
  <div class="header-brand">
    <div class="header-logo">S</div>
    <div class="header-title-group">
      <div class="header-title">시몬스 브랜드 트렌드 대시보드</div>
      <div class="header-sub">{report_month} · 월간 리포트</div>
    </div>
  </div>
  <div class="header-right">
    <span class="header-chip">수집 {collected_at}</span>
    <span class="header-chip">11개 브랜드</span>
    <span class="conf-badge">{conf_label} {confidence_score}점</span>
  </div>
</div>

<div id="layout">

<!-- 좌측 사이드바 -->
<nav id="sidebar">

  <div class="nav-section">
    <div class="nav-label">티어 필터</div>
    <div class="tier-grid">
      <button class="tier-pill active tier-filter" data-tier="ALL" onclick="setTierFilter(this,'ALL')">전체</button>
      <button class="tier-pill tier-filter" data-tier="A" onclick="setTierFilter(this,'A')">Tier A</button>
      <button class="tier-pill tier-filter" data-tier="B" onclick="setTierFilter(this,'B')">Tier B</button>
      <button class="tier-pill tier-filter" data-tier="C" onclick="setTierFilter(this,'C')">Tier C</button>
      <button class="tier-pill tier-filter" data-tier="D" onclick="setTierFilter(this,'D')">Tier D</button>
    </div>
  </div>

  <div class="nav-section">
    <div class="nav-label">브랜드 목록</div>
    <div id="brand-list"></div>
  </div>

  <div class="nav-section">
    <div class="nav-label">내보내기</div>
    <button class="action-btn" onclick="exportCSV()">↓ CSV 다운로드</button>
    <button class="action-btn" onclick="exportPrint()">⎙ 인쇄 / PDF</button>
  </div>

</nav>

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
      <div class="section-title" id="section-changes-title">이번 달 변화점</div>
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
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub">브랜드별 구글 검색 점유율 (%) · SoS = 브랜드 지수 ÷ 전체 합계 × 100</div>
      <div id="chart-sos" style="height:280px;"></div>
      <div id="sos-table"></div>
    </div>
    <div class="card" id="section-gap">
      <div class="card-title">구글 vs 네이버 갭 분석
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub">브랜드 카테고리 평균=100 기준 재정규화 후 네이버 지수 − 구글 지수 (양수=네이버 강세 / 음수=구글 강세)</div>
      <div id="chart-gap" style="height:320px;"></div>
    </div>
  </div>

  <!-- ⑥ 구글 순위 + 네이버 콘텐츠 노출량 (T1-4 라벨 변경) -->
  <div class="chart-row col2" id="section-rank">
    <div class="card">
      <div class="card-title">구글 검색 지수 순위
        <span class="source-badge badge-google">Google Trends</span>
        <span class="source-badge" style="background:#fff3e0;color:#e65100;" title="Tier C(종합가구)·D(렌탈) 브랜드는 가구·렌탈 수요 혼재로 직접 비교 주의">⚠ Tier C·D 비교 주의</span>
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub" id="sub-google-rank">시몬스=100 기준 · 최근 3개월 한국</div>
      <div id="chart-google-rank" style="min-height:200px;"></div>
      <!-- 이케아 별도 패널 -->
      <div style="margin-top:16px;">
        <p style="font-size:12px;font-weight:600;color:#6c3483;margin-bottom:6px;">
          &#9646; 이케아 별도 표기 (Tier C &#8212; 종합가구, 스케일 분리)
        </p>
        <div id="chart-google-rank-ikea" style="min-height:80px;"></div>
      </div>
    </div>
    <div class="card" id="section-naver-rank">
      <div class="card-title">네이버 콘텐츠 노출량
        <span class="source-badge badge-naver">Naver Search</span>
        <span class="source-badge" style="background:#fff3e0;color:#e65100;" title="Tier C(종합가구)·D(렌탈) 브랜드는 가구·렌탈 수요 혼재로 직접 비교 주의">⚠ Tier C·D 비교 주의</span>
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub" id="sub-naver-rank">시몬스=100 기준 · 블로그+뉴스 건수 · 최근 3개월</div>
      <div id="chart-naver-rank" style="min-height:200px;"></div>
    </div>
  </div>

  <!-- ⑦ 월별 추이 -->
  <div class="chart-row" id="section-trend">
    <div class="card">
      <div class="card-title">월별 검색 트렌드 추이
        <span class="source-badge badge-google">Google Trends</span>
        <span class="period-chip">최근 12개월</span>
      </div>
      <div class="card-sub">주요 브랜드 · 음영은 신뢰구간(CV) · 출처: Google Trends · 기준: 시몬스=100</div>
      <div id="chart-monthly" style="height:420px;"></div>
      <div id="monthly-heatmap"></div>
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
        <span class="period-chip">최근 1개월</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <button class="demo-toggle active" id="gender-toggle-norm" onclick="setGenderMode('norm')">브랜드 내 비율</button>
        <button class="demo-toggle" id="gender-toggle-idx" onclick="setGenderMode('idx')">카테고리 인덱스</button>
      </div>
      <div class="card-sub" id="gender-sub">브랜드별 성별 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-gender" style="height:320px;"></div>
    </div>
    <div class="card">
      <div class="card-title">연령대별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
        <span class="period-chip">최근 1개월</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:8px;">
        <button class="demo-toggle active" id="age-toggle-norm" onclick="setAgeMode('norm')">브랜드 내 비율</button>
        <button class="demo-toggle" id="age-toggle-idx" onclick="setAgeMode('idx')">카테고리 인덱스</button>
      </div>
      <div class="card-sub" id="age-sub">브랜드별 연령대 비율 (브랜드 내 합계=100%)</div>
      <div id="chart-age" style="height:320px;"></div>
    </div>
  </div>

  <!-- T2-3: SoS vs SoM 산점도 -->
  <div class="chart-row" id="section-sos-som" style="display:none;">
    <div class="card">
      <div style="display:flex;align-items:flex-start;gap:16px;margin-bottom:4px;">
        <div style="flex:1;min-width:0;">
          <div class="card-title">Share of Search vs Share of Market (ESOV 분석)</div>
          <div class="card-sub">● 실선 원형: 침대 전업 브랜드 (지누스·에이스침대) &nbsp;|&nbsp; △ 삼각형: 침대 외 사업 포함 — 전체 매출 기준 (참고용)</div>
          <div style="display:inline-block;margin:8px 0 0;padding:7px 14px;background:#fff3f3;border:1px solid #f5c6c6;border-radius:6px;font-size:12px;color:#c0392b;line-height:1.6;">
            ⚑ {simmons_sos_note}
          </div>
          <div style="margin-top:6px;font-size:10px;color:#aaa;">※ 비상장 업체(시몬스·씰리침대·까사미아·일룸·에몬스·코웨이 비렉스 매출 분리분)는 DART 공시 없음 — SoM 산출 불가</div>
        </div>
        <div style="flex:0 0 730px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:11px 14px;font-size:11px;color:#475569;line-height:1.75;">
          <div style="font-weight:700;color:#1e3a8a;margin-bottom:6px;font-size:11px;">📌 지표 해석 가이드</div>
          <div style="margin-bottom:5px;">
            <span style="font-weight:700;color:#334155;">SoS</span> — 비교군 전체 검색량 중 해당 브랜드 비중.
            Google Trends 지수를 시몬스=100으로 정규화해 산출.
          </div>
          <div style="margin-bottom:5px;">
            <span style="font-weight:700;color:#334155;">SoM</span> — DART 공시 매출 기준 점유율.
            분모는 수집된 브랜드 매출 합계. 코웨이(전체 사업) 포함 시 SoM 53% 차지 → 나머지 브랜드 수치 하향 왜곡.
          </div>
          <div style="padding-top:6px;border-top:1px solid #e2e8f0;color:#64748b;">
            <span style="font-weight:700;">대각선 (y=x)</span> — SoS=SoM 기준선.
            <span style="color:#2563eb;">위쪽</span> = 매출 대비 검색 적음 (검색 투자 여력).
            <span style="color:#dc2626;">아래쪽</span> = 검색 대비 매출 적음 (전환 효율 점검 필요).
          </div>
        </div>
      </div>
      <div id="chart-sos-som" style="height:400px;margin-top:12px;"></div>
      <div id="sos-som-caution-ref"></div>
      <div style="font-size:10px;color:#999;margin-top:8px;padding-top:8px;border-top:1px solid #f0f0f0;">
        ※ SoM = DART 공시 매출 기준, 침대 전업 브랜드 합산. 복합 사업 브랜드(한샘·현대리바트·코웨이비렉스)는 전사 매출 혼재로 SoM 제외.
      </div>
      {_caption("Google Trends + 네이버 증권", collected_at)}
    </div>
  </div>

  <!-- ⑩ 부록: 데이터 신뢰도 상세 (CV 분석) -->
  <div class="chart-row" id="section-cv">
    <div class="card">
      <div class="card-title">지표 변동성 (CV 분석)</div>
      <div class="card-sub">CV≤0.05 안정(녹) · CV≤0.15 주의(주황) · CV&gt;0.15 불안정(빨강)
        · 출처: Google Trends 월별 지수 · 기준: 최근 12개월 monthly_series 기반 변동계수
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
// canvas 인스턴스 재사용 (매번 생성 비용 방지)
const _measureCtx = (function() {{
  try {{
    const c = document.createElement('canvas');
    const ctx = c.getContext('2d');
    ctx.font = '12px "Noto Sans KR", "Malgun Gothic", sans-serif';
    return ctx;
  }} catch(e) {{ return null; }}
}})();

function measureTextWidth(text) {{
  if (_measureCtx) {{
    return _measureCtx.measureText(String(text)).width;
  }}
  // fallback: 한글은 약 13px, ASCII는 약 7px
  return Array.from(String(text)).reduce((w, ch) => {{
    return w + (ch.charCodeAt(0) > 127 ? 13 : 7);
  }}, 0);
}}

function leftMargin(labels) {{
  const maxW = Math.max(...labels.map(l => measureTextWidth(String(l))));
  return Math.ceil(maxW) + 16;  // 눈금 여백 8px + 여유 8px
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
  const parts = [];
  if (opts.formula)   parts.push(`<span class="cap-formula">산출식: ${{opts.formula}}</span>`);
  if (opts.source)    parts.push(`출처: ${{opts.source}}`);
  if (opts.collected) parts.push(`수집: ${{opts.collected}}`);
  if (opts.n)         parts.push(`n=${{opts.n}}`);

  let html = `<div class="chart-caption">${{parts.join(' · ')}}`;
  if (opts.note) html += `<br><span class="cap-note">⚠ ${{opts.note}}</span>`;
  if (opts.drillId && opts.drillContent) {{
    html += `<span class="cap-drill" onclick="toggleDrill('${{opts.drillId}}')"> 계산 내역 ▾</span>
             <div id="${{opts.drillId}}" class="drill-detail">${{opts.drillContent}}</div>`;
  }}
  html += `</div>`;
  return html;
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
const SOS_CATEGORY = {sos_category_json};
const IS_PARTIAL_MONTH = {_is_partial_js};

// 현재 티어 필터 상태
let _activeTier = 'ALL';
// 현재 기간 필터 상태 ('3M' | '6M' | '12M' | 'ALL')
let _activePeriod = '6M';

// dispose 후 재초기화 헬퍼
function reInitChart(domId) {{
  const dom = document.getElementById(domId);
  if (!dom) return null;
  const existing = echarts.getInstanceByDom(dom);
  if (existing) existing.dispose();
  return dom;
}}

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

// 차트 초기화 — 인스턴스 전역 추적 (인쇄 시 리사이즈용)
window._chartInstances = window._chartInstances || [];
const gc = (id) => {{
  const dom = document.getElementById(id);
  if (!dom) return null;
  const existing = echarts.getInstanceByDom(dom);
  if (existing) existing.dispose();
  const inst = echarts.init(dom);
  window._chartInstances.push(inst);
  return inst;
}};

// B-4: 겹침 검증 루틴 (window.__devMode = true 로 활성화)
function checkOverlap(chartDom, label) {{
  if (!window.__devMode) return;
  const cardEl = chartDom.closest('.card');
  const cardRect = cardEl ? cardEl.getBoundingClientRect() : null;

  // 1) 카드 밖으로 나간 요소
  if (cardRect) {{
    chartDom.querySelectorAll('.chart-caption, text').forEach(el => {{
      const r = el.getBoundingClientRect();
      if (r.bottom > cardRect.bottom + 2)
        console.warn(`[카드 하단 넘침] ${{label}}: ${{el.className || el.tagName}}`);
      if (r.left < cardRect.left - 2)
        console.warn(`[카드 좌측 넘침] ${{label}}: ${{el.className || el.tagName}}`);
    }});
  }}

  // 2) 동일 텍스트 중복 검출
  if (cardEl) {{
    const texts = {{}};
    cardEl.querySelectorAll('.chart-caption').forEach(el => {{
      const t = el.innerText.slice(0, 30);
      texts[t] = (texts[t] || 0) + 1;
      if (texts[t] > 1) console.warn(`[캡션 중복] ${{label}}: "${{t}}..."`);
    }});
  }}

  // 3) 기존 bounding box 교차 검사
  const rects = [];
  chartDom.querySelectorAll('.chart-caption').forEach(el => {{
    rects.push({{ el, r: el.getBoundingClientRect(), name: 'caption' }});
  }});
  for (let i = 0; i < rects.length; i++) {{
    for (let j = i + 1; j < rects.length; j++) {{
      const a = rects[i].r, b = rects[j].r;
      if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top)
        console.warn(`[겹침] ${{label}}: caption ↔ caption`);
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
  renderRankCharts();
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

// renderGoogleRank() 와 renderNaverRank() 를 모두 호출하는 공통 진입점
function renderRankCharts() {{
  const gNorm = RAW.google?.normalized || {{}};
  const nNorm = RAW.naver?.normalized || {{}};
  const allBrands = Array.from(new Set([...Object.keys(gNorm), ...Object.keys(nNorm)]));
  const sharedLeft = leftMargin(allBrands);
  renderGoogleRank(sharedLeft);
  renderNaverRank(sharedLeft);
}}

// 1. 구글 순위 바차트 (이케아 별도 패널 분리)
function renderGoogleRank(sharedLeft) {{
  const norm = RAW.google?.normalized || {{}};
  if (!Object.keys(norm).length) return;

  // 이케아 키 탐색
  const IKEA_KEY = Object.keys(norm).find(k => k.includes('이케아') || k.includes('IKEA')) || null;

  // 티어 필터 적용 후 이케아 제외
  let allEntries = Object.entries(norm);
  allEntries = _filterByTier(allEntries);
  const mainEntries = allEntries
    .filter(([b]) => b !== IKEA_KEY)
    .sort(([,a],[,b]) => a - b);  // 오름차순 (ECharts 가로막대: 아래→위)

  const ikeaVal = IKEA_KEY ? norm[IKEA_KEY] : null;
  const simonVal = norm['시몬스'] || 100;

  // ── 메인 차트 (이케아 제외) ──────────────────────────
  const mainDomRaw = reInitChart('chart-google-rank');
  const mainDom = mainDomRaw || document.getElementById('chart-google-rank');
  if (mainDom && mainEntries.length) {{
    const brands = mainEntries.map(([b]) => b);
    const vals   = mainEntries.map(([,v]) => v);
    const dataMax = Math.max(...vals);

    const h = calcBarChartHeight(brands.length);
    mainDom.style.height = h + 'px';
    const mainChart = echarts.init(mainDom);

    const lm = sharedLeft !== undefined ? sharedLeft : leftMargin(brands);
    mainChart.setOption({{
      grid: {{ left: lm, right: 110, top: TOP_PAD, bottom: AXIS_AREA, containLabel: false }},
      xAxis: axisOption(dataMax, '', 5),
      yAxis: {{
        type: 'category',
        data: brands,
        axisLabel: {{
          fontSize: 12,
          margin: 8,
          formatter: b => b === '시몬스' ? '{{highlight|' + b + '}}' : b,
          rich: {{ highlight: {{ fontWeight: 'bold', color: '#e53935' }} }}
        }},
        axisTick: {{ alignWithLabel: true }},
        boundaryGap: true
      }},
      series: [{{
        type: 'bar',
        barMaxWidth: BAR_HEIGHT,
        data: brands.map((b, i) => ({{
          value: vals[i],
          itemStyle: {{
            color: b === '시몬스' ? '#e53935' : (COLORS[b] || '#3498db'),
            opacity: b === '시몬스' ? 1 : ((BRAND_TO_TIER[b] === 'C' || BRAND_TO_TIER[b] === 'D') ? 0.45 : 0.75),
            borderColor: b === '시몬스' ? '#c8a96e' : 'transparent',
            borderWidth: b === '시몬스' ? 2 : 0
          }}
        }})),
        label: {{ show: true, position: 'right', fontSize: 11,
                  formatter: p => typeof p.value === 'number' ? p.value.toFixed(1) : p.value }}
      }}],
      tooltip: {{
        trigger: 'axis',
        axisPointer: {{ type: 'shadow' }},
        confine: true,
        position: function(point, params, dom, rect, size) {{
          const tooltipW = size.contentSize[0];
          const chartW   = size.viewSize[0];
          const x = rect.x + rect.width + 8;
          return [x + tooltipW > chartW ? rect.x - tooltipW - 8 : x, rect.y];
        }},
        backgroundColor: '#ffffff',
        borderColor: '#cccccc',
        borderWidth: 1,
        textStyle: {{ color: '#333', fontSize: 12 }},
        extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15); pointer-events:none;',
        formatter: p => {{
          const t = BRAND_TO_TIER[p[0].name] || '?';
          return `${{p[0].name}} [Tier ${{t}}]<br>${{p[0].value}} (시몬스=100)`;
        }}
      }}
    }});
    mainChart.resize();
    // C: 구글 순위 상세 테이블 삽입
    const sortedForTable = mainEntries.slice().reverse(); // 내림차순 (높은 순위 먼저)
    const tableItems = sortedForTable.map((entry, i) => ({{
      brand: entry[0], value: entry[1], rank: i + 1
    }}));
    const tableHtml = renderGoogleRankTable(tableItems, sharedLeft);
    const existingTable = mainDom.nextElementSibling;
    if (existingTable && existingTable.classList.contains('rank-table-wrap')) {{
      existingTable.remove();
    }}
    mainDom.insertAdjacentHTML('afterend', tableHtml);
    setTimeout(() => checkOverlap(mainDom, 'GoogleRank'), 300);
  }}

  // ── 이케아 별도 패널 ─────────────────────────────────
  const ikeaDomRaw = reInitChart('chart-google-rank-ikea');
  const ikeaDom = ikeaDomRaw || document.getElementById('chart-google-rank-ikea');
  if (!ikeaDom || !IKEA_KEY || !ikeaVal) return;

  ikeaDom.style.height = '100px';
  const ikeaChart = echarts.init(ikeaDom);

  ikeaChart.setOption({{
    grid: {{ left: sharedLeft !== undefined ? sharedLeft : leftMargin(['이케아', '시몬스(기준)']), right: 110, top: 8, bottom: 30, containLabel: false }},
    xAxis: {{ type: 'value', min: 0, max: Math.ceil(ikeaVal * 1.1 / 100) * 100,
              axisLabel: {{ fontSize: 11 }} }},
    yAxis: {{ type: 'category', data: ['시몬스(기준)', IKEA_KEY],
              axisLabel: {{ fontSize: 11 }}, boundaryGap: true }},
    series: [{{
      type: 'bar',
      data: [
        {{ value: simonVal, itemStyle: {{ color: '#e53935' }} }},
        {{ value: ikeaVal,  itemStyle: {{ color: '#9b59b6' }} }}
      ],
      barMaxWidth: 22,
      label: {{ show: true, position: 'right', fontSize: 11,
                formatter: p => typeof p.value === 'number' ? p.value.toFixed(1) : p.value }}
    }}],
    tooltip: {{ trigger: 'axis', formatter: p =>
      `${{p[0].name}}<br>${{p[0].value.toFixed(1)}} (시몬스=100)` }}
  }});
}}

// C: 구글 순위 상세 데이터 테이블
function renderGoogleRankTable(items, sharedLeft) {{
  const simonVal = RAW.google?.normalized?.['시몬스'] || 100;

  const rows = items.map(item => {{
    const rawVal = RAW.google?.linked?.[item.brand] ?? item.value;
    const formula = `${{item.value.toFixed(1)}} = ${{rawVal.toFixed(1)}} ÷ ${{simonVal.toFixed(1)}} × 100`;
    const badge = `<span class="src-badge gt">GT</span>`;
    const isSim = item.brand === '시몬스';
    const isLowRes = rawVal < 1.0 && !isSim;
    const lowResNote = isLowRes ? `<span style="font-size:9px;color:#b45309;margin-left:4px;">※ 측정 해상도 한계</span>` : '';
    const displayVal = isLowRes ? item.value.toFixed(0) : item.value.toFixed(1);
    return `<tr class="${{isSim ? 'simmons-row' : ''}}">
      <td>${{item.rank}}</td>
      <td>${{isSim ? '<strong>'+item.brand+'</strong>' : item.brand}} ${{badge}}${{lowResNote}}</td>
      <td style="text-align:right">${{displayVal}}</td>
      <td class="detail-cell" style="display:none">
        <span class="formula-text">${{rawVal.toFixed(1)}}</span>
      </td>
      <td class="detail-cell" style="display:none">
        <span class="formula-text">${{formula}}</span>
      </td>
      <td class="detail-cell" style="display:none">Google Trends · KR · N=5 중앙값</td>
      <td class="detail-cell" style="display:none">${{isLowRes ? '⚠ 해상도 한계 (원본값 < 1)' : '정상'}}</td>
    </tr>`;
  }}).join('');

  return `
    <div class="rank-table-wrap" style="margin-top:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <p style="font-size:11px;font-weight:600;color:#555">상세 데이터</p>
        <button onclick="toggleDetailCols(this)" style="font-size:10px;padding:2px 8px;border:1px solid #ccc;border-radius:3px;background:#fff;cursor:pointer">
          산출식 보기 ▾
        </button>
      </div>
      <table class="rank-detail-table">
        <thead><tr>
          <th>순위</th><th>브랜드</th><th>지수</th>
          <th class="detail-cell" style="display:none">원본값</th>
          <th class="detail-cell" style="display:none">산출식</th>
          <th class="detail-cell" style="display:none">수집 방식</th>
          <th class="detail-cell" style="display:none">상태</th>
        </tr></thead>
        <tbody>${{rows}}</tbody>
      </table>
    </div>`;
}}

function toggleDetailCols(btn) {{
  const table = btn.closest('.rank-table-wrap').querySelector('table');
  const cells = table.querySelectorAll('.detail-cell');
  const isHidden = cells[0].style.display === 'none';
  cells.forEach(c => c.style.display = isHidden ? '' : 'none');
  btn.textContent = isHidden ? '산출식 접기 ▴' : '산출식 보기 ▾';
}}

// C: 네이버 순위 상세 데이터 테이블
function renderNaverRankTable(items) {{
  const rows = items.map(item => {{
    const badge = `<span class="src-badge ns">NS</span>`;
    const isSim = item.brand === '시몬스';
    return `<tr class="${{isSim ? 'simmons-row' : ''}}">
      <td>${{item.rank}}</td>
      <td>${{isSim ? '<strong>'+item.brand+'</strong>' : item.brand}} ${{badge}}</td>
      <td style="text-align:right">${{item.value.toFixed(1)}}</td>
      <td class="detail-cell" style="display:none">
        <span class="formula-text">블로그+뉴스 건수</span>
      </td>
      <td class="detail-cell" style="display:none">Naver 검색 API · 블로그+뉴스</td>
      <td class="detail-cell" style="display:none">정상</td>
    </tr>`;
  }}).join('');

  return `
    <div class="rank-table-wrap" style="margin-top:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <p style="font-size:11px;font-weight:600;color:#555">상세 데이터</p>
        <button onclick="toggleDetailCols(this)" style="font-size:10px;padding:2px 8px;border:1px solid #ccc;border-radius:3px;background:#fff;cursor:pointer">
          산출식 보기 ▾
        </button>
      </div>
      <table class="rank-detail-table">
        <thead><tr>
          <th>순위</th><th>브랜드</th><th>지수</th>
          <th class="detail-cell" style="display:none">수집값</th>
          <th class="detail-cell" style="display:none">수집 방식</th>
          <th class="detail-cell" style="display:none">상태</th>
        </tr></thead>
        <tbody>${{rows}}</tbody>
      </table>
    </div>`;
}}

// 2. 네이버 순위 바차트
function renderNaverRank(sharedLeft) {{
  const norm = RAW.naver?.normalized || {{}};
  let entries = Object.entries(norm);
  entries = _filterByTier(entries);
  const sorted = entries.sort((a,b)=>a[1]-b[1]);  // 오름차순 → ECharts 가로막대에서 높은 값이 위
  if (!sorted.length) return;
  const chartDomRaw = reInitChart('chart-naver-rank');
  const chartDom = chartDomRaw || document.getElementById('chart-naver-rank');
  const h = calcBarChartHeight(sorted.length);
  chartDom.style.height = h + 'px';
  const chart = echarts.init(chartDom);
  const vals = sorted.map(x=>x[1]).filter(v=>v!=null);
  const brandNames = sorted.map(x=>x[0]);
  const dataMax = vals.length ? Math.max(...vals) : 100;
  const xOpt = axisOption(dataMax, '', 5);
  const lm = sharedLeft !== undefined ? sharedLeft : leftMargin(brandNames);
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
    tooltip: {{
      trigger: 'axis',
      axisPointer: {{ type: 'shadow' }},
      confine: true,
      position: function(point, params, dom, rect, size) {{
        const tooltipW = size.contentSize[0];
        const chartW   = size.viewSize[0];
        const x = rect.x + rect.width + 8;
        return [x + tooltipW > chartW ? rect.x - tooltipW - 8 : x, rect.y];
      }},
      backgroundColor: '#ffffff',
      borderColor: '#cccccc',
      borderWidth: 1,
      textStyle: {{ color: '#333', fontSize: 12 }},
      extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15); pointer-events:none;',
      formatter: p => {{
        const t = BRAND_TO_TIER[p[0].name] || '?';
        return `${{p[0].name}} [Tier ${{t}}]<br>${{p[0].value}} (시몬스=100)`;
      }}
    }}
  }});
  chart.resize();
  // C: 네이버 순위 상세 테이블 삽입
  const naverTableItems = sorted.slice().reverse().map((entry, i) => ({{
    brand: entry[0], value: entry[1], rank: i + 1
  }}));
  const naverTableHtml = renderNaverRankTable(naverTableItems);
  const existingNaverTable = chartDom.nextElementSibling;
  if (existingNaverTable && existingNaverTable.classList.contains('rank-table-wrap')) {{
    existingNaverTable.remove();
  }}
  chartDom.insertAdjacentHTML('afterend', naverTableHtml);
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

// 3. 월별 추이 (시몬스=강조 · 13개월 monthly_series 활용)
function renderMonthly() {{
  const ms = RAW.google?.monthly_series || {{}};
  const brands = Object.keys(ms);
  if (!brands.length) {{
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

  // 기간 필터 적용
  const periodMap = {{ '3M': 3, '6M': 6, '12M': 12, 'ALL': 999 }};
  const limit = periodMap[_activePeriod] || 6;

  // 전체 기간 목록 (시몬스 기준)
  const simonsPts = ms['시몬스'] || [];
  const allPeriods = simonsPts.map(p => p.period?.substring(0,7)).filter(Boolean);
  const slicedPeriods = allPeriods.slice(-limit);

  // 기본 ON 브랜드: 시몬스, 에이스침대, 씰리침대, 한샘, 이케아
  const DEFAULT_ON = ['시몬스', '에이스침대', '씰리침대', '한샘', '이케아'];
  const IKEA_KEY = brands.find(b => b.includes('이케아') || b.includes('IKEA'));

  // 시리즈 생성
  const series = brands.map(brand => {{
    const pts = ms[brand] || [];
    // 기간 필터링
    const filtered = pts.filter(p => slicedPeriods.includes(p.period?.substring(0,7)));
    const values = slicedPeriods.map(period => {{
      const pt = filtered.find(p => p.period?.substring(0,7) === period);
      return pt ? pt.value : null;  // 결측은 null (선 끊김)
    }});

    const isSimmons = brand === '시몬스';
    const isDefaultOn = DEFAULT_ON.includes(brand) || (IKEA_KEY && brand === IKEA_KEY);

    return {{
      name: brand,
      type: 'line',
      data: values,
      connectNulls: false,
      lineStyle: {{
        width: isSimmons ? 3 : 1.5,
        color: isSimmons ? '#1a1a1a' : undefined,
      }},
      itemStyle: {{ color: isSimmons ? '#1a1a1a' : undefined }},
      symbol: isSimmons ? 'circle' : 'none',
      symbolSize: 5,
      selected: isDefaultOn,
      endLabel: {{
        show: isDefaultOn,
        formatter: '{{b}}',
        fontSize: 10,
        offset: [4, 0]
      }},
      emphasis: {{ focus: 'series' }}
    }};
  }});

  // 전체 legendSelected: DEFAULT_ON 기준
  const legendSelected = {{}};
  brands.forEach(b => {{
    legendSelected[b] = DEFAULT_ON.includes(b) || (IKEA_KEY && b === IKEA_KEY);
  }});

  // 표시 중인 시리즈의 최댓값으로 y축 자동 계산
  const visibleMax = Math.max(...series
    .filter(s => legendSelected[s.name])
    .flatMap(s => s.data.filter(v => v != null))
    .concat([100])
  );

  // 실제 범위 표기
  const rangeLabel = slicedPeriods.length > 0
    ? `${{slicedPeriods[0].replace('-','.')}}.01 ~ ${{slicedPeriods[slicedPeriods.length-1].replace('-','.')}}.01 (${{slicedPeriods.length}}개월)`
    : '';

  const dom = reInitChart('chart-monthly');
  if (!dom) return;
  dom.style.height = '480px';
  const chart = echarts.init(dom);

  chart.setOption({{
    title: {{
      text: rangeLabel,
      textStyle: {{ fontSize: 11, color: '#888', fontWeight: 'normal' }},
      left: 0, top: 0
    }},
    legend: {{
      type: 'scroll',
      bottom: 0,
      selected: legendSelected,
      textStyle: {{ fontSize: 11 }}
    }},
    grid: {{ left: 55, right: 80, top: 30, bottom: 60 }},
    xAxis: dateAxisOption(slicedPeriods),
    yAxis: axisOption(visibleMax, '', 5),
    series,
    tooltip: {{
      trigger: 'axis',
      confine: true,
      backgroundColor: '#fff',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {{ fontSize: 11 }}
    }}
  }});

  renderMonthlyHeatmap();
}}

// 3-b. 월별 전월비 히트맵 (셀 분할: 좌=지수값, 우=증감률)
function renderMonthlyHeatmap() {{
  const ms = RAW.google?.monthly_series || {{}};
  const brands = Object.keys(ms);
  if (!brands.length) return;

  const simonsPts = ms['시몬스'] || [];
  const allPeriods = simonsPts.map(p => p.period?.substring(0,7)).filter(Boolean);

  if (allPeriods.length < 3) return;

  // 지수값 + 전월비 계산
  const rows = brands.map(brand => {{
    const pts = ms[brand] || [];
    const byPeriod = {{}};
    pts.forEach(p => {{ byPeriod[p.period?.substring(0,7)] = p.value; }});

    const cells = allPeriods.map((period, i) => {{
      const curr = byPeriod[period] ?? null;
      if (i === 0) return {{ val: curr, delta: null }};
      const prev = byPeriod[allPeriods[i-1]] ?? null;
      const delta = (curr != null && prev != null && prev !== 0)
        ? ((curr - prev) / prev * 100) : null;
      return {{ val: curr, delta }};
    }});
    return {{ brand, cells }};
  }});

  // 색상: 양수=녹, 음수=적, null=회색
  function heatColor(v) {{
    if (v === null) return '#f0f0f0';
    if (v > 20)  return '#1a7a3c';
    if (v > 10)  return '#27ae60';
    if (v > 0)   return '#82c99d';
    if (v > -10) return '#f5a89a';
    if (v > -20) return '#e74c3c';
    return '#a93226';
  }}

  // 헤더: 월 이름 — 월 경계마다 좌측 구분선
  const colHeaders = allPeriods.slice(1).map(p =>
    `<th style="font-size:10px;padding:4px 6px;text-align:center;min-width:90px;
                border-left:2px solid #b0bec5;border-bottom:2px solid #b0bec5;">
      ${{p.substring(2).replace('-','.')}}
    </th>`
  ).join('');

  const tableRows = rows.map(r => {{
    const isSim = r.brand === '시몬스';
    const tdCells = r.cells.slice(1).map(c => {{
      const bg    = heatColor(c.delta);
      const dText = c.delta === null ? '—' : (c.delta > 0 ? '+' : '') + c.delta.toFixed(1) + '%';
      const dColor = c.delta === null ? '#aaa' : Math.abs(c.delta) > 10 ? '#fff' : '#333';
      const vText = c.val !== null ? c.val.toFixed(1) : '—';
      return `<td style="padding:0;border-bottom:1px solid #e8e8e8;border-left:2px solid #b0bec5;">
        <div style="display:flex;align-items:stretch;min-height:28px;">
          <div style="flex:1;display:flex;align-items:center;justify-content:center;
                      font-size:10px;color:#555;border-right:1px solid #ddd;padding:2px 4px;">
            ${{vText}}
          </div>
          <div style="flex:1;display:flex;align-items:center;justify-content:center;
                      background:${{bg}};color:${{dColor}};font-size:10px;padding:2px 4px;font-weight:500;">
            ${{dText}}
          </div>
        </div>
      </td>`;
    }}).join('');

    return `<tr>
      <td style="font-size:11px;padding:4px 8px;font-weight:${{isSim?'bold':'normal'}};
                 white-space:nowrap;border-bottom:1px solid #e8e8e8;border-right:2px solid #b0bec5;">${{r.brand}}</td>
      ${{tdCells}}
    </tr>`;
  }}).join('');

  const html = `
    <div style="margin-top:20px">
      <p style="font-size:12px;font-weight:600;color:#2c3e50;margin-bottom:6px">월별 전월비 증감 히트맵</p>
      <p style="font-size:10px;color:#999;margin-bottom:8px">좌: 지수값 (시몬스=100) &nbsp;|&nbsp; 우: 전월비 증감률(%)</p>
      <div style="overflow-x:auto">
        <table style="border-collapse:collapse;font-size:11px;width:100%;border:2px solid #b0bec5;border-radius:6px;overflow:hidden;">
          <thead><tr style="background:#eceff1;">
            <th style="text-align:left;padding:5px 8px;font-size:10px;min-width:80px;border-bottom:2px solid #b0bec5;border-right:2px solid #b0bec5;">브랜드</th>
            ${{colHeaders}}
          </tr></thead>
          <tbody>${{tableRows}}</tbody>
        </table>
      </div>
      <p style="font-size:10px;color:#999;margin-top:6px">— = 데이터 없음</p>
    </div>`;

  const container = document.getElementById('monthly-heatmap');
  if (container) container.innerHTML = html;
}}

// 4. Share of Search 파이차트 (시몬스 강조)
function renderSoS() {{
  const sos = RAW.sos || {{}};
  let entries = Object.entries(sos);
  if (_activeTier !== 'ALL') {{
    entries = entries.filter(([name]) => name === '시몬스' || BRAND_TO_TIER[name] === _activeTier);
  }}
  const sorted = entries.sort((a,b)=>b[1]-a[1]);
  const total = sorted.reduce((s,[,v])=>s+v, 0);
  const data = sorted.map(([name,val])=>{{
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

  // SoS 상세 테이블
  const rows = sorted.map(([name, val], i) => {{
    const tier = BRAND_TO_TIER[name] || '—';
    const isSimmons = name === '시몬스';
    const formula = `${{val.toFixed(2)}}% = ${{val.toFixed(2)}} ÷ ${{total.toFixed(2)}} × 100`;
    return `<tr style="${{isSimmons ? 'background:#fff8f8;font-weight:bold' : ''}}">
      <td style="text-align:center;color:#888;font-size:11px">${{i+1}}</td>
      <td>
        ${{isSimmons ? '<strong>'+name+'</strong>' : name}}
        <span class="src-badge gt">GT</span>
        <span style="font-size:10px;color:#888;margin-left:4px">Tier ${{tier}}</span>
      </td>
      <td style="text-align:right;font-weight:600;color:${{isSimmons?'#e53935':'#333'}}">${{val.toFixed(1)}}%</td>
      <td class="detail-cell" style="display:none;font-family:monospace;font-size:10px">${{formula}}</td>
      <td class="detail-cell" style="display:none;font-size:10px;color:#555">Google Trends · KR</td>
    </tr>`;
  }}).join('');

  const tableHtml = `
    <div class="rank-table-wrap" style="margin-top:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <p style="font-size:11px;font-weight:600;color:#555">브랜드별 SoS 상세</p>
        <button onclick="toggleDetailCols(this)" style="font-size:10px;padding:2px 8px;border:1px solid #ccc;border-radius:3px;background:#fff;cursor:pointer">
          산출식 보기 ▾
        </button>
      </div>
      <table class="rank-detail-table">
        <thead><tr>
          <th style="text-align:center;width:32px">#</th>
          <th>브랜드</th>
          <th style="text-align:right">SoS</th>
          <th class="detail-cell" style="display:none">산출식</th>
          <th class="detail-cell" style="display:none">출처</th>
        </tr></thead>
        <tbody>${{rows}}</tbody>
      </table>
    </div>`;
  const container = document.getElementById('sos-table');
  if (container) container.innerHTML = tableHtml;
}}

// 5. 갭 분석 — 좌우 대칭 축, 음수 레이블 겹침 방지
function renderGap() {{
  const gap = RAW.gap || [];
  let items = gap;
  if (!items.length) return;

  // gap이 배열인 경우 ({{brand, gap}} 형태)
  let sortedItems;
  if (Array.isArray(items)) {{
    sortedItems = items
      .filter(x => x.gap !== null && x.gap !== undefined)
      .sort((a, b) => a.gap - b.gap);
  }} else {{
    // 혹시 객체 형태인 경우
    sortedItems = Object.entries(items)
      .filter(([b, v]) => v !== null && v !== undefined)
      .sort(([,a],[,b]) => a - b)
      .map(([b, v]) => ({{brand: b, gap: v}}));
  }}

  if (!sortedItems.length) return;

  const brands = sortedItems.map(x => x.brand);
  const vals = sortedItems.map(x => x.gap);
  const absMax = Math.max(...vals.map(v => Math.abs(v)), 1);

  // 좌우 대칭 축
  const interval = niceInterval(absMax * 2 * 1.1, 5);
  const halfMax = Math.ceil(absMax * 1.1 / interval) * interval;

  // 동적 높이
  const BAR_H = 22, GAP_PX = 10, AXIS_AREA = 48, TOP = 16;
  const h = sortedItems.length * BAR_H + (sortedItems.length - 1) * GAP_PX + AXIS_AREA + TOP;

  // 음수 레이블이 브랜드명 침범하지 않도록 좌측 마진에 반영
  const negLabelMaxW = Math.max(...vals.filter(v => v < 0).map(v => measureTextWidth(v.toFixed(1))), 0);
  const lm = Math.max(leftMargin(brands), leftMargin(brands) + Math.ceil(negLabelMaxW) + 8, 96);
  const rightM = 64;

  const dom = reInitChart('chart-gap');
  if (!dom) return;
  dom.style.height = h + 'px';
  const chart = echarts.init(dom);

  chart.setOption({{
    grid: {{ left: lm, right: rightM, top: TOP, bottom: AXIS_AREA, containLabel: false }},
    xAxis: {{
      type: 'value',
      min: -halfMax,
      max: halfMax,
      interval,
      axisLabel: {{
        fontSize: 11,
        rotate: 0,
        formatter: v => v === 0 ? '0' : (v > 0 ? '+' + v : String(v))
      }},
      axisLine: {{ show: true }},
      splitLine: {{ show: true, lineStyle: {{ type: 'dashed', color: '#eee' }} }}
    }},
    yAxis: {{
      type: 'category',
      data: brands,
      axisLabel: {{
        fontSize: 11,
        margin: 8,
        formatter: b => b
      }},
      axisTick: {{ alignWithLabel: true }},
      boundaryGap: true
    }},
    series: [{{
      type: 'bar',
      data: vals.map((v, i) => ({{
        value: v,
        itemStyle: {{ color: brands[i] === '시몬스' ? '#0b0b0b' : (v >= 0 ? '#3498db' : '#e74c3c') }},
        label: {{
          show: true,
          position: v >= 0 ? 'right' : 'left',
          formatter: p => (p.value > 0 ? '+' : '') + p.value.toFixed(1),
          fontSize: 10,
          color: '#333'
        }}
      }})),
      barMaxWidth: BAR_H,
      markLine: {{
        silent: true,
        symbol: 'none',
        lineStyle: {{ color: '#333', width: 1.5, type: 'solid' }},
        data: [{{ xAxis: 0 }}]
      }}
    }}],
    tooltip: {{
      trigger: 'axis',
      confine: true,
      backgroundColor: '#fff',
      borderColor: '#ccc',
      borderWidth: 1,
      formatter: params => `${{params[0].name}}: ${{params[0].value > 0 ? '+' : ''}}${{params[0].value.toFixed(1)}}`
    }}
  }});

  // 겹침 검증
  setTimeout(() => checkOverlap(dom, 'Gap'), 300);
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
    const pts = (ms[brand] || []).slice(-12);  // 최근 12개월
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

  const nMonths = Math.min(12, Math.max(...ordered.map(b => {{
    const pts = (ms[b] || []).slice(-12);
    return pts.map(p => p.value).filter(v => v != null && !isNaN(v)).length;
  }}), 0));

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
  const msAll = dl.monthly_series || {{}};
  const periodsAll = dl.periods || [];
  if (!Object.keys(msAll).length) return;

  document.getElementById('datalab-row').style.display = '';

  // 기간 필터 적용
  const periodMap = {{ '3M': 3, '6M': 6, '12M': 12, 'ALL': 9999 }};
  const limit = periodMap[_activePeriod] || 12;
  const periods = periodsAll.slice(-limit);
  const ms = {{}};
  Object.entries(msAll).forEach(([brand, pts]) => {{
    ms[brand] = pts.slice(-limit);
  }});

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
  // P0-3: SoM 산출 브랜드(non-caution)만 scatter에 표시
  // P1-3: 시몬스 포함 (DART 감사보고서 수동 입력)
  const mainData = data.filter(d => d.som !== null && d.som !== undefined && !d.caution);
  const cautionData = data.filter(d => d.caution);
  if (!mainData.length) return;

  document.getElementById('section-sos-som').style.display = '';

  const maxVal = Math.max(...mainData.map(d => Math.max(d.sos, d.som || 0))) * 1.2;

  function makePoint(d) {{
    const isSimmons = d.is_simmons;
    return {{
      name: d.brand,
      value: [d.sos, d.som],
      symbol: isSimmons ? 'pin' : 'circle',
      symbolSize: isSimmons ? 22 : 15,
      itemStyle: {{color: COLORS[d.brand] || '#888', opacity: 0.95}},
      label: {{
        show: true,
        formatter: isSimmons ? d.brand + ' ★' : d.brand,
        position: 'top',
        fontSize: isSimmons ? 11 : 10,
        fontWeight: isSimmons ? 'bold' : 'normal',
        color: COLORS[d.brand] || '#333',
      }},
    }};
  }}

  const sosSomMaxX = Math.max(...mainData.map(d => d.sos), 1);
  const sosSomMaxY = Math.max(...mainData.map(d => d.som || 0), 1);
  const xOptSoSSoM = Object.assign(axisOption(sosSomMaxX, '%', 5), {{name:'SoS-카테고리 (%)',nameLocation:'middle',nameGap:30}});
  const yOptSoSSoM = Object.assign(axisOption(sosSomMaxY, '%', 5), {{name:'SoM (%)',nameLocation:'middle',nameGap:40}});

  gc('chart-sos-som').setOption({{
    grid: {{left: 60, right: 30, top: 40, bottom: 50}},
    xAxis: xOptSoSSoM,
    yAxis: yOptSoSSoM,
    series: [
      {{
        name: '침대 전업',
        type: 'scatter',
        data: mainData.map(d => makePoint(d)),
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
      }},
    ],
    tooltip: {{
      formatter: p => {{
        const d = mainData.find(x => x.brand === p.name);
        if (!d) return p.name;
        const src = d.data_source === 'DART_audit_report' ? '<br><span style="font-size:10px;color:#666;">출처: DART 감사보고서</span>' : '';
        const note = d.som_note ? `<br><span style="font-size:10px;color:#b45309;">⚠ ${{d.som_note}}</span>` : '';
        return `<b>${{p.name}}</b> [Tier ${{d.tier}}]<br>SoS(카테고리): ${{d.sos}}%<br>SoM: ${{d.som}}%${{src}}${{note}}`;
      }}
    }},
  }});

  // P0-3: caution 브랜드 참고 테이블 (SoS만 표시)
  const refEl = document.getElementById('sos-som-caution-ref');
  if (refEl && cautionData.length) {{
    const rows = cautionData.map(d =>
      `<tr>
        <td style="padding:4px 8px;font-size:11px;color:${{COLORS[d.brand]||'#555'}};font-weight:600;">${{d.brand}}</td>
        <td style="padding:4px 8px;font-size:11px;text-align:right;">${{d.sos.toFixed(1)}}%</td>
        <td style="padding:4px 8px;font-size:11px;color:#999;">—</td>
        <td style="padding:4px 8px;font-size:10px;color:#b45309;">전사 매출 혼재 (SoM 산출 불가)</td>
      </tr>`
    ).join('');
    refEl.innerHTML = `
      <div style="margin-top:12px;font-size:11px;color:#888;font-weight:600;margin-bottom:4px;">복합 사업 브랜드 참고 (SoS만 산출)</div>
      <table style="width:100%;border-collapse:collapse;border:1px solid #eee;">
        <thead>
          <tr style="background:#f9f9f9;">
            <th style="padding:4px 8px;font-size:10px;font-weight:600;text-align:left;color:#555;">브랜드</th>
            <th style="padding:4px 8px;font-size:10px;font-weight:600;text-align:right;color:#555;">SoS</th>
            <th style="padding:4px 8px;font-size:10px;font-weight:600;color:#555;">SoM</th>
            <th style="padding:4px 8px;font-size:10px;font-weight:600;color:#555;">비고</th>
          </tr>
        </thead>
        <tbody>${{rows}}</tbody>
      </table>`;
  }}
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

  // 이번 달 변화점: monthly_series 등락폭 상위 5
  // P0-1: 미완결 월이면 N-2 vs N-3 (직전 완결 월 기준)으로 전환
  const changeEl = document.getElementById('insight-changes');
  const changesTitleEl = document.getElementById('section-changes-title');
  (function renderThisMonthChanges() {{
    const ms = RAW.google?.monthly_series || {{}};
    const simonsPts = ms['시몬스'] || [];
    const minLen = IS_PARTIAL_MONTH ? 3 : 2;
    if (simonsPts.length < minLen) {{
      changeEl.innerHTML = '<div style="grid-column:1/-1;color:#aaa;font-size:12px;padding:12px">전월 비교 데이터 없음 — ' + minLen + '개월 이상 수집 후 자동 표시</div>';
      return;
    }}

    let latestPeriod, prevPeriod, titleText;
    if (IS_PARTIAL_MONTH) {{
      // N-2(직전 완결 월) vs N-3
      latestPeriod = simonsPts[simonsPts.length - 2].period?.substring(0, 7);
      prevPeriod   = simonsPts[simonsPts.length - 3].period?.substring(0, 7);
      titleText = `지난달 변화점 (${{latestPeriod}}) — 이번달 부분 집계`;
    }} else {{
      latestPeriod = simonsPts[simonsPts.length - 1].period?.substring(0, 7);
      prevPeriod   = simonsPts[simonsPts.length - 2].period?.substring(0, 7);
      titleText = '이번 달 변화점';
    }}
    if (changesTitleEl) changesTitleEl.textContent = titleText;

    const movers = Object.entries(ms).map(([brand, pts]) => {{
      const byP = {{}};
      pts.forEach(p => {{ byP[p.period?.substring(0,7)] = p.value; }});
      const curr = byP[latestPeriod], prev = byP[prevPeriod];
      if (curr == null || prev == null || prev === 0) return null;
      return {{ brand, pct: (curr - prev) / prev * 100, curr }};
    }}).filter(Boolean);

    movers.sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));

    changeEl.innerHTML = movers.slice(0, 5).map(m => {{
      const isRise = m.pct > 0;
      return `<div class="insight-item ${{isRise ? 'good' : 'warn'}}">
        <span style="font-size:11px;color:#888;">${{m.brand}} · ${{latestPeriod}}</span><br>
        <b>${{isRise ? '급등' : '급락'}} ${{isRise ? '+' : ''}}${{m.pct.toFixed(1)}}%</b>
        <span style="font-size:11px;color:#aaa;margin-left:6px">지수 ${{m.curr.toFixed(1)}}</span>
      </div>`;
    }}).join('');
  }})();
}}

// T3-3: 기본값 변경 배너 로직
function _updateFilterBanner() {{
  const tierBtn = document.querySelector('.tier-filter.active');
  const banner = document.getElementById('filter-changed-banner');
  if (!banner) return;
  const tierDefault = tierBtn?.dataset?.tier === 'ALL' || !tierBtn;
  banner.style.display = tierDefault ? 'none' : 'block';
}}

function setRange(btn, range) {{
  document.querySelectorAll('.period-pill[data-range]').forEach(b=>b.classList.remove('active'));
  btn.dataset.range = range;
  btn.classList.add('active');
  // range 문자열 → _activePeriod 매핑
  const rangeMap = {{
    'today 3-m': '3M',
    'today 6-m': '6M',
    'today 12-m': '12M',
    'all': 'ALL'
  }};
  _activePeriod = rangeMap[range] || '3M';
  // 기간에 영향받는 차트 재렌더링
  const hasMonthlySeries = Object.keys(RAW.google?.monthly_series || {{}}).length > 0;
  const hasDatalabSeries = Object.keys((RAW.datalab || {{}}).monthly_series || {{}}).length > 0;
  if (hasMonthlySeries) {{
    renderMonthly();
  }}
  if (hasDatalabSeries) {{
    renderDatalab();
  }}
  _updateFilterBanner();
}}

// T3-3: PDF 인쇄 표지 자동 기록
function exportPrint() {{
  const cover = document.getElementById('cover-page');
  const rangeBtn = document.querySelector('.period-pill.active[data-range]');
  const tierBtn = document.querySelector('.tier-filter.active');
  const rangeLabel = rangeBtn?.textContent || '최근 3개월';
  const tierLabel = tierBtn?.textContent || '전체';
  if (cover) {{
    const stateEl = cover.querySelector('#print-filter-state');
    if (stateEl) stateEl.textContent = `보고 기준: ${{rangeLabel}} · ${{tierLabel}}`;
  }}
  // ECharts 인스턴스 전체 리사이즈 후 인쇄 (차트 공백 방지)
  if (window._chartInstances) {{
    window._chartInstances.forEach(c => {{ try {{ c.resize(); }} catch(e) {{}} }});
  }}
  setTimeout(() => window.print(), 300);
}}

// 인쇄 전후 ECharts 강제 리사이즈
window.addEventListener('beforeprint', () => {{
  if (window._chartInstances) {{
    window._chartInstances.forEach(c => {{ try {{ c.resize(); }} catch(e) {{}} }});
  }}
}});
window.addEventListener('afterprint', () => {{
  if (window._chartInstances) {{
    window._chartInstances.forEach(c => {{ try {{ c.resize(); }} catch(e) {{}} }});
  }}
}});

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
renderRankCharts();
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
    formula: 'Gap = (네이버 지수 ÷ 네이버 평균 × 100) − (구글 지수 ÷ 구글 평균 × 100) | 브랜드 평균=100 기준 재정규화',
    source: 'Google Trends + Naver 검색 API',
    collected
  }});
  document.getElementById('section-gap')?.insertAdjacentHTML('beforeend', gapCaption);

  // 지수 설명 박스
  const gapGuide = `<div style="margin-top:10px;padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;font-size:11px;color:#475569;line-height:1.9;">
    <div style="margin-bottom:6px;font-weight:700;color:#1e3a8a;font-size:11px;">📌 지수 해석 가이드</div>
    <div><span style="display:inline-block;width:16px;text-align:center;margin-right:4px;">🔵</span><b>구글 카테고리 지수</b> — Google Trends 검색 관심도 · 소비자가 얼마나 검색하는지 (수요 지표) · 11개 브랜드 평균=100 기준 · 최근 3개월 한국</div>
    <div style="margin-top:4px;"><span style="display:inline-block;width:16px;text-align:center;margin-right:4px;">🟢</span><b>네이버 카테고리 지수</b> — Naver 블로그+뉴스 총 건수 · 브랜드 관련 콘텐츠 발행량 (마케팅 활동 지표) · 11개 브랜드 평균=100 기준 · 전체 누적 인덱스</div>
    <div style="margin-top:5px;padding:6px 8px;background:#eff6ff;border-radius:4px;color:#1e40af;font-size:10.5px;">
      <b>산출식:</b> &nbsp;구글 카테고리 지수 = 브랜드 구글 지수 ÷ 전체 평균 × 100 &nbsp;|&nbsp; 네이버 카테고리 지수 = 브랜드 네이버 지수 ÷ 전체 평균 × 100 &nbsp;|&nbsp; <b>갭 = 네이버 지수 − 구글 지수</b>
    </div>
    <div style="margin-top:6px;padding-top:6px;border-top:1px solid #e2e8f0;color:#64748b;">
      <b>갭 해석:</b> &nbsp;100 = 카테고리 평균 수준 &nbsp;|&nbsp; 양수(+) = 네이버 콘텐츠 상대 강세, 구글 대비 마케팅 활발 &nbsp;|&nbsp; 음수(−) = 구글 검색 강세, 브랜드 파워 대비 콘텐츠 발행 상대적 적음
    </div>
  </div>`;
  document.getElementById('section-gap')?.insertAdjacentHTML('beforeend', gapGuide);

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
  ['chart-google-rank','chart-google-rank-ikea','chart-naver-rank','chart-monthly','chart-datalab',
   'chart-sos','chart-gap','chart-gender','chart-age','chart-sos-som']
  .forEach(id=>{{const el=document.getElementById(id);if(el){{const inst=echarts.getInstanceByDom(el);if(inst)inst.resize();}}}});
}});
</script>
</body>
</html>"""
    return html
