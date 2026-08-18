import os
import sys
import glob
import json

# events.json 로드 함수
def _load_events():
    events_path = os.path.join(os.path.dirname(__file__), "config", "events.json")
    try:
        with open(events_path, encoding="utf-8") as f:
            return json.load(f).get("events", [])
    except Exception:
        return []

# Windows 콘솔 UTF-8 강제
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import db
from collector.google_collector import fetch_google_trends
from collector.naver_collector import fetch_naver_counts, fetch_naver_demographics
from collector.naver_datalab_api import fetch_datalab_trends
from collector.dart_collector import fetch_dart_revenues
from collector.commentary import generate_commentary
from analyzer.validator import overall_confidence_score
from analyzer.stats import share_of_search, detect_change_points, naver_google_gap
from builder.dashboard import build_dashboard
from brand_config import KEYWORD_VERSION

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SNAP_DIR = os.path.join(DATA_DIR, "snapshots")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SNAP_DIR, exist_ok=True)


def save_history(snapshot: dict, report_month: str):
    """data/history/YYYY_MM.json 에 누적 저장 (덮어쓰지 않음)"""
    hist_dir = os.path.join(os.path.dirname(__file__), "data", "history")
    os.makedirs(hist_dir, exist_ok=True)
    # report_month 예: "2026년 08월" → "2026_08"
    month_key = report_month.replace("년 ", "_").replace("월", "").strip()
    hist_path = os.path.join(hist_dir, f"{month_key}.json")
    if not os.path.exists(hist_path):   # 이미 있으면 덮어쓰지 않음
        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"[history] 저장: {hist_path}")
    else:
        print(f"[history] 이미 존재: {hist_path} (스킵)")


