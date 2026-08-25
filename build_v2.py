"""
report_2026_08_v2.html 생성
기존 report_2026_08.html 기반으로 두 섹션 추가:
  - 네이버 콘텐츠 노출량 (section-rank) 바로 아래
    → 상세 건수: 블로그 기준 / 뉴스 기준 (ECharts 동일 형식)
  - 맨 아래
    → 전체 매트리스 시장 매출 현황 (시몬스 비중)
"""
import os, sys, json, time, random, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# builder/dashboard.py 에서 실조사 데이터 임포트
sys.path.insert(0, os.path.dirname(__file__))
from builder.dashboard import _build_price_table, _YOUTUBE_STATIC_DATA

from dotenv import load_dotenv
load_dotenv()

BASE_DIR  = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "latest.json")
SRC_HTML  = os.path.join(BASE_DIR, "output", "report_2026_08.html")
DEST_HTML = os.path.join(BASE_DIR, "output", "report_2026_08_v2.html")

CLIENT_ID     = os.getenv("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

from brand_config import BRANDS, BRAND_TO_TIER_NEW

# 기존 네이버 차트와 동일한 color/opacity 로직
_BRAND_COLOR = {b["name"]: b["color"] for b in BRANDS}
_CAUTION_TIERS = {"C", "D"}

def brand_color(name):
    return _BRAND_COLOR.get(name, "#888888")

def brand_opacity(name):
    if name == "시몬스":
        return 1.0
    tier = BRAND_TO_TIER_NEW.get(name, "B")
    return 0.45 if tier in _CAUTION_TIERS else 0.75

def brand_item_style(name):
    style = {"color": brand_color(name), "opacity": brand_opacity(name)}
    if name == "시몬스":
        style["borderColor"] = "#c8a96e"
        style["borderWidth"] = 2
    return style

# ── 1. 네이버 API 블로그/뉴스 분리 수집 ─────────────────────────────────────

def _api_count(query, api_type):
    url = (f"https://openapi.naver.com/v1/search/{api_type}"
           f"?query={urllib.parse.quote(query)}&display=1")
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        time.sleep(random.uniform(0.3, 0.6))
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode()).get("total", 0)
    except Exception as e:
        print(f"  [API 오류] {api_type}/{query}: {e}")
        return 0


def fetch_blog_news():
    if not CLIENT_ID:
        print("  [skip] NAVER_CLIENT_ID 없음")
        return None
    print("  [Naver API] 블로그/뉴스 분리 수집 중...")
    results = {}
    for b in BRANDS:
        kw   = b["naver_kw"]
        name = b["name"]
        blog = _api_count(kw, "blog")
        news = _api_count(kw, "news")
        results[name] = {"blog": blog, "news": news, "kw": kw}
        print(f"    {name}: 블로그 {blog:,} / 뉴스 {news:,}")
    return results


# ── 2. 매출 데이터 ──────────────────────────────────────────────────────────

