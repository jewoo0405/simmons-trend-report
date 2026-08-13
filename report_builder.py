from brand_config import BRANDS
from datetime import datetime


def _color(name):
    for b in BRANDS:
        if b["name"] == name:
            return b["color"]
    return "#888"


def _bar_chart(data_dict, title, max_val=100):
    """가로 막대 차트 HTML"""
    sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    rows = ""
    for rank, (name, val) in enumerate(sorted_items, 1):
        color = _color(name)
        width = round((val / max_val) * 100) if max_val else 0
        simmons_mark = " ★" if name == "시몬스" else ""
        bold = "font-weight:bold;" if name == "시몬스" else ""
        rows += f"""
        <tr>
          <td style="padding:5px 8px;font-size:13px;{bold}width:90px;white-space:nowrap;">
            {rank}. {name}{simmons_mark}
          </td>
          <td style="padding:5px 4px;width:100%;">
            <div style="background:#f0f0f0;border-radius:4px;height:20px;">
              <div style="background:{color};width:{width}%;height:20px;border-radius:4px;
                          display:flex;align-items:center;padding-left:6px;
                          min-width:30px;box-sizing:border-box;">
                <span style="color:#fff;font-size:11px;font-weight:bold;">{val}</span>
              </div>
            </div>
          </td>
        </tr>"""
    return f"""
    <div style="margin-bottom:24px;">
      <div style="font-size:14px;font-weight:bold;color:#1a1a2e;
                  border-left:4px solid #c8a96e;padding-left:10px;margin-bottom:12px;">
        {title}
      </div>
      <table style="width:100%;border-collapse:collapse;">{rows}</table>
    </div>"""


def _line_chart(monthly_data, periods):
    """SVG 라인 차트"""
    if not monthly_data or not periods:
        return "<p style='color:#999;font-size:13px;'>데이터 없음</p>"

    W, H, PAD_L, PAD_R, PAD_T, PAD_B = 560, 220, 50, 20, 20, 40
    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B
    n = len(periods)
    if n < 2:
        return "<p style='color:#999;font-size:13px;'>데이터 부족</p>"

    all_vals = [v for vals in monthly_data.values() for v in vals]
    max_v = max(all_vals) if all_vals else 100
    max_v = max(max_v, 1)

    def px(i, v):
        x = PAD_L + (i / (n - 1)) * chart_w
        y = PAD_T + chart_h - (v / max_v) * chart_h
        return x, y

    svg = f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">'

    # 격자선
    for step in [0, 25, 50, 75, 100]:
        y = PAD_T + chart_h - (step / 100) * chart_h
        svg += f'<line x1="{PAD_L}" y1="{y}" x2="{W-PAD_R}" y2="{y}" stroke="#eee" stroke-width="1"/>'
        svg += f'<text x="{PAD_L-4}" y="{y+4}" text-anchor="end" font-size="10" fill="#aaa">{step}</text>'

    # X축 레이블 (3개월마다)
    for i, p in enumerate(periods):
        if i % 3 == 0:
            x, _ = px(i, 0)
            label = p[-5:].replace("-", "/")
            svg += f'<text x="{x}" y="{H-6}" text-anchor="middle" font-size="10" fill="#888">{label}</text>'

    # 라인
    for brand, vals in monthly_data.items():
        color = _color(brand)
        points = " ".join(f"{px(i,v)[0]:.1f},{px(i,v)[1]:.1f}" for i, v in enumerate(vals))
        width = "2.5" if brand == "시몬스" else "1.5"
        svg += f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>'
        # 시몬스 점 강조
        if brand == "시몬스":
            for i, v in enumerate(vals):
                x, y = px(i, v)
                svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>'

    # 범례
    legend_x = PAD_L
    svg += f'<g transform="translate({legend_x},{H-20})">'
    offset = 0
    for brand in monthly_data:
        color = _color(brand)
        svg += f'<rect x="{offset}" y="0" width="10" height="10" fill="{color}"/>'
        svg += f'<text x="{offset+13}" y="9" font-size="11" fill="#555">{brand}</text>'
        offset += len(brand) * 8 + 24
    svg += '</g></svg>'
    return svg


