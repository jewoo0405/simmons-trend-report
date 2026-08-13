import os
import sys
import glob
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import db
from collector.google_collector import fetch_google_trends
from collector.naver_collector import fetch_naver_counts, fetch_naver_demographics
from analyzer.validator import overall_confidence_score
from analyzer.stats import share_of_search, detect_change_points, naver_google_gap
from builder.dashboard import build_dashboard

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def update_index():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "report_*.html")), reverse=True)
    items = ""
    for fp in files:
        fname = os.path.basename(fp)
        parts = fname.replace("report_", "").replace(".html", "").split("_")
        label = f"{parts[0]}년 {parts[1]}월 보고서" if len(parts) == 2 else fname
        items += f"""
        <tr>
          <td style="padding:12px 16px;font-size:14px;">{label}</td>
          <td style="padding:12px 16px;text-align:right;">
            <a href="output/{fname}" style="background:#1a1a2e;color:#fff;padding:6px 14px;
               border-radius:4px;text-decoration:none;font-size:13px;">대시보드 열기</a>
          </td>
        </tr>"""
    if not items:
        items = '<tr><td colspan="2" style="padding:20px;color:#999;text-align:center;">아직 생성된 보고서가 없습니다.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>시몬스 브랜드 트렌드 보고서</title>
<style>
  body{{margin:0;padding:24px 0;background:#eeeeee;font-family:'Malgun Gothic',Arial,sans-serif;}}
  .wrap{{max-width:700px;margin:0 auto;}}
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
    <p>11개 브랜드 경쟁 분석 — 월간 자동 발행 | 데스크톱 전용</p>
  </div>
  <table>{items}</table>
  <div class="footer"><span>SIMMONS KOREA · CS팀 · 내부 공유용</span></div>
</div>
</body>
</html>"""
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[인덱스] 갱신 완료 ({len(files)}개 보고서)")


def run():
    db.init_db()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    collected_at = datetime.now().strftime("%Y.%m.%d %H:%M")
    report_month = datetime.now().strftime("%Y년 %m월")

    print(f"\n{'='*50}")
    print(f"  시몬스 브랜드 트렌드 분석 시작")
    print(f"  run_id: {run_id}")
    print(f"{'='*50}\n")

    # 1. Google Trends 수집
    print("[1/4] Google Trends 수집 중...")
    google_data = fetch_google_trends(run_id, collected_at)

    # 2. Naver 수집
    print("\n[2/4] 네이버 관심도 수집 중...")
    naver_data = fetch_naver_counts(run_id, collected_at)

    # 3. 네이버 인구통계 (DataLab Playwright)
    print("\n[3/4] 네이버 성별·연령 수집 중...")
    demographics = fetch_naver_demographics(run_id, collected_at)

    # 4. 분석
    print("\n[4/4] 분석 중...")
    google_norm = google_data.get("normalized", {})
    naver_norm = naver_data.get("normalized", {})
    naver_stats = naver_data.get("stats", {})

    sos = share_of_search({k: v for k, v in google_norm.items() if v > 0} or naver_norm)

    # 변화점 탐지
    change_points = []
    monthly = google_data.get("monthly_series", {})
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

    gap = naver_google_gap(naver_norm, google_norm)

    # 신뢰도 점수
    all_stats = list(naver_stats.values())
    conf_score = overall_confidence_score(all_stats)
    print(f"  신뢰도 점수: {conf_score}점")

    # 전체 데이터 묶음
    payload = {
        "google": google_data,
        "naver": naver_data,
        "demographics": demographics,
        "sos": sos,
        "gap": gap,
        "change_points": change_points,
        "meta": {
            "run_id": run_id,
            "collected_at": collected_at,
            "confidence_score": conf_score,
        }
    }

    # 보고서 생성
    html = build_dashboard(payload, report_month, collected_at, conf_score)
    fname = f"report_{datetime.now().strftime('%Y_%m')}.html"
    fpath = os.path.join(OUTPUT_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[보고서] 저장: {fpath}")

    update_index()
    print(f"\n완료! 신뢰도: {conf_score}점")


if __name__ == "__main__":
    run()