def load_revenue():
    with open(DATA_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("dart", {})


# ── 3. 상세 건수 섹션 (ECharts 동일 형식) ───────────────────────────────────

def _chart_rows(sorted_items, base_color_key="brand"):
    """ECharts series data + 순위 테이블 행 생성 헬퍼"""
    echarts_data, table_rows = [], ""
    for rank, (name, val) in enumerate(sorted_items, 1):
        is_simm = name == "시몬스"
        bg  = "#f8f8f8" if is_simm else "transparent"
        fw  = "700"     if is_simm else "400"
        echarts_data.append({"value": val, "name": name, "itemStyle": brand_item_style(name)})
        badge_color = brand_color(name)
        table_rows += f"""
          <tr style="background:{bg};">
            <td style="padding:5px 10px;color:#888;font-size:12px;">{rank}</td>
            <td style="padding:5px 10px;">
              <span style="background:{badge_color};color:#fff;padding:1px 7px;border-radius:3px;
                font-size:10px;font-weight:700;opacity:{brand_opacity(name)};">{name}</span>
            </td>
            <td style="padding:5px 10px;text-align:right;font-weight:{fw};font-size:12px;">{val}</td>
          </tr>"""
    return echarts_data, table_rows


def build_detail_section(api_data):
    """상세 건수 섹션 HTML (section-rank 바로 아래 삽입)"""

    if api_data is None:
        return """
  <!-- 상세 건수 — API 없음 -->
  <div class="chart-row" style="margin-bottom:0;">
    <div class="card">
      <div class="card-title">상세 건수 — 블로그 · 뉴스 기준</div>
      <div class="card-sub" style="color:#e65100;">⚠ NAVER_CLIENT_ID 미설정 — 분리 수집 불가</div>
    </div>
  </div>"""

    # 시몬스 기준 정규화
    blog_base = api_data["시몬스"]["blog"] or 1
    news_base = api_data["시몬스"]["news"] or 1

    blog_norm = {n: round(v["blog"] / blog_base * 100, 1) for n, v in api_data.items()}
    news_norm = {n: round(v["news"]  / news_base * 100, 1) for n, v in api_data.items()}

    blog_sorted = sorted(blog_norm.items(), key=lambda x: x[1], reverse=True)
    news_sorted = sorted(news_norm.items(), key=lambda x: x[1], reverse=True)

    blog_echarts, blog_table = _chart_rows(blog_sorted)
    news_echarts, news_table = _chart_rows(news_sorted)

    # 실제 건수 표 (블로그)
    blog_raw_sorted = sorted(api_data.items(), key=lambda x: x[1]["blog"], reverse=True)
    news_raw_sorted = sorted(api_data.items(), key=lambda x: x[1]["news"],  reverse=True)

    def raw_table(raw_sorted, key):
        rows = ""
        for rank, (name, v) in enumerate(raw_sorted, 1):
            cnt  = v[key]
            is_s = name == "시몬스"
            bg   = "#f8f8f8" if is_s else "transparent"
            fw   = "700"     if is_s else "400"
            rows += f"""
          <tr style="background:{bg};">
            <td style="padding:5px 10px;color:#888;font-size:12px;">{rank}</td>
            <td style="padding:5px 10px;">
              <span style="background:{brand_color(name)};color:#fff;padding:1px 7px;border-radius:3px;
                font-size:10px;font-weight:700;opacity:{brand_opacity(name)};">{name}</span>
            </td>
            <td style="padding:5px 10px;text-align:right;font-weight:{fw};font-size:12px;">{cnt:,}건</td>
          </tr>"""
        return rows

    blog_raw_rows = raw_table(blog_raw_sorted, "blog")
    news_raw_rows = raw_table(news_raw_sorted, "news")

    import json as _json
    blog_json = _json.dumps(blog_echarts, ensure_ascii=False)
    news_json = _json.dumps(news_echarts, ensure_ascii=False)

    chart_h = max(len(api_data) * 28 + 40, 320)

    return f"""
  <!-- 상세 건수: 블로그/뉴스 기준 -->
  <div class="chart-row col2" id="section-detail-counts">
    <!-- 블로그 기준 -->
    <div class="card">
      <div class="card-title">상세 건수 — 블로그 기준
        <span class="source-badge badge-naver">Naver Search</span>
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub">시몬스=100 기준 · 블로그 건수</div>
      <div id="chart-naver-blog" style="height:{chart_h}px;"></div>
      <details style="margin-top:12px;">
        <summary style="cursor:pointer;font-size:12px;font-weight:600;color:#374151;padding:6px 0;
          border-top:1px solid #f0f0f0;list-style:none;display:flex;align-items:center;gap:6px;">
          <span>상세 데이터</span>
          <span style="font-size:10px;background:#e5e7eb;padding:1px 8px;border-radius:10px;">산출식 보기 ▾</span>
        </summary>
        <table style="width:100%;border-collapse:collapse;margin-top:8px;">
          <thead>
            <tr style="border-bottom:1px solid #e5e7eb;">
              <th style="padding:5px 10px;text-align:left;font-size:11px;color:#888;">순위</th>
              <th style="padding:5px 10px;text-align:left;font-size:11px;color:#888;">브랜드</th>
              <th style="padding:5px 10px;text-align:right;font-size:11px;color:#888;">지수</th>
            </tr>
          </thead>
          <tbody>{blog_table}</tbody>
        </table>
        <div style="margin-top:8px;font-size:10px;color:#999;border-top:1px solid #f0f0f0;padding-top:6px;">
          실제 건수 (내림차순):
          <table style="width:100%;border-collapse:collapse;margin-top:4px;">
            <tbody>{blog_raw_rows}</tbody>
          </table>
        </div>
      </details>
    </div>

    <!-- 뉴스 기준 -->
    <div class="card">
      <div class="card-title">상세 건수 — 뉴스 기준
        <span class="source-badge badge-naver">Naver Search</span>
        <span class="period-chip">최근 3개월</span>
      </div>
      <div class="card-sub">시몬스=100 기준 · 뉴스 건수</div>
      <div id="chart-naver-news" style="height:{chart_h}px;"></div>
      <details style="margin-top:12px;">
        <summary style="cursor:pointer;font-size:12px;font-weight:600;color:#374151;padding:6px 0;
          border-top:1px solid #f0f0f0;list-style:none;display:flex;align-items:center;gap:6px;">
          <span>상세 데이터</span>
          <span style="font-size:10px;background:#e5e7eb;padding:1px 8px;border-radius:10px;">산출식 보기 ▾</span>
        </summary>
        <table style="width:100%;border-collapse:collapse;margin-top:8px;">
          <thead>
            <tr style="border-bottom:1px solid #e5e7eb;">
              <th style="padding:5px 10px;text-align:left;font-size:11px;color:#888;">순위</th>
              <th style="padding:5px 10px;text-align:left;font-size:11px;color:#888;">브랜드</th>
              <th style="padding:5px 10px;text-align:right;font-size:11px;color:#888;">지수</th>
            </tr>
          </thead>
          <tbody>{news_table}</tbody>
        </table>
        <div style="margin-top:8px;font-size:10px;color:#999;border-top:1px solid #f0f0f0;padding-top:6px;">
          실제 건수 (내림차순):
          <table style="width:100%;border-collapse:collapse;margin-top:4px;">
            <tbody>{news_raw_rows}</tbody>
          </table>
        </div>
      </details>
    </div>
  </div>

  <script>
  (function() {{
    var blogData = {blog_json};
    var newsData = {news_json};

    function initBar(divId, data) {{
      var el = document.getElementById(divId);
      if (!el || typeof echarts === 'undefined') return;
      var rev  = data.slice().reverse();
      var chart = echarts.init(el);
      chart.setOption({{
        grid: {{ left: 100, right: 70, top: 10, bottom: 20 }},
        tooltip: {{ trigger: 'axis', formatter: function(p) {{
          return p[0].name + '<br/>지수: <b>' + p[0].value + '</b> (시몬스=100)';
        }} }},
        xAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }} }},
        yAxis: {{ type: 'category',
          data: rev.map(function(d) {{ return d.name; }}),
          axisLabel: {{ fontSize: 11, fontFamily: 'Malgun Gothic,Arial,sans-serif' }} }},
        series: [{{
          type: 'bar',
          barMaxWidth: 22,
          data: rev.map(function(d) {{ return {{
            value: d.value,
            itemStyle: d.itemStyle
          }}; }}),
          label: {{ show: true, position: 'right', fontSize: 11,
            formatter: function(p) {{ return p.value; }} }}
        }}]
      }});
      window.addEventListener('resize', function() {{ chart.resize(); }});
    }}

    // ECharts 로드 대기 후 초기화
    function tryInit() {{
      if (typeof echarts !== 'undefined') {{
        initBar('chart-naver-blog', blogData);
        initBar('chart-naver-news', newsData);
      }} else {{
        setTimeout(tryInit, 200);
      }}
    }}
    tryInit();
  }})();
  </script>"""


# ── 4. 매출 섹션 — 3개년 그룹 세로 막대 + 추세선 ───────────────────────────

def build_revenue_section():
    # FY2023/2024: DART·언론 IR 조사 (2026-08-25)
    # FY2025: 기존 수집 기준 유지
    BRANDS_REV = [
        # (이름, [FY2023, FY2024, FY2025], 출처, 추정여부)
        ("시몬스",        [3138, 3295, 3239], "DART 감사보고서",            False),
        ("에이스침대",    [3064, 3260, 3173], "DART 사업보고서",            False),
        ("코웨이 비렉스", [2618, 3167, 3654], "매트리스 부문 IR (추정★)",   True),
        ("템퍼",          [1016, 1119, 1229], "DART 공시 유한회사 (추정★)", True),
        ("씰리침대",      [ 676,  810,  889], "씰리코리아컴퍼니(유) DART",  False),
        ("지누스",        [ 384,  443,  590], "국내별도 사측발표 (추정★)",  True),
    ]

    total_fy25 = sum(d[1][2] for d in BRANDS_REV)
    simmons_som = round(3239 / total_fy25 * 100, 1)

    import json as _j

    bar_series  = []
    line_series = []
    legend_names = []

    for name, vals, src_note, is_est in BRANDS_REV:
        fy23, fy24, fy25 = vals
        yoy24 = round((fy24 - fy23) / fy23 * 100, 1)
        yoy25 = round((fy25 - fy24) / fy24 * 100, 1)
        col   = brand_color(name)
        opac  = brand_opacity(name)
        nm_j  = _j.dumps(name)
        col_j = _j.dumps(col)
        border_extra = ", borderColor: '#c8a96e', borderWidth: 2" if name == "시몬스" else ""

        bar_series.append(f"""{{
            name: {nm_j}, type: 'bar', barMaxWidth: 45, barCategoryGap: '22%', barGap: '30%',
            itemStyle: {{ color: {col_j}, opacity: {opac}{border_extra} }},
            label: {{
                show: true, position: 'top', distance: 6,
                rich: {{
                    v:  {{ fontSize: 12, color: '#111', fontWeight: 'bold' }},
                    up: {{ fontSize: 11, color: '#2e7d32', fontWeight: 'bold' }},
                    dn: {{ fontSize: 11, color: '#c62828', fontWeight: 'bold' }}
                }},
                formatter: function(p) {{
                    return '{{v|' + p.value.toLocaleString() + '}}';
                }}
            }},
            data: [{fy23}, {fy24}, {fy25}]
        }}""")

        # 추세선 제거됨

        legend_names.append(name)

    all_series  = ',\n            '.join(bar_series)
    legend_data = _j.dumps(legend_names)

    # 연도별 합계
    tot23 = sum(d[1][0] for d in BRANDS_REV)
    tot24 = sum(d[1][1] for d in BRANDS_REV)
    tot25 = sum(d[1][2] for d in BRANDS_REV)

    # 출처 테이블 (SoM% 포함)
    src_rows = ""
    for name, vals, src_note, is_est in BRANDS_REV:
        fy23, fy24, fy25 = vals
        yoy24  = round((fy24 - fy23) / fy23 * 100, 1)
        yoy25  = round((fy25 - fy24) / fy24 * 100, 1)
        som23  = round(fy23 / tot23 * 100, 1)
        som24  = round(fy24 / tot24 * 100, 1)
        som25  = round(fy25 / tot25 * 100, 1)
        sign24 = "+" if yoy24 >= 0 else ""
        sign25 = "+" if yoy25 >= 0 else ""
        c24    = "#2e7d32" if yoy24 >= 0 else "#c62828"
        c25    = "#2e7d32" if yoy25 >= 0 else "#c62828"
        BL  = "border-left:2px solid #cbd5e1;"   # 연도 구분선
        bold = "font-weight:700;background:#fafaf5;" if name == "시몬스" else ""
        # 각 셀: 매출액 | 전년비 | (비중%) — 한 줄 인라인
        cell23 = (f'<span style="font-size:13px;font-weight:700;">{fy23:,}</span>'
                  f'&nbsp;&nbsp;<span style="font-size:11px;color:#6b7280;">({som23}%)</span>')
        cell24 = (f'<span style="font-size:13px;font-weight:700;">{fy24:,}</span>'
                  f'&nbsp;<span style="font-size:11px;color:{c24};font-weight:600;">{sign24}{yoy24}%</span>'
                  f'&nbsp;&nbsp;<span style="font-size:11px;color:#6b7280;">({som24}%)</span>')
        cell25 = (f'<span style="font-size:13px;font-weight:700;">{fy25:,}</span>'
                  f'&nbsp;<span style="font-size:11px;color:{c25};font-weight:600;">{sign25}{yoy25}%</span>'
                  f'&nbsp;&nbsp;<span style="font-size:11px;color:#6b7280;">({som25}%)</span>')
        src_rows += f"""<tr style="{bold}border-bottom:1px solid #f0f0f0;">
          <td style="padding:7px 10px;font-size:12px;white-space:nowrap;font-weight:{'700' if name=='시몬스' else '400'};">{name}</td>
          <td style="padding:6px 12px;{BL}">{cell23}</td>
          <td style="padding:6px 12px;{BL}">{cell24}</td>
          <td style="padding:6px 12px;{BL}">{cell25}</td>
          <td style="padding:6px 10px;font-size:10px;color:#9ca3af;{BL}white-space:nowrap;">{src_note}</td>
        </tr>"""

    # 합계 행
    tot_yoy24 = round((tot24 - tot23) / tot23 * 100, 1)
    tot_yoy25 = round((tot25 - tot24) / tot24 * 100, 1)
    BL = "border-left:2px solid #374151;"
    total_row = f"""<tr style="background:#1a1a2e;color:#fff;font-weight:700;border-top:2px solid #4b5563;">
          <td style="padding:7px 10px;font-size:12px;">6개사 합계</td>
          <td style="padding:7px 12px;font-size:12px;{BL}">{tot23:,}억</td>
          <td style="padding:7px 12px;font-size:12px;{BL}">{tot24:,}억&nbsp;<span style="font-size:10px;color:#86efac;font-weight:600;">(+{tot_yoy24}%)</span></td>
          <td style="padding:7px 12px;font-size:12px;{BL}">{tot25:,}억&nbsp;<span style="font-size:10px;color:#86efac;font-weight:600;">(+{tot_yoy25}%)</span></td>
          <td style="padding:7px 10px;font-size:10px;color:#6b7280;{BL}">6개사 단순합</td>
        </tr>"""

    return f"""
  <div class="chart-row" id="section-revenue-market" style="margin-top:0;">
    <div class="card">
      <div class="card-title">매트리스 시장 매출 현황 · 시몬스 비중
        <span class="source-badge" style="background:#fff3e0;color:#e65100;border:1px solid #ffcc80;">추정치 포함</span>
        <span class="period-chip">FY2023–2025</span>
      </div>
      <div class="card-sub">침대·매트리스 매출이 분리되는 6개사 기준 · 3개년 추이</div>

      <div style="display:flex;gap:12px;margin:14px 0 12px;">
        <div style="background:#0b0b0b;border-radius:8px;padding:16px 20px;text-align:center;min-width:118px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div style="font-size:30px;font-weight:800;color:#c8a96e;line-height:1;">{simmons_som}%</div>
          <div style="font-size:12px;color:#d1d5db;margin-top:6px;font-weight:600;">시몬스 SoM</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:3px;">FY2025 · 6개사 {total_fy25:,}억</div>
        </div>
        <div style="flex:1;overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;">
            <tr style="background:#1a1a2e;color:#fff;">
              <th style="padding:7px 10px;text-align:left;font-size:11px;font-weight:600;">브랜드</th>
              <th style="padding:7px 12px;text-align:left;font-size:11px;font-weight:600;border-left:2px solid #374151;">FY2023&nbsp;<span style="font-size:9px;font-weight:400;color:#9ca3af;">매출 (비중)</span></th>
              <th style="padding:7px 12px;text-align:left;font-size:11px;font-weight:600;border-left:2px solid #374151;">FY2024&nbsp;<span style="font-size:9px;font-weight:400;color:#9ca3af;">매출 전년비 (비중)</span></th>
              <th style="padding:7px 12px;text-align:left;font-size:11px;font-weight:600;border-left:2px solid #374151;">FY2025&nbsp;<span style="font-size:9px;font-weight:400;color:#9ca3af;">매출 전년비 (비중)</span></th>
              <th style="padding:7px 10px;text-align:left;font-size:11px;font-weight:600;border-left:2px solid #374151;">출처</th>
            </tr>
            {src_rows}
            {total_row}
          </table>
        </div>
      </div>

      <div id="chart-revenue-3y" style="height:480px;"></div>
      <script>
      (function() {{
        var dom = document.getElementById('chart-revenue-3y');
        if (!dom || typeof echarts === 'undefined') return;
        var chart = echarts.init(dom);
        chart.setOption({{
          legend: {{
            data: {legend_data}, bottom: 0, type: 'scroll',
            itemWidth: 16, itemHeight: 10, textStyle: {{ fontSize: 13 }}
          }},
          grid: {{ left: 72, right: 20, top: 60, bottom: 60 }},
          xAxis: {{
            type: 'category', data: ['FY2023', 'FY2024', 'FY2025'],
            axisLabel: {{ fontSize: 14, fontWeight: 'bold' }},
            axisTick: {{ alignWithLabel: true }}
          }},
          yAxis: {{
            type: 'value', name: '억원',
            nameTextStyle: {{ fontSize: 11, color: '#999' }},
            axisLabel: {{ formatter: function(v) {{ return v.toLocaleString(); }}, fontSize: 11 }},
            splitLine: {{ lineStyle: {{ type: 'dashed', color: '#f0f0f0' }} }}
          }},
          tooltip: {{
            trigger: 'axis',
            formatter: function(params) {{
              var html = '<b>' + params[0].axisValue + '</b><br>';
              params.forEach(function(p) {{
                if (p.seriesName.indexOf('_trend_') === 0) return;
                html += p.marker + ' ' + p.seriesName + ': <b>' + p.value.toLocaleString() + '억</b><br>';
              }});
              return html;
            }}
          }},
          series: [
            {all_series}
          ]
        }});
        window.addEventListener('resize', function() {{ chart.resize(); }});
      }})();
      </script>

      <div style="margin-top:10px;font-size:10px;color:#9ca3af;background:#fffbeb;
        padding:8px 12px;border-radius:5px;border-left:3px solid #fbbf24;line-height:1.7;">
        ★ 코웨이 비렉스(매트리스 부문 IR)·지누스(국내별도 사측발표)·템퍼(유한회사 DART)는 공식 부문 공시가 아닌 추정·발표 기준.
        시몬스·에이스침대·씰리침대는 DART 공시 기준. 내부 참고용으로만 활용하고 대외 보고 시 주석 필요.
      </div>
    </div>
  </div>"""


# ── 5. 주력 매트리스 가격 비교 섹션 ────────────────────────────────────────

def build_price_section():
    # 원본 dashboard.py _build_price_table() 형식 그대로 사용 (2026년 8월 공식몰 조사)
    # id만 변경해 원본 section-price-table(하단)과 중복 방지
    html = _build_price_table()
    return html.replace('id="section-price-table"', 'id="section-price-compare"', 1)


# ── 6. YouTube 구독자 수 섹션 ────────────────────────────────────────────────

def build_youtube_section():
    # 실조사 데이터 (builder/dashboard.py _YOUTUBE_STATIC_DATA, 2026년 8월 직접 조사)
    # 템퍼는 12번째 브랜드로 추가됐으나 조사 미완료 → 미확인 처리
    raw = dict(_YOUTUBE_STATIC_DATA)
    raw["템퍼"] = {"subs": None, "channel": "Tempur Korea", "note": "미확인"}

    # 구독자 있는 항목 내림차순, 미확인 후순위
    sorted_items = sorted(
        raw.items(),
        key=lambda x: (x[1]["subs"] is None, -(x[1]["subs"] or 0))
    )

    import json as _json
    echarts_data = []
    table_rows   = ""
    for rank, (name, info) in enumerate(sorted_items, 1):
        subs  = info["subs"]
        ch    = info["channel"]
        note  = info.get("note", "")
        is_s  = name == "시몬스"
        bg    = "#f8f8f8" if is_s else "transparent"
        fw    = "700"     if is_s else "400"

        echarts_data.append({
            "value": subs or 0, "name": name,
            "itemStyle": brand_item_style(name),
        })

        if subs is None:
            sub_disp = f'<span style="color:#aaa;">미확인</span>'
        elif subs >= 10000:
            sub_disp = f"{subs/10000:.1f}만명"
        else:
            sub_disp = f"{subs:,}명"

        note_html = f'<span style="color:#aaa;font-size:10px;"> ({note})</span>' if note else ""
        table_rows += f"""
          <tr style="background:{bg};">
            <td style="padding:4px 10px;color:#888;font-size:12px;">{rank}</td>
            <td style="padding:4px 10px;">
              <span style="background:{brand_color(name)};color:#fff;padding:1px 7px;
                border-radius:3px;font-size:10px;font-weight:700;
                opacity:{brand_opacity(name)};">{name}</span>
            </td>
            <td style="padding:4px 10px;font-size:11px;color:#555;">{ch}{note_html}</td>
            <td style="padding:4px 10px;text-align:right;font-weight:{fw};font-size:12px;">{sub_disp}</td>
          </tr>"""

    chart_h = max(len(sorted_items) * 28 + 40, 320)
    rev_data = list(reversed(echarts_data))
    ed_json  = _json.dumps(rev_data, ensure_ascii=False)

    return f"""
  <div class="chart-row" id="section-youtube-subs">
    <div class="card">
      <div class="card-title">YouTube 공식 채널 구독자 수
        <span class="source-badge" style="background:#f3e5f5;color:#6a1b9a;border:1px solid #ce93d8;">직접 조사</span>
        <span class="period-chip">2026년 8월 기준</span>
      </div>
      <div class="card-sub">공식 채널 구독자 수 · 2026년 8월 직접 조사 / 씰리침대·템퍼 미확인</div>
      <div id="chart-youtube-subs" style="height:{chart_h}px;"></div>
      <details style="margin-top:12px;">
        <summary style="cursor:pointer;font-size:12px;font-weight:600;color:#374151;padding:6px 0;
          border-top:1px solid #f0f0f0;list-style:none;display:flex;align-items:center;gap:6px;">
          <span>상세 데이터</span>
          <span style="font-size:10px;background:#e5e7eb;padding:1px 8px;border-radius:10px;">채널 목록 ▾</span>
        </summary>
        <table style="width:100%;border-collapse:collapse;margin-top:8px;">
          <thead>
            <tr style="border-bottom:1px solid #e5e7eb;">
              <th style="padding:4px 10px;text-align:left;font-size:11px;color:#888;">순위</th>
              <th style="padding:4px 10px;text-align:left;font-size:11px;color:#888;">브랜드</th>
              <th style="padding:4px 10px;text-align:left;font-size:11px;color:#888;">채널</th>
              <th style="padding:4px 10px;text-align:right;font-size:11px;color:#888;">구독자</th>
            </tr>
          </thead>
          <tbody>{table_rows}</tbody>
        </table>
      </details>
    </div>
  </div>

  <script>
  (function() {{
    var ytData = {ed_json};
    function initYTChart() {{
      var el = document.getElementById('chart-youtube-subs');
      if (!el || typeof echarts === 'undefined') {{ setTimeout(initYTChart, 200); return; }}
      var chart = echarts.init(el);
      chart.setOption({{
        grid: {{ left: 110, right: 90, top: 10, bottom: 20 }},
        tooltip: {{ trigger: 'axis', formatter: function(p) {{
          var v = p[0].value;
          if (v === 0) return p[0].name + ': 미확인';
          var disp = v >= 10000 ? (v/10000).toFixed(1) + '만명' : v.toLocaleString() + '명';
          return p[0].name + '<br/>구독자: <b>' + disp + '</b>';
        }} }},
        xAxis: {{ type: 'value', axisLabel: {{ fontSize: 11,
          formatter: function(v) {{ return v >= 10000 ? (v/10000).toFixed(0) + '만' : v; }} }} }},
        yAxis: {{ type: 'category',
          data: ytData.map(function(d) {{ return d.name; }}),
          axisLabel: {{ fontSize: 11, fontFamily: 'Malgun Gothic,Arial,sans-serif' }} }},
        series: [{{
          type: 'bar', barMaxWidth: 22,
          data: ytData.map(function(d) {{ return {{
            value: d.value, itemStyle: d.itemStyle
          }}; }}),
          label: {{ show: true, position: 'right', fontSize: 11,
            formatter: function(p) {{
              var v = p.value;
              if (v === 0) return '미확인';
              return v >= 10000 ? (v/10000).toFixed(1) + '만' : v.toLocaleString();
            }} }}
        }}]
      }});
      window.addEventListener('resize', function() {{ chart.resize(); }});
    }}
    initYTChart();
  }})();
  </script>"""


# ── 7. 조합 및 저장 ─────────────────────────────────────────────────────────

def patch_sos_som_tempur(src: str) -> str:
    """
    latest.json에서 템퍼 Google Trends 데이터가 수집된 경우
    SOS_SOM_DATA의 템퍼 항목을 실데이터로 교체한다.
    템퍼 데이터 없으면 아무것도 하지 않는다.
    """
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            latest = json.load(f)
    except Exception:
        return src

    google_linked = latest.get("google", {}).get("linked", {})
    tempur_val = google_linked.get("템퍼")
    if not tempur_val or tempur_val <= 0:
        return src  # 아직 수집 안 됨 → 변경 없음

    # 6개 매출 브랜드 중 Google Trends 있는 것만 SoS 계산
    REV_BRANDS = ["코웨이 비렉스", "시몬스", "에이스침대", "템퍼", "씰리침대", "지누스"]
    REV_REV    = {  # FY2025 매출 (억원)
        "시몬스": 3239, "에이스침대": 3173, "코웨이 비렉스": 3654,
        "템퍼": 1229,  "씰리침대": 889,   "지누스": 590,
    }
    r_total = sum(REV_REV.values())  # 12,774억

    g_subset = {b: google_linked[b] for b in REV_BRANDS if b in google_linked and google_linked[b] > 0}
    g_total  = sum(g_subset.values())
    if g_total == 0:
        return src

    sos = {b: round(v / g_total * 100, 1) for b, v in g_subset.items()}
    som = {b: round(REV_REV[b] / r_total * 100, 1) for b in g_subset}

    # SOS_SOM_DATA 내 템퍼 항목 교체 (caution→False, sos/som 실값)
    import re
    tempur_sos = sos.get("템퍼")
    tempur_som = som.get("템퍼")
    if tempur_sos is None:
        return src

    # 기존 템퍼 caution 항목 패턴 교체
    old_pat = r'\{"brand":"템퍼","sos":null[^}]*"caution":true[^}]*\}'
    new_entry = (
        f'{{"brand":"템퍼","sos":{tempur_sos},"sos_total":null,"sos_cat":{tempur_sos},'
        f'"som":{tempur_som},"caution":false,"tier":"A","in_dart":true,'
        f'"is_simmons":false,"data_source":"DART_유한회사_추정★",'
        f'"som_note":"국내별도 추정★"}}'
    )
    patched, n = re.subn(old_pat, new_entry, src)
    if n > 0:
        # 시몬스 SoS도 업데이트
        sim_sos = sos.get("시몬스", 58.3)
        patched = re.sub(
            r'"brand":"시몬스","sos":\d+\.?\d*,"sos_total":\d+\.?\d*,"sos_cat":\d+\.?\d*,"som":\d+\.?\d*',
            f'"brand":"시몬스","sos":{sim_sos},"sos_total":8.5,"sos_cat":{sim_sos},"som":{som.get("시몬스", 25.4)}',
            patched, count=1
        )
        print(f"  → 템퍼 SoS={tempur_sos}% / SoM={tempur_som}% 실데이터 반영 완료")
        return patched
    return src


def main():
    print("[v2] 기존 리포트 로드...")
    with open(SRC_HTML, encoding="utf-8") as f:
        src = f.read()

    print("[v2] 블로그/뉴스 수집...")
    api_data = fetch_blog_news()

    print("[v2] 섹션 생성...")
    src = patch_sos_som_tempur(src)   # 템퍼 SoS 실데이터 반영 (수집됐을 때만 동작)
    detail_sec   = build_detail_section(api_data)
    revenue_sec  = build_revenue_section()
    price_sec    = build_price_section()

    # ① 매출 현황 → 가격 비교 순으로 main 최상단에 삽입
    top_anchor = '<div id="main">'
    if top_anchor in src:
        src = src.replace(
            top_anchor,
            top_anchor + "\n\n" + revenue_sec + "\n\n" + price_sec,
            1
        )
        print("  → 매출 현황 + 가격 비교 섹션: main 최상단 삽입 완료")
    else:
        src = src.replace("</body>", revenue_sec + "\n</body>")

    # ① -b  section-social(YouTube 구독자, 원본 직접조사 데이터)을 가격 비교 바로 뒤로 이동
    YT_START    = '\n\n  <!-- YouTube 구독자 섹션 -->'
    YT_END_MARK = '\n  <!-- 부록 섹션'
    yt_s = src.find(YT_START)
    yt_e = src.find(YT_END_MARK, yt_s) if yt_s != -1 else -1
    if yt_s != -1 and yt_e != -1:
        yt_block = src[yt_s:yt_e]
        src = src[:yt_s] + src[yt_e:]          # 원위치 제거
        kpi_pos = src.find('id="section-kpi"')  # price_sec 바로 다음 = kpi 직전
        if kpi_pos != -1:
            tag_open = src.rfind('\n  <div', 0, kpi_pos)
            src = src[:tag_open] + yt_block + '\n' + src[tag_open:]
            print("  → YouTube 구독자 섹션(원본): 가격 비교 뒤로 이동 완료")
        else:
            print("  ⚠ section-kpi 삽입 위치 없음 — YouTube 원위치 유지")
    else:
        print(f"  ⚠ section-social 탐색 실패 (s={yt_s}, e={yt_e})")

    # ② 상세 건수 → section-rank 바로 뒤 (⑦ 월별 추이 앞)에 삽입
    rank_anchor = "<!-- ⑦ 월별 추이 -->"
    if rank_anchor in src:
        src = src.replace(rank_anchor, detail_sec + "\n\n  " + rank_anchor)
        print("  → 상세 건수 섹션: section-rank 뒤 삽입 완료")
    else:
        print("  ⚠ ⑦ 앵커 없음 — </body> 앞에 추가")
        src = src.replace("</body>", detail_sec + "\n</body>")

    # ②-b  section-demo(성별/연령대)를 section-detail-counts 바로 아래로 이동
    #       (⑧ 주석부터 ① 주석 직전까지 추출 → ⑦ 월별 추이 주석 바로 앞에 삽입)
    #       반드시 ③ 이전에 실행 — ③이 ① 주석을 제거하므로 DEMO_END를 찾지 못하게 됨
    DEMO_START  = '\n\n  <!-- ⑧ 성별 / 연령대 (T2-6: 인덱스화 토글) -->'
    DEMO_END    = '\n\n  <!-- T2-3: SoS vs SoM 산점도 -->'
    DEMO_INSERT = '<!-- ⑦ 월별 추이 -->'

    dm_s = src.find(DEMO_START)
    dm_e = src.find(DEMO_END, dm_s) if dm_s != -1 else -1
    if dm_s != -1 and dm_e != -1:
        demo_block = src[dm_s:dm_e]
        src = src[:dm_s] + src[dm_e:]           # 원위치 제거
        ins = src.find(DEMO_INSERT)
        if ins != -1:
            src = src[:ins] + demo_block + '\n\n  ' + src[ins:]
            print("  → 성별/연령대 섹션: 상세 건수 바로 아래 이동 완료")
        else:
            print("  ⚠ ⑦ 월별추이 앵커 없음 — 원위치 유지")
            src = src[:dm_s] + demo_block + src[dm_s:]
    else:
        print(f"  ⚠ section-demo 탐색 실패 (s={dm_s}, e={dm_e})")

    # ②-c  section-trend(⑦ 월별 추이)를 ESOV(section-sos-som) 바로 아래로 이동
    #       ②-b 이후 ⑧이 제거된 상태이므로 TREND_END = T2-3 주석 사용
    TREND_START  = '\n\n  <!-- ⑦ 월별 추이 -->'
    TREND_END    = '\n\n  <!-- T2-3: SoS vs SoM 산점도 -->'

    tr_s = src.find(TREND_START)
    tr_e = src.find(TREND_END, tr_s) if tr_s != -1 else -1
    if tr_s != -1 and tr_e != -1:
        trend_block = src[tr_s:tr_e]
        src = src[:tr_s] + src[tr_e:]          # 원위치 제거
        # id="section-price-table" 앞에 삽입 (한글 주석 인코딩 우회)
        cv_pos = src.find('id="section-price-table"')
        if cv_pos != -1:
            ins = src.rfind('\n\n', 0, cv_pos)
            if ins == -1:
                ins = cv_pos
            src = src[:ins] + trend_block + src[ins:]
            print("  → 월별 추이 섹션: ESOV 산점도 아래로 이동 완료")
        else:
            print("  ⚠ section-price-table 앵커 없음 — 원위치 유지")
            src = src[:tr_s] + trend_block + src[tr_s:]
    else:
        print(f"  ⚠ section-trend 탐색 실패 (s={tr_s}, e={tr_e})")

    # ③ 임원 요약 3개 섹션(월별추이·포지셔닝·변화점)을 ESOV 산점도 바로 앞으로 이동
    MOVE_START    = '\n\n  <!-- ① - 월별 추이 (임원 요약용 — 상단 배치) -->'
    MOVE_END      = '\n\n  <!-- ⑤ Share of Search'
    INSERT_BEFORE = '<!-- T2-3: SoS vs SoM 산점도 -->'

    s_idx = src.find(MOVE_START)
    e_idx = src.find(MOVE_END, s_idx) if s_idx != -1 else -1
    if s_idx != -1 and e_idx != -1:
        block = src[s_idx:e_idx]
        src = src[:s_idx] + src[e_idx:]
        ins = src.find(INSERT_BEFORE)
        if ins != -1:
            src = src[:ins] + block + '\n\n  ' + src[ins:]
            print("  → 임원 요약 3섹션: ESOV 산점도 위로 이동 완료")
        else:
            print("  ⚠ T2-3 삽입 위치 없음 — 원위치 유지")
            src = src[:s_idx] + block + src[s_idx:]
    else:
        print(f"  ⚠ 이동 블록 탐색 실패 (s={s_idx}, e={e_idx})")

    # v2 전용: KPI 요약 카드 숨김 + 원본 가격 테이블 위치 숨김 (상단 복사본만 표시)
    src = src.replace(
        "</head>",
        "<style>#section-kpi{display:none!important;}"
        "#section-price-table{display:none!important;}</style>\n</head>",
        1
    )

    with open(DEST_HTML, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"\n[완료] {DEST_HTML}")
    return DEST_HTML


if __name__ == "__main__":
    path = main()
    import subprocess
    subprocess.Popen(["cmd", "/c", "start", "", path])
