# 키워드 버전 관리
KEYWORD_VERSION = "2026-08-v2"
KEYWORD_CHANGELOG = [
    {
        "version": "2026-08-v1",
        "date": "2026-08-18",
        "changes": "초기 정의"
    },
    {
        "version": "2026-08-v2",
        "date": "2026-08-18",
        "changes": "브랜드 간 형평성 확장 — 시몬스·씰리·에몬스·지누스·이케아·에이스침대 조합형 키워드 추가. 단독 에이스/ACE는 동음이의 위험으로 제외."
    }
]

TIER_NEW = {
    "A": {"label": "Tier A — 프리미엄 매트리스", "warning": None, "brands": ["시몬스", "씰리침대"]},
    "B": {"label": "Tier B — 매스 침대", "warning": None, "brands": ["에이스침대", "에몬스", "지누스"]},
    "C": {"label": "Tier C — 종합가구", "warning": "검색 지수에 가구·인테리어 수요 혼재. 직접 비교 주의.", "brands": ["한샘", "현대리바트", "까사미아", "일룸", "이케아"]},
    "D": {"label": "Tier D — 렌탈", "warning": "렌탈 사업 모델로 직접 비교 주의.", "brands": ["코웨이 비렉스"]},
}
BRAND_TO_TIER_NEW = {brand: k for k, v in TIER_NEW.items() for brand in v["brands"]}

BRANDS = [
    {"name": "시몬스",       "tier": 0, "baseline": True,  "category": "bed_specialist",   "trend_kw": "시몬스",        "naver_kw": "시몬스 침대",       "color": "#0b0b0b",
     "shop_kw": "시몬스 매트리스",    "youtube": "시몬스침대",         "instagram": "simmons_kr"},
    {"name": "에이스침대",   "tier": 1, "baseline": False, "category": "bed_specialist",   "trend_kw": "에이스침대",    "naver_kw": "에이스침대",         "color": "#e34948",
     "shop_kw": "에이스침대 매트리스", "youtube": "에이스침대",        "instagram": "acedotcom_official"},
    {"name": "씰리침대",     "tier": 1, "baseline": False, "category": "bed_specialist",   "trend_kw": "씰리침대",      "naver_kw": "씰리침대",           "color": "#1baf7a",
     "shop_kw": "씰리침대 매트리스",  "youtube": "씰리코리아",         "instagram": "sealy_korea"},
    {"name": "지누스",       "tier": 2, "baseline": False, "category": "bed_specialist",   "trend_kw": "지누스",         "naver_kw": "지누스 매트리스",    "color": "#008300",
     "shop_kw": "지누스 매트리스",    "youtube": "지누스코리아",       "instagram": "zinuskorea"},
    {"name": "코웨이 비렉스","tier": 2, "baseline": False, "category": "general_furniture","trend_kw": "코웨이 비렉스", "naver_kw": "코웨이 비렉스",      "color": "#2a78d6",
     "shop_kw": "비렉스 매트리스",    "youtube": "코웨이공식채널",     "instagram": "coway_official"},
    {"name": "한샘",         "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "한샘",           "naver_kw": "한샘 매트리스",      "color": "#199e70",
     "shop_kw": "한샘 매트리스",      "youtube": "한샘공식",           "instagram": "hansem_official"},
    {"name": "현대리바트",   "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "현대리바트",    "naver_kw": "현대리바트 침대",    "color": "#4a3aa7",
     "shop_kw": "현대리바트 침대",    "youtube": "현대리바트",         "instagram": "hyundailivart"},
    {"name": "까사미아",     "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "까사미아",      "naver_kw": "까사미아 침대",      "color": "#eb6834",
     "shop_kw": "까사미아 침대",      "youtube": "까사미아",           "instagram": "casamia_official"},
    {"name": "일룸",         "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "일룸",           "naver_kw": "일룸 침대",          "color": "#d95926",
     "shop_kw": "일룸 침대",          "youtube": "일룸공식",           "instagram": "iloom_official"},
    {"name": "에몬스",       "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "에몬스",         "naver_kw": "에몬스 가구",        "color": "#534ab7",
     "shop_kw": "에몬스 침대",        "youtube": "에몬스가구",         "instagram": "emons_furniture"},
    {"name": "이케아",       "tier": 3, "baseline": False, "category": "general_furniture","trend_kw": "이케아",         "naver_kw": "이케아 침대",        "color": "#378add",
     "shop_kw": "이케아 매트리스",    "youtube": "IKEA Korea",         "instagram": "ikea_korea"},
]

