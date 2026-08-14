"""
DART OpenAPI 매출 연동 — §13

https://opendart.fss.or.kr/api/fnlttSinglAcnt.json
API 키 없으면 조용히 건너뜀.

corp_code 매핑: DART에서 corpCode.xml을 받아 확인한 값.
⚠ 표시 = 종합 가구·렌탈 등 침대 외 사업 포함 — 차트에 각주 필수.
"""
import os
import json
import urllib.request
import urllib.parse

DART_API_KEY = os.getenv("DART_API_KEY")
DART_BASE_URL = "https://opendart.fss.or.kr/api"

# corp_code 매핑 (1회성 작업, 하드코딩)
# DART corpCode.xml → 브랜드 회사명으로 검색하여 확인
DART_CORP = {
    "에이스침대": {
        "code": "00133729",
        "report_code": "11011",  # 사업보고서
        "note": "매트리스 전업",
        "caution": False,
    },
    "한샘": {
        "code": "00213737",
        "report_code": "11011",
        "note": "종합 가구 — 침대·매트리스는 일부 사업부",
        "caution": True,
    },
    "현대리바트": {
        "code": "00155217",
        "report_code": "11011",
        "note": "종합 가구 — 침대 외 사업 포함",
        "caution": True,
    },
    "일룸": {
        "code": "01160621",
        "report_code": "11011",
        "note": "종합 가구",
        "caution": True,
    },
    # 비공개 또는 유한회사 — DART 공시 없음
    "시몬스": {
        "code": None,
        "note": "비상장 — 감사보고서(개별)만 존재, DART 공시 미확인",
        "caution": False,
    },
    "이케아": {
        "code": None,
        "note": "유한회사 이케아코리아 — 별도 감사보고서 확인 필요",
        "caution": True,
    },
    # 상장사 중 확인 필요 (corp_code 미확인)
    "씰리침대": {"code": None, "note": "상장사 여부 확인 필요"},
    "지누스": {"code": "00955711", "note": "코스피 상장", "caution": False},
    "까사미아": {"code": None, "note": "확인 필요"},
    "에몬스": {"code": None, "note": "확인 필요"},
    "코웨이 비렉스": {"code": "00254900", "note": "코웨이(주) 전체 — 비렉스 분리 불가", "caution": True},
}


def _dart_get(endpoint, params):
    params["crtfc_key"] = DART_API_KEY
    url = f"{DART_BASE_URL}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        raise ValueError(f"DART API 오류: {e}")


def _fetch_revenue(corp_code, bsns_year):
    """단일 재무제표에서 매출액 추출"""
    data = _dart_get("fnlttSinglAcnt.json", {
        "corp_code": corp_code,
        "bsns_year": str(bsns_year),
        "reprt_code": "11011",  # 사업보고서
        "fs_div": "CFS",        # 연결재무제표
    })
    if data.get("status") != "000":
        # 연결 없으면 별도재무제표 시도
        data = _dart_get("fnlttSinglAcnt.json", {
            "corp_code": corp_code,
            "bsns_year": str(bsns_year),
            "reprt_code": "11011",
            "fs_div": "OFS",
        })
    if data.get("status") != "000":
        return None

    for item in data.get("list", []):
        if item.get("account_nm") in ("매출액", "수익(매출액)", "영업수익"):
            try:
                return {
                    "year": bsns_year,
                    "amount": int(item.get("thstrm_amount", "0").replace(",", "")),
                    "unit": "원",
                    "caution": DART_CORP.get("", {}).get("caution", False),
                }
            except (ValueError, TypeError):
                pass
    return None


def fetch_dart_revenues(target_year=None):
    """
    브랜드별 최근 매출액 수집.
    Returns: {brand: {year, amount, unit, caution}} or {} if no API key.
    """
    if not DART_API_KEY:
        print("  [DART] API 키 없음 (DART_API_KEY 미설정) — 건너뜀")
        return {}

    from datetime import datetime
    year = target_year or (datetime.now().year - 1)  # 전년도 사업보고서
    print(f"  [DART] {year}년 사업보고서 수집 중...")

    revenues = {}
    for brand, info in DART_CORP.items():
        code = info.get("code")
        if not code:
            print(f"    {brand}: corp_code 미확인 — 건너뜀")
            continue
        try:
            rev = _fetch_revenue(code, year)
            if rev:
                rev["caution"] = info.get("caution", False)
                rev["note"] = info.get("note", "")
                revenues[brand] = rev
                amount_b = rev["amount"] // 100_000_000
                caution_mark = " ⚠" if rev["caution"] else ""
                print(f"    {brand}: {amount_b}억원{caution_mark}")
            else:
                print(f"    {brand}: 매출액 항목 없음")
        except ValueError as e:
            print(f"    {brand}: {e}")

    return revenues
