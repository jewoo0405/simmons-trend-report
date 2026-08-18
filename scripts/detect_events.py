"""
scripts/detect_events.py
Google 검색 지수 급등/급락(±30% 이상) 구간 자동 탐지 → config/events.json 에 추가
"""
import json
import os
import glob
import sys

SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "snapshots")
EVENTS_JSON = os.path.join(os.path.dirname(__file__), "..", "config", "events.json")
THRESHOLD = 30.0  # ±30% 이상 변화를 이벤트로 탐지


def load_events():
    if os.path.exists(EVENTS_JSON):
        with open(EVENTS_JSON, encoding="utf-8") as f:
            return json.load(f).get("events", [])
    return []


def save_events(events):
    with open(EVENTS_JSON, "w", encoding="utf-8") as f:
        json.dump({"events": events}, f, ensure_ascii=False, indent=2)


def is_duplicate(events, brand, date):
    """동일 brand+date 조합의 auto_detected 이벤트가 이미 있으면 True"""
    for ev in events:
        if ev.get("brand") == brand and ev.get("date") == date and ev.get("type") == "auto_detected":
            return True
    return False


def detect():
    snap_files = sorted(glob.glob(os.path.join(SNAP_DIR, "*.json")))
    # KPI 스냅샷 파일 제외
    snap_files = [f for f in snap_files if "_kpi.json" not in f]

    if len(snap_files) < 2:
        print("[detect_events] 스냅샷이 2개 미만 — 탐지 불가")
        return

    existing_events = load_events()
    new_events = []

    # 각 스냅샷에서 monthly_series 추출하여 전월비 계산
    # 스냅샷 파일이 날짜 기반이므로, 월별로 집계
    monthly_data = {}  # brand -> {period: value}
    for fpath in snap_files:
        try:
            with open(fpath, encoding="utf-8") as f:
                snap = json.load(f)
        except Exception:
            continue
        ms = snap.get("google", {}).get("monthly_series", {})
        for brand, pts in ms.items():
            if brand not in monthly_data:
                monthly_data[brand] = {}
            for pt in pts:
                period = pt.get("period", "")[:7]  # YYYY-MM
                val = pt.get("value", 0)
                if period and val is not None:
                    monthly_data[brand][period] = val

    # 탐지: 전월 대비 ±THRESHOLD% 이상 변화
    detected_count = 0
    for brand, period_vals in monthly_data.items():
        periods = sorted(period_vals.keys())
        for i in range(1, len(periods)):
            prev_period = periods[i - 1]
            curr_period = periods[i]
            prev_val = period_vals[prev_period]
            curr_val = period_vals[curr_period]
            if prev_val == 0:
                continue
            pct_change = (curr_val - prev_val) / prev_val * 100
            if abs(pct_change) >= THRESHOLD:
                event_date = curr_period + "-01"
                if is_duplicate(existing_events, brand, event_date):
                    continue
                direction = "급등" if pct_change > 0 else "급락"
                label = f"{brand} 검색량 {direction} ({pct_change:+.1f}%)"
                new_events.append({
                    "date": event_date,
                    "brand": brand,
                    "type": "auto_detected",
                    "label": label,
                    "source": "추정",
                    "pct_change": round(pct_change, 1),
                })
                detected_count += 1

    if new_events:
        all_events = existing_events + new_events
        save_events(all_events)
        print(f"[detect_events] {detected_count}개 이벤트 후보 추가됨 → {EVENTS_JSON}")
    else:
        print(f"[detect_events] 새로운 이벤트 후보 없음 (기존 {len(existing_events)}개 유지)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    detect()
