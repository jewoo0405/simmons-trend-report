import json
from brand_config import BRANDS
from analyzer.validator import overall_confidence_score


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

    conf_color = "#2e7d32" if confidence_score >= 70 else "#e65100" if confidence_score >= 40 else "#c62828"
    conf_label = "안정" if confidence_score >= 70 else "주의" if confidence_score >= 40 else "불안정"

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
  background:#1a1a2e;color:#fff;
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

/* 레이아웃 */
#layout{{display:flex;height:calc(100vh - 52px);}}

/* 좌측 사이드바 */
#sidebar{{
  width:220px;min-width:220px;background:#fff;
  border-right:1px solid #e0e0e0;overflow-y:auto;padding:16px 12px;
}}
#sidebar h3{{font-size:12px;color:#888;text-transform:uppercase;
             letter-spacing:1px;margin:16px 0 8px;padding-bottom:4px;
             border-bottom:1px solid #eee;}}
.brand-item{{
  display:flex;align-items:center;gap:8px;padding:5px 4px;
  border-radius:4px;cursor:pointer;font-size:13px;transition:background 0.15s;
}}
.brand-item:hover{{background:#f5f5f5;}}
.brand-item.active{{background:#e8eaf6;font-weight:bold;}}
.brand-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
.filter-btn{{
  display:block;width:100%;padding:6px 10px;margin-bottom:6px;
  border:1px solid #ddd;border-radius:4px;background:#fff;
  font-size:12px;cursor:pointer;text-align:left;transition:all 0.15s;
}}
.filter-btn:hover,.filter-btn.active{{background:#1a1a2e;color:#fff;border-color:#1a1a2e;}}

/* 중앙 차트 영역 */
#main{{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:16px;}}

/* 우측 인사이트 패널 */
#insight-panel{{
  width:280px;min-width:280px;background:#fff;
  border-left:1px solid #e0e0e0;overflow-y:auto;padding:16px;
}}
#insight-panel h3{{font-size:13px;font-weight:bold;color:#1a1a2e;
                   border-left:3px solid #c8a96e;padding-left:8px;margin-bottom:12px;}}

/* 차트 카드 */
.chart-row{{display:grid;gap:16px;}}
.chart-row.col2{{grid-template-columns:1fr 1fr;}}
.chart-row.col3{{grid-template-columns:1fr 1fr 1fr;}}
.card{{background:#fff;border-radius:8px;border:1px solid #e0e0e0;padding:16px;}}
.card-title{{font-size:13px;font-weight:bold;color:#1a1a2e;margin-bottom:4px;}}
.card-sub{{font-size:11px;color:#888;margin-bottom:12px;}}
.source-badge{{
  display:inline-block;font-size:10px;padding:2px 6px;border-radius:4px;
  margin-left:6px;font-weight:normal;
}}
.badge-google{{background:#e8f5e9;color:#2e7d32;}}
.badge-naver{{background:#e3f2fd;color:#1565c0;}}
.badge-no-demo{{background:#fff3e0;color:#e65100;}}

/* 인사이트 아이템 */
.insight-item{{
  padding:10px;border-radius:6px;background:#f9f9f9;
  margin-bottom:8px;font-size:12px;line-height:1.6;
}}
.insight-item.warn{{background:#fff3e0;border-left:3px solid #e65100;}}
.insight-item.good{{background:#e8f5e9;border-left:3px solid #2e7d32;}}

/* CV 신뢰도 색상 */
.cv-stable{{color:#2e7d32;font-weight:bold;}}
.cv-warning{{color:#e65100;font-weight:bold;}}
.cv-unstable{{color:#c62828;font-weight:bold;}}

/* 데이터 테이블 */
.data-table{{width:100%;border-collapse:collapse;font-size:12px;}}
.data-table th{{background:#1a1a2e;color:#fff;padding:7px 10px;text-align:left;}}
.data-table td{{padding:7px 10px;border-bottom:1px solid #f0f0f0;}}
.data-table tr:hover td{{background:#f9f9f9;}}

/* 인구통계 없음 */
.no-data{{text-align:center;padding:30px;color:#aaa;font-size:13px;}}
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

<!-- 중앙 차트 -->
<div id="main">

  <!-- Row 1: 구글 순위 + 네이버 순위 -->
  <div class="chart-row col2">
    <div class="card">
      <div class="card-title">구글 검색 지수 순위
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub">시몬스=100 기준 · 최근 3개월 한국</div>
      <div id="chart-google-rank" style="height:300px;"></div>
    </div>
    <div class="card">
      <div class="card-title">네이버 관심도 순위
        <span class="source-badge badge-naver">Naver Search</span>
      </div>
      <div class="card-sub">시몬스=100 기준 · 블로그+뉴스 건수</div>
      <div id="chart-naver-rank" style="height:300px;"></div>
    </div>
  </div>

  <!-- Row 2: 월별 추이 -->
  <div class="chart-row">
    <div class="card">
      <div class="card-title">월별 검색 트렌드 추이
        <span class="source-badge badge-google">Google Trends</span>
      </div>
      <div class="card-sub">주요 5개 브랜드 · 음영은 신뢰구간(CV)</div>
      <div id="chart-monthly" style="height:280px;"></div>
    </div>
  </div>

  <!-- Row 3: Share of Search + 갭 분석 -->
  <div class="chart-row col2">
    <div class="card">
      <div class="card-title">Share of Search</div>
      <div class="card-sub">브랜드별 검색 점유율 (%)</div>
      <div id="chart-sos" style="height:260px;"></div>
    </div>
    <div class="card">
      <div class="card-title">구글 vs 네이버 갭 분석</div>
      <div class="card-sub">플랫폼 간 순위 차이 — 차이 클수록 전략 검토 필요</div>
      <div id="chart-gap" style="height:260px;"></div>
    </div>
  </div>

  <!-- Row 4: 인구통계 -->
  <div class="chart-row col2">
    <div class="card">
      <div class="card-title">성별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div class="card-sub">주요 4개 브랜드 성별 비교</div>
      <div id="chart-gender" style="height:260px;"></div>
    </div>
    <div class="card">
      <div class="card-title">연령대별 검색 관심도
        <span class="source-badge badge-naver">Naver DataLab</span>
      </div>
      <div class="card-sub">주요 4개 브랜드 연령대 비교</div>
      <div id="chart-age" style="height:260px;"></div>
    </div>
  </div>

  <!-- Row 5: 신뢰도 테이블 -->
  <div class="chart-row">
    <div class="card">
      <div class="card-title">데이터 신뢰도 상세 (CV 분석)</div>
      <div class="card-sub">CV≤0.05 안정(녹) · CV≤0.15 주의(주황) · CV>0.15 불안정(빨강)</div>
      <div id="cv-table"></div>
    </div>
  </div>

</div><!-- /main -->

<!-- 우측 인사이트 패널 -->
<div id="insight-panel">
  <h3>시몬스 포지셔닝</h3>
  <div id="insight-simmons"></div>

  <h3 style="margin-top:16px;">주요 발견</h3>
  <div id="insight-findings"></div>

  <h3 style="margin-top:16px;">변화점</h3>
  <div id="insight-changes"></div>
</div>

</div><!-- /layout -->

<script>
const RAW = {data_json};
const COLORS = {colors_json};

// 브랜드 목록 렌더
const brandList = document.getElementById('brand-list');
Object.entries(COLORS).forEach(([name, color]) => {{
  const el = document.createElement('div');
  el.className = 'brand-item';
  el.innerHTML = `<div class="brand-dot" style="background:${{color}}"></div>${{name}}`;
  brandList.appendChild(el);
}});

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
        return {{value:x[1],itemStyle:{{color:COLORS[x[0]]||'#888',
          opacity: x[0]==='시몬스' ? 1 : 0.75}}}}
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
        return {{value:x[1],itemStyle:{{color:COLORS[x[0]]||'#888',
          opacity: x[0]==='시몬스' ? 1 : 0.75}}}}
      }}),
      label:{{show:true,position:'right',fontSize:11,formatter:p=>p.value}}
    }}],
    tooltip:{{trigger:'axis',formatter:p=>`${{p[0].name}}: ${{p[0].value}} (시몬스=100)`}}
  }});
}}

// 3. 월별 추이 (CV 밴드 포함)
function renderMonthly() {{
  const ms = RAW.google?.monthly_series || {{}};
  const periods = RAW.google?.periods || [];
  if(!Object.keys(ms).length) return;
  const series = [];
  Object.entries(ms).forEach(([brand, pts]) => {{
    const vals = pts.map(p=>p.value);
    const color = COLORS[brand] || '#888';
    series.push({{
      name:brand, type:'line', data:vals,
      lineStyle:{{color,width: brand==='시몬스'?3:1.5}},
      itemStyle:{{color}},
      symbol: brand==='시몬스'?'circle':'none',
      symbolSize:5,
      tooltip:{{formatter: (p) => {{
        const pt = pts[p.dataIndex];
        return `${{brand}}<br>${{p.name}}: ${{pt.value}}<br>CV: ${{pt.cv}} (${{pt.confidence}})`;
      }}}}
    }});
  }});
  const pLabels = periods.map(p=>p.substring(0,7));
  gc('chart-monthly').setOption({{
    legend:{{data:Object.keys(ms),bottom:0,textStyle:{{fontSize:11}}}},
    grid:{{left:40,right:20,top:10,bottom:40}},
    xAxis:{{type:'category',data:pLabels,axisLabel:{{fontSize:10,rotate:30}}}},
    yAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis'}}
  }});
}}

// 4. Share of Search 파이차트
function renderSoS() {{
  const sos = RAW.sos || {{}};
  const data = Object.entries(sos)
    .sort((a,b)=>b[1]-a[1])
    .map(([name,val])=>({{name,value:val,itemStyle:{{color:COLORS[name]||'#888'}}}}));
  gc('chart-sos').setOption({{
    tooltip:{{trigger:'item',formatter:p=>`${{p.name}}: ${{p.value}}%`}},
    legend:{{orient:'vertical',right:0,top:'center',textStyle:{{fontSize:11}}}},
    series:[{{
      type:'pie',radius:['40%','70%'],center:['40%','50%'],
      label:{{show:false}},data
    }}]
  }});
}}

// 5. 갭 분석 바차트
function renderGap() {{
  const gaps = RAW.gap || [];
  const sorted = gaps.slice(0,8);
  gc('chart-gap').setOption({{
    grid:{{left:90,right:20,top:10,bottom:10}},
    xAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:sorted.map(x=>x.brand),axisLabel:{{fontSize:11}}}},
    series:[{{
      type:'bar',
      data:sorted.map(x=>{{
        const color = x.gap > 0 ? '#1565c0' : '#c62828';
        return {{value:x.gap,itemStyle:{{color}}}};
      }}),
      label:{{show:true,position:'right',fontSize:11,
              formatter:p=>p.value>0?`+${{p.value}}`:`${{p.value}}`}}
    }}],
    tooltip:{{formatter:p=>`${{p.name}}<br>네이버-구글: ${{p.value>0?'+':''}}${{p.value}}`}}
  }});
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
  const series = genders.map(g=>{{
    return {{
      name:g, type:'bar',
      data:brands.map(b=>demo[b].gender[g]||0),
      itemStyle:{{color: g==='여성'?'#e91e63':'#1565c0'}}
    }};
  }});
  gc('chart-gender').setOption({{
    legend:{{data:genders,bottom:0}},
    grid:{{left:80,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis'}}
  }});
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
  const series = ages.map((age,i)=>{{
    return {{
      name:age, type:'bar', stack:'total',
      data:brands.map(b=>demo[b].age[age]||0),
      itemStyle:{{color:ageColors[i]}}
    }};
  }});
  gc('chart-age').setOption({{
    legend:{{data:ages,bottom:0,textStyle:{{fontSize:10}}}},
    grid:{{left:80,right:20,top:10,bottom:40}},
    xAxis:{{type:'value',axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'category',data:brands,axisLabel:{{fontSize:11}}}},
    series,
    tooltip:{{trigger:'axis'}}
  }});
}}

// 8. CV 신뢰도 테이블
function renderCVTable() {{
  const stats = RAW.naver?.stats || {{}};
  const rows = Object.entries(stats).map(([name,s])=>{{
    const cls = s.confidence==='stable'?'cv-stable':s.confidence==='warning'?'cv-warning':'cv-unstable';
    const label = s.confidence==='stable'?'안정':s.confidence==='warning'?'주의':'불안정';
    return `<tr>
      <td>${{name}}</td>
      <td>${{s.median}}</td>
      <td class="${{cls}}">${{(s.cv*100).toFixed(1)}}%</td>
      <td class="${{cls}}">${{label}}</td>
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

// 9. 인사이트 패널
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

function exportCSV() {{
  const norm_g = RAW.google?.normalized || {{}};
  const norm_n = RAW.naver?.normalized || {{}};
  const sos = RAW.sos || {{}};
  const rows = [['브랜드','구글 지수','네이버 지수','SoS(%)']];
  Object.keys({{...norm_g,...norm_n}}).forEach(name=>{{
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
renderSoS();
renderGap();
renderGender();
renderAge();
renderCVTable();
renderInsights();

window.addEventListener('resize', ()=>{{
  ['chart-google-rank','chart-naver-rank','chart-monthly',
   'chart-sos','chart-gap','chart-gender','chart-age']
  .forEach(id=>{{const el=document.getElementById(id);if(el&&el._echarts_instance_)echarts.getInstanceByDom(el)?.resize();}});
}});
</script>
</body>
</html>"""
    return html