def save_snapshot(payload, collected_date):
    """
    data/snapshots/{date}.json 에 수집 결과 저장.
    절대 덮어쓰지 않음 (날짜가 같아도 기존 파일 보존).
    data/latest.json 은 항상 최신으로 갱신.
    """
    snap_path = os.path.join(SNAP_DIR, f"{collected_date}.json")

    # 스냅샷 파일은 덮어쓰지 않음
    if not os.path.exists(snap_path):
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[스냅샷] 저장: {snap_path}")
    else:
        print(f"[스냅샷] 이미 존재: {snap_path} (건너뜀)")

    # latest.json 갱신
    latest_path = os.path.join(DATA_DIR, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[스냅샷] latest.json 갱신")


def build_snapshot_payload(run_id, collected_at, google_data, naver_data,
                           demographics, naver_stats, gap, conf_score,
                           datalab_data=None, dart_data=None):
    """스냅샷 JSON 스키마 (§14-1) 구성"""
    # linked = 시몬스=100 재정규화 완료값 (스펙 §14-1 스키마 준수)
    google_linked = google_data.get("normalized", {})
    google_batches = google_data.get("batches_raw", [])
    google_warnings = google_data.get("warnings", [])

    # 네이버 검색 API 결과
    naver_search = {}
    for b_name, stats in naver_stats.items():
        naver_search[b_name] = {"blog_news_total": stats.get("median", 0)}

    # CV 품질 정보
    cv_map = {name: s.get("cv", 0) for name, s in naver_stats.items()}
    outliers_removed = sum(s.get("outliers_removed", 0) for s in naver_stats.values())

    return {
        "collected_at": collected_at,
        "baseline": "시몬스",
        "run_id": run_id,
        "google": {
            "batches": google_batches,
            "linked": google_linked,
            "normalized": google_data.get("normalized", {}),
            "warnings": google_warnings,
            "monthly_series": google_data.get("monthly_series", {}),
            "periods": google_data.get("periods", []),
        },
        "naver_datalab_trend": datalab_data or {},
        "naver_datalab": demographics,
        "naver_search": naver_search,
        "dart": dart_data or {},
        "gap": gap,
        "keyword_version": KEYWORD_VERSION,  # 이 수집에 사용된 키워드 버전
        "quality": {
            "cv": cv_map,
            "confidence_score": conf_score,
            "sample_count": 3,  # naver N_SAMPLES
            "outliers_removed": outliers_removed,
            "suspect": False,
        }
    }


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
            <a href="output/{fname}" style="background:#0b0b0b;color:#fff;padding:6px 14px;
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
  .header{{background:#0b0b0b;padding:24px 28px;border-bottom:3px solid #c8a96e;}}
  .header h1{{color:#fff;font-size:20px;margin:0 0 4px;}}
  .header p{{color:#aaa;font-size:13px;margin:0;}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e0e0e0;}}
  tr{{border-bottom:1px solid #f0f0f0;}}
  tr:last-child{{border-bottom:none;}}
  .footer{{background:#0b0b0b;padding:12px 28px;text-align:center;}}
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
    collected_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    collected_date = datetime.now().strftime("%Y-%m-%d")
    report_month = datetime.now().strftime("%Y년 %m월")
    collected_display = datetime.now().strftime("%Y.%m.%d %H:%M")

    print(f"\n{'='*50}")
    print(f"  시몬스 브랜드 트렌드 분석 시작")
    print(f"  run_id: {run_id}")
    print(f"{'='*50}\n")

    # 1. Google Trends 수집
    print("[1/6] Google Trends 수집 중...")
    google_data = fetch_google_trends(run_id, collected_at)

    # 2. Naver 검색 지수 수집
    print("\n[2/6] 네이버 관심도 수집 중...")
    naver_data = fetch_naver_counts(run_id, collected_at)

    # 3. DataLab 검색어트렌드 수집 (§12)
    print("\n[3/6] DataLab 검색어트렌드 수집 중...")
    datalab_data = fetch_datalab_trends(run_id, collected_at)

    # 4. 네이버 인구통계 (DataLab API 우선, Playwright 폴백)
    print("\n[4/6] 네이버 성별·연령 수집 중...")
    demographics = fetch_naver_demographics(run_id, collected_at)

    # 5. 매출 수집 (네이버 증권 스크래핑)
    print("\n[5/6] 매출 수집 중 (네이버 증권)...")
    dart_data = fetch_dart_revenues()

    # 6. 분석
    print("\n[6/6] 분석 중...")
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

    # 구글 경고 출력
    for w in google_data.get("warnings", []):
        print(f"  ⚠ Google 경고: {w}")

    # ── 스냅샷 저장 (§14-1) ───────────────────────────────────────
    snapshot = build_snapshot_payload(
        run_id, collected_at, google_data, naver_data,
        demographics, naver_stats, gap, conf_score,
        datalab_data=datalab_data, dart_data=dart_data,
    )
    save_snapshot(snapshot, collected_date)
    save_history(snapshot, report_month)

    # ── AI 코멘터리 생성 (§16) ────────────────────────────────────
    print("\n[AI] 임원 브리핑 생성 중...")
    commentary = generate_commentary(snapshot)

    # ── 이벤트 로드 ────────────────────────────────────────────────
    events = _load_events()

    # ── 대시보드 데이터 조립 ───────────────────────────────────────
    payload = {
        "google": google_data,
        "naver": naver_data,
        "datalab": datalab_data,
        "demographics": demographics,
        "dart": dart_data,
        "commentary": commentary,
        "sos": sos,
        "gap": gap,
        "change_points": change_points,
        "events": events,
        "meta": {
            "run_id": run_id,
            "collected_at": collected_display,
            "confidence_score": conf_score,
        }
    }

    # 보고서 생성
    html = build_dashboard(payload, report_month, collected_display, conf_score)
    fname = f"report_{datetime.now().strftime('%Y_%m')}.html"
    fpath = os.path.join(OUTPUT_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[보고서] 저장: {fpath}")

    update_index()
    print(f"\n완료! 신뢰도: {conf_score}점")


if __name__ == "__main__":
    run()