def _comparison_table(google_norm, naver_norm):
    """구글 vs 네이버 순위 비교표"""
    g_rank = {n: i+1 for i, (n, _) in enumerate(sorted(google_norm.items(), key=lambda x: x[1], reverse=True))}
    n_rank = {n: i+1 for i, (n, _) in enumerate(sorted(naver_norm.items(), key=lambda x: x[1], reverse=True))}
    all_brands = sorted(set(g_rank) | set(n_rank), key=lambda x: g_rank.get(x, 99))

    rows = ""
    for name in all_brands:
        gr = g_rank.get(name, "-")
        nr = n_rank.get(name, "-")
        gv = google_norm.get(name, 0)
        nv = naver_norm.get(name, 0)
        bold = "font-weight:bold;background:#fffde7;" if name == "시몬스" else ""
        diff = ""
        if isinstance(gr, int) and isinstance(nr, int):
            d = gr - nr
            if d > 0:
                diff = f'<span style="color:#c62828;">▼{d}</span>'
            elif d < 0:
                diff = f'<span style="color:#2e7d32;">▲{abs(d)}</span>'
            else:
                diff = '<span style="color:#888;">-</span>'
        rows += f"""
        <tr style="{bold}">
          <td style="padding:8px 10px;font-size:13px;">{name}{"★" if name=="시몬스" else ""}</td>
          <td style="padding:8px 10px;text-align:center;font-size:13px;">{gr}위 ({gv})</td>
          <td style="padding:8px 10px;text-align:center;font-size:13px;">{nr}위 ({nv})</td>
          <td style="padding:8px 10px;text-align:center;font-size:13px;">{diff}</td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <tr style="background:#1a1a2e;color:#fff;">
        <th style="padding:10px;text-align:left;">브랜드</th>
        <th style="padding:10px;text-align:center;">구글 순위</th>
        <th style="padding:10px;text-align:center;">네이버 순위</th>
        <th style="padding:10px;text-align:center;">격차</th>
      </tr>
      {rows}
    </table>"""


def _simmons_summary(google_norm, naver_norm, report_month):
    """시몬스 포지셔닝 요약"""
    g_rank = sorted(google_norm.items(), key=lambda x: x[1], reverse=True)
    n_rank = sorted(naver_norm.items(), key=lambda x: x[1], reverse=True)
    g_pos = next((i+1 for i, (n, _) in enumerate(g_rank) if n == "시몬스"), "-")
    n_pos = next((i+1 for i, (n, _) in enumerate(n_rank) if n == "시몬스"), "-")
    g_top = g_rank[0][0] if g_rank else "-"
    n_top = n_rank[0][0] if n_rank else "-"

    return f"""
    <div style="background:#fffde7;border:1px solid #c8a96e;border-radius:6px;padding:16px 20px;margin-bottom:20px;">
      <div style="font-size:14px;font-weight:bold;color:#1a1a2e;margin-bottom:10px;">
        {report_month} 시몬스 포지셔닝 요약
      </div>
      <ul style="margin:0;padding-left:18px;font-size:13px;line-height:2;color:#333;">
        <li>구글 트렌드: 11개 브랜드 중 <b>{g_pos}위</b> (1위: {g_top})</li>
        <li>네이버 관심도: 11개 브랜드 중 <b>{n_pos}위</b> (1위: {n_top})</li>
        <li>구글 기준 시몬스 지수: <b>100</b> (자사 기준점)</li>
        <li>네이버 기준 시몬스 지수: <b>{naver_norm.get("시몬스", 0)}</b></li>
      </ul>
    </div>"""


