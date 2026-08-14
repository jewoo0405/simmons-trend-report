BRANDS = [
    {"name": "시몬스",       "tier": 0, "baseline": True,  "trend_kw": "시몬스",        "naver_kw": "시몬스 침대",       "color": "#0b0b0b"},
    {"name": "에이스침대",   "tier": 1, "baseline": False, "trend_kw": "에이스침대",    "naver_kw": "에이스침대",         "color": "#e34948"},
    {"name": "씰리침대",     "tier": 1, "baseline": False, "trend_kw": "씰리침대",      "naver_kw": "씰리침대",           "color": "#1baf7a"},
    {"name": "지누스",       "tier": 2, "baseline": False, "trend_kw": "지누스",         "naver_kw": "지누스 매트리스",    "color": "#008300"},
    {"name": "코웨이 비렉스","tier": 2, "baseline": False, "trend_kw": "코웨이 비렉스", "naver_kw": "코웨이 비렉스",      "color": "#2a78d6"},
    {"name": "한샘",         "tier": 3, "baseline": False, "trend_kw": "한샘",           "naver_kw": "한샘 매트리스",      "color": "#199e70"},
    {"name": "현대리바트",   "tier": 3, "baseline": False, "trend_kw": "현대리바트",    "naver_kw": "현대리바트 침대",    "color": "#4a3aa7"},
    {"name": "까사미아",     "tier": 3, "baseline": False, "trend_kw": "까사미아",      "naver_kw": "까사미아 침대",      "color": "#eb6834"},
    {"name": "일룸",         "tier": 3, "baseline": False, "trend_kw": "일룸",           "naver_kw": "일룸 침대",          "color": "#d95926"},
    {"name": "에몬스",       "tier": 3, "baseline": False, "trend_kw": "에몬스",         "naver_kw": "에몬스 가구",        "color": "#534ab7"},
    {"name": "이케아",       "tier": 3, "baseline": False, "trend_kw": "이케아",         "naver_kw": "이케아 침대",        "color": "#378add"},
]

TIER_LABELS = {
    0: "기준",
    1: "1군 · 직접 경쟁",
    2: "2군 · 대체 채널",
    3: "3군 · 종합 가구",
}

# Google Trends 그룹 (최대 5개, 시몬스 기준점으로 매 그룹 포함)
TREND_GROUPS = [
    ["시몬스", "에이스침대", "씰리침대", "지누스", "코웨이 비렉스"],
    ["시몬스", "한샘", "현대리바트", "까사미아", "일룸"],
    ["시몬스", "에몬스", "이케아"],
]

SIMMONS_TREND_KW = "시몬스"

# 네이버 데이터랩 키워드 그룹 (브랜드 표기 변형 통합)
KEYWORD_GROUPS = {
    "시몬스":       ["시몬스", "시몬스침대", "시몬스 침대", "시몬스 매트리스", "SIMMONS", "뷰티레스트"],
    "에이스침대":   ["에이스침대", "에이스 침대", "에이스 매트리스", "ACE침대"],
    "씰리침대":     ["씰리침대", "씰리 침대", "씰리 매트리스", "SEALY"],
    "지누스":       ["지누스", "지누스 매트리스", "Zinus"],
    "코웨이 비렉스":["코웨이 비렉스", "비렉스", "코웨이 매트리스"],
    "한샘":         ["한샘 침대", "한샘 매트리스"],        # '한샘' 단독 금지 — 카테고리 오염
    "현대리바트":   ["현대리바트 침대", "리바트 침대", "리바트 매트리스"],
    "까사미아":     ["까사미아 침대", "까사미아 매트리스"],
    "일룸":         ["일룸 침대", "일룸 매트리스"],
    "에몬스":       ["에몬스", "에몬스 가구", "에몬스 침대"],
    "이케아":       ["이케아 침대", "이케아 매트리스"],    # '이케아' 단독 금지 — 카테고리 오염
}