# 침대 전업 브랜드 집합 (P1-1 SoS 카테고리 기준 분모)
BED_SPECIALISTS = {b["name"] for b in BRANDS if b["category"] == "bed_specialist"}

TIER_LABELS = {
    0: "기준",
    1: "1군 · 직접 경쟁",
    2: "2군 · 대체 채널",
    3: "3군 · 종합 가구",
}

SIMMONS_TREND_KW = "시몬스"

# 네이버 데이터랩 배치 (시몬스를 모든 배치 첫 번째로 고정 = 앵커)
# DataLab은 배치 내 최댓값=100이므로, 시몬스 포함 시 per-batch 정규화로 비교 가능
DATALAB_BATCHES = [
    ["시몬스", "에이스침대", "씰리침대", "지누스", "코웨이 비렉스"],
    ["시몬스", "한샘", "현대리바트", "까사미아", "일룸"],
    ["시몬스", "에몬스", "이케아"],
]

# Google Trends 배치 — P0-2 체인 정규화 재설계 (2026-08-19)
# 목표: 모든 배치 max/min ≤ 20x, 시몬스를 주요 배치(A·B·C)에 공통 앵커로 포함
# 브리지 브랜드는 인접 배치에 중복 포함되어 스케일 연결 역할 수행
TREND_BATCHES = [
    ["시몬스", "일룸", "까사미아", "에이스침대", "지누스"],      # A: 중형 (시몬스 1차 앵커·시계열 기준), 예상 max/min ≈3x
    ["시몬스", "이케아", "한샘"],                               # B: 대형 (이케아 최대, 시몬스 브리지), 예상 max/min ≈7x
    ["시몬스", "에몬스"],                                       # C: 소형상위 (시몬스 앵커, 에몬스 브리지), 예상 max/min ≈7x
    ["에몬스", "현대리바트", "씰리침대"],                       # D: 소형하위 (에몬스 브리지), 예상 max/min ≈4x
    ["씰리침대", "코웨이 비렉스"],                              # E: 해상도 한계 (씰리침대 브리지), 예상 max/min ≈34x ※
]
TREND_BRIDGES = ["시몬스", "시몬스", "에몬스", "씰리침대"]  # A→B, B→C, C→D, D→E 브리지

# 배치 비고 (max/min 20x 달성 불가 배치 주석)
TREND_BATCH_NOTES = {
    "E": "코웨이 비렉스 측정 해상도 한계 (원본값 < 1). 예상 max/min ≈34x (20x 초과). P0-3 키워드 재검증 예정.",
}

# 네이버 데이터랩 키워드 그룹 (브랜드 표기 변형 통합)
KEYWORD_GROUPS = {
    "시몬스":       ["시몬스", "시몬스침대", "시몬스 침대", "시몬스 매트리스", "SIMMONS", "뷰티레스트"],
    "에이스침대":   ["에이스침대", "에이스 침대", "에이스 매트리스", "ACE침대"],
    "씰리침대":     ["씰리침대", "씰리 침대", "씰리 매트리스", "SEALY", "씰리", "Sealy"],
    "지누스":       ["지누스", "지누스 매트리스", "Zinus", "zinus", "지누스침대"],
    "코웨이 비렉스":["코웨이 비렉스", "비렉스", "코웨이 매트리스"],
    "한샘":         ["한샘 침대", "한샘 매트리스", "HANSEM"],  # '한샘' 단독 금지 — 카테고리 오염 | ⚠ HANSEM 위험도 중간 — IT회사 한샘과 혼동 가능
    "현대리바트":   ["현대리바트 침대", "리바트 침대", "리바트 매트리스"],
    "까사미아":     ["까사미아 침대", "까사미아 매트리스"],
    "일룸":         ["일룸 침대", "일룸 매트리스"],
    "에몬스":       ["에몬스", "에몬스 가구", "에몬스 침대", "EMONS", "에몬스침대"],
    "이케아":       ["이케아 침대", "이케아 매트리스", "IKEA"],    # '이케아' 단독 금지 — 카테고리 오염
}