def build_report(google_norm, naver_norm, naver_raw, monthly_data, periods, report_month):
    """최종 HTML 보고서 생성"""
    today = datetime.now().strftime("%Y.%m.%d %H:%M")
    g_max = max(google_norm.values()) if google_norm else 100
    n_max = max(naver_norm.values()) if naver_norm else 100

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>시몬스 브랜드 트렌드 보고서 — {report_month}</title>
<style>
  body{{margin:0;padding:16px 0;background:#eeeeee;font-family:Arial,sans-serif;color:#222;}}
  .wrap{{max-width:680px;margin:0 auto;}}
  .header{{background:#1a1a2e;padding:24px 28px;}}
  .header h1{{color:#fff;font-size:20px;margin:0 0 6px;}}
  .header p{{color:#aaa;font-size:12px;margin:0;}}
  .body{{background:#f9f9f9;padding:24px 28px;border:1px solid #e0e0e0;border-top:none;}}
  .section-title{{color:#1a1a2e;border-left:4px solid #c8a96e;padding-left:10px;
                  margin:28px 0 14px;font-size:15px;font-weight:bold;}}
  .footer-note{{background:#fff8e7;border:1px solid #c8a96e;padding:12px 16px;
                font-size:12px;color:#666;margin-top:24px;}}
  .footer-bar{{background:#1a1a2e;padding:12px 28px;text-align:center;}}
  .footer-bar span{{color:#888;font-size:12px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>시몬스 브랜드 경쟁 트렌드 보고서</h1>
    <p>{report_month} | 생성: {today} | 대상: 11개 브랜드</p>
  </div>
  <div class="body">

    <div class="section-title">포지셔닝 요약</div>
    {_simmons_summary(google_norm, naver_norm, report_month)}

    <div class="section-title">구글 트렌드 검색량 순위 (시몬스=100 기준)</div>
    <p style="font-size:12px;color:#888;margin:-8px 0 12px;">
      최근 3개월 한국 구글 검색 기준 상대 지수
    </p>
    {_bar_chart(google_norm, "구글 검색 관심도", max_val=g_max)}

    <div class="section-title">네이버 관심도 순위 (시몬스=100 기준)</div>
    <p style="font-size:12px;color:#888;margin:-8px 0 12px;">
      네이버 블로그+뉴스 결과 수 기반 추정 지수
    </p>
    {_bar_chart(naver_norm, "네이버 관심도", max_val=n_max)}

    <div class="section-title">구글 vs 네이버 순위 비교</div>
    <p style="font-size:12px;color:#888;margin:-8px 0 12px;">
      플랫폼별 순위 차이 — ▲은 네이버에서 더 높음, ▼은 낮음
    </p>
    {_comparison_table(google_norm, naver_norm)}

    <div class="section-title">최근 12개월 검색 트렌드 추이 (구글)</div>
    <p style="font-size:12px;color:#888;margin:-8px 0 12px;">
      시몬스 및 주요 경쟁사 5개 브랜드 월별 검색 추이
    </p>
    <div style="overflow-x:auto;">
      {_line_chart(monthly_data, periods)}
    </div>

    <div class="footer-note">
      본 보고서는 시몬스 CS팀 내부 공유용 자료입니다. 외부 유출을 삼가주세요.<br>
      데이터 출처: Google Trends (검색 지수) / Naver 검색 API (블로그+뉴스 건수)
    </div>
  </div>
  <div class="footer-bar">
    <span>SIMMONS KOREA · 브랜드 트렌드 자동 분석 시스템</span>
  </div>
</div>
</body>
</html>"""
    return html


def build_index(report_files):
    """index.html — 보고서 목록 페이지"""
    items = ""
    for fname, label in report_files:
        items += f"""
        <tr>
          <td style="padding:12px 16px;font-size:14px;">{label}</td>
          <td style="padding:12px 16px;text-align:right;">
            <a href="output/{fname}" style="background:#1a1a2e;color:#fff;padding:6px 14px;
               border-radius:4px;text-decoration:none;font-size:13px;">보고서 보기</a>
          </td>
        </tr>"""
    if not items:
        items = '<tr><td colspan="2" style="padding:20px;color:#999;text-align:center;">아직 생성된 보고서가 없습니다.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>시몬스 브랜드 트렌드 보고서</title>
<style>
  body{{margin:0;padding:24px 0;background:#eeeeee;font-family:Arial,sans-serif;}}
  .wrap{{max-width:680px;margin:0 auto;}}
  .header{{background:#1a1a2e;padding:24px 28px;}}
  .header h1{{color:#fff;font-size:20px;margin:0 0 4px;}}
  .header p{{color:#aaa;font-size:13px;margin:0;}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e0e0e0;}}
  tr{{border-bottom:1px solid #f0f0f0;}}
  tr:last-child{{border-bottom:none;}}
  .footer{{background:#1a1a2e;padding:12px 28px;text-align:center;}}
  .footer span{{color:#888;font-size:12px;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>시몬스 브랜드 트렌드 보고서</h1>
    <p>11개 브랜드 경쟁 분석 — 월간 자동 발행</p>
  </div>
  <table>{items}</table>
  <div class="footer"><span>SIMMONS KOREA · CS팀</span></div>
</div>
</body>
</html>"""
