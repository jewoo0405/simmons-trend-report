"""
데이터 품질 게이트 — 스펙 §15

수집 결과 JSON을 읽어 게이트 통과 여부를 판정합니다.
GitHub Actions에서 `python scripts/validate.py data/latest.json` 으로 호출.
게이트 통과 시 exit(0), 실패 시 exit(1).
"""
import json
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BRAND_COUNT = 11  # 브랜드 전체 수


def load_snapshot(path=None):
    if path is None:
        path = os.path.join(DATA_DIR, "latest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_previous(current_date):
    """전날 스냅샷 로드 (없으면 None)"""
    snap_dir = os.path.join(DATA_DIR, "snapshots")
    if not os.path.isdir(snap_dir):
        return None
    files = sorted(f for f in os.listdir(snap_dir) if f.endswith(".json"))
    # current_date 파일 이전 것 찾기
    prev_files = [f for f in files if f.replace(".json", "") < current_date]
    if not prev_files:
        return None
    prev_path = os.path.join(snap_dir, prev_files[-1])
    try:
        with open(prev_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def check_dod_change(current, previous, threshold=3.0):
    """전일 대비 이상 변동 검사 (threshold배 이상 변동 시 suspect)"""
    if not previous:
        return True  # 전일 없으면 통과
    curr_linked = current.get("google", {}).get("linked", {})
    prev_linked = previous.get("google", {}).get("linked", {})
    for brand, curr_val in curr_linked.items():
        prev_val = prev_linked.get(brand)
        if not prev_val or prev_val == 0:
            continue
        ratio = curr_val / prev_val
        if ratio > threshold or ratio < (1 / threshold):
            return False  # suspect
    return True


def run_gates(snapshot, previous=None):
    google = snapshot.get("google", {})
    linked = google.get("linked", {})
    batches = google.get("batches_raw", [])
    quality = snapshot.get("quality", {})
    sample_count = quality.get("sample_count", 0)

    results = []
    passed = True

    def gate(name, ok, critical=True, message=""):
        nonlocal passed
        status = "✓" if ok else ("✗" if critical else "⚠")
        if not ok and critical:
            passed = False
        results.append(f"  {status} {name}" + (f": {message}" if message else ""))

    # 게이트 1: 앵커 존재 (시몬스=100.0)
    simmons_val = linked.get("시몬스")
    gate("앵커 존재 (시몬스=100.0)", simmons_val == 100.0,
         message=f"현재값={simmons_val}")

    # 게이트 2: 브리지 유효 (raw >= 5)
    bridge_ok = True
    for batch in batches:
        bridge = batch.get("bridge")
        if bridge:
            raw = batch.get("raw_medians", {}).get(bridge, 0)
            if raw < 5:
                bridge_ok = False
                results.append(f"    브리지 '{bridge}' raw={raw:.1f} < 5")
    gate("브리지 유효 (raw≥5)", bridge_ok)

    # 게이트 3: 배치 비율 (max/min ≤ 20)
    ratio_ok = True
    for batch in batches:
        vals = [v for v in batch.get("raw_medians", {}).values() if v > 0]
        if vals:
            ratio = max(vals) / max(min(vals), 0.01)
            if ratio > 20:
                ratio_ok = False
                results.append(f"    배치{batch.get('label','')} 비율 {ratio:.1f}x > 20")
    gate("배치 비율 (max/min≤20)", ratio_ok)

    # 게이트 4: 브랜드 누락 없음
    found = len(linked)
    gate("브랜드 누락 없음",
         found >= BRAND_COUNT,
         message=f"{found}/{BRAND_COUNT}개")

    # 게이트 5: 전일 대비 이상 (3배 초과 → suspect, 실패 아님)
    dod_ok = check_dod_change(snapshot, previous)
    if not dod_ok:
        snapshot.setdefault("quality", {})["suspect"] = True
    gate("전일 대비 이상 (3배)", dod_ok, critical=False,
         message="suspect=True 기록됨" if not dod_ok else "")

    # 게이트 6: CV 계산 가능 (sample_count >= 3)
    gate("CV 계산 가능 (n≥3)",
         sample_count >= 3,
         critical=False,
         message=f"n={sample_count} (부족 시 '측정 불가' 표시)")

    # 경고 메시지
    for w in google.get("warnings", []):
        results.append(f"  ⚠ 경고: {w}")

    return passed, results, snapshot  # snapshot은 suspect 갱신 포함


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        snapshot = load_snapshot(path)
    except FileNotFoundError:
        print(f"[Validate] 파일 없음: {path or 'data/latest.json'}")
        sys.exit(1)

    collected_date = snapshot.get("collected_at", "")[:10]
    previous = load_previous(collected_date)

    print(f"\n[품질 게이트] {collected_date}")
    passed, results, updated_snapshot = run_gates(snapshot, previous)
    for line in results:
        print(line)

    # suspect 갱신된 경우 파일 재저장
    if updated_snapshot.get("quality", {}).get("suspect"):
        try:
            p = path or os.path.join(DATA_DIR, "latest.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(updated_snapshot, f, ensure_ascii=False, indent=2)
            print("  → suspect=True 기록 완료")
        except Exception as e:
            print(f"  → suspect 기록 실패: {e}")

    if passed:
        print("\n✓ 품질 게이트 통과\n")
        sys.exit(0)
    else:
        print("\n✗ 품질 게이트 실패 — 커밋 중단\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
