# 코드베이스 맵 — simmons-trend-report
작성일: 2026-08-19 (세션 1 조사 결과)

---

## 프로젝트 구조

```
C:\simmons-trend-report/
├── brand_config.py              # 브랜드 메타데이터, 배치 정의
├── main.py                      # 메인 수집·분석 파이프라인
├── cache.py                     # SQLite 캐시 관리
├── analyzer/
│   ├── chain_link.py            # Google Trends 배치 체인 링킹
│   ├── stats.py                 # SoS, Gap, CV 계산
│   └── validator.py             # 신뢰도 검증
├── collector/
│   ├── google_collector.py      # Google Trends 수집 (trendspy)
│   ├── naver_collector.py       # Naver Search API + Playwright
│   ├── naver_datalab_api.py     # DataLab 검색어트렌드 + 인구통계
│   └── dart_collector.py        # 네이버 증권 스크래핑 (매출액)
├── builder/
│   └── dashboard.py             # HTML 렌더링 (ECharts)
├── data/
│   ├── snapshots/               # 일자별 수집 결과 JSON (덮어쓰지 않음)
│   ├── history/                 # 월별 누적 JSON
│   └── latest.json
└── docs/
    └── fix-spec.md
```

---

## 지표 산출 위치

| 지표 | 파일 | 함수 | 분모/기준 |
|---|---|---|---|
| SoS | analyzer/stats.py:1-6 | share_of_search() | 11개 브랜드 전체 합계 |
| SoM | builder/dashboard.py:210-237 | _compute_sos_som() | dart 브랜드 매출 합계 |
| Gap | analyzer/stats.py:44-60 | naver_google_gap() | 카테고리 평균=100 재정규화 후 차이 |
| CV | analyzer/validator.py:26-42 | summarize() | std/mean (MAD 이상치 제거) |

---

## 브랜드 메타데이터 (brand_config.py)

- BRANDS: 11개 브랜드, tier/baseline/trend_kw/naver_kw/color 필드 존재
- **category 필드: 없음** → P1-1에서 추가 필요
- TREND_BATCHES: A/B/C 3개 배치, 브리지=일룸/에이스침대
- 현재 배치C: [에이스침대, 에몬스, 코웨이 비렉스, 씰리침대] → max/min=251.6배 문제

---

## 원본 데이터 보존 현황

| 데이터 | 보존 여부 | 위치 |
|---|---|---|
| Google 배치별 raw_medians | ✓ | snapshots/google.batches |
| Google 월별 시계열 | ✓ | snapshots/google.monthly_series |
| Naver 블로그+뉴스 건수 | ✓ | snapshots/naver_search |
| DataLab 인구통계 | ✓ | snapshots/naver_datalab |
| DART 매출액 (5개 상장사) | ✓ | snapshots/dart |
| 시몬스 매출 | ✗ | 감사보고서 존재하나 미수집 |
| 지누스 국내 매출 | ✗ | 글로벌 기준만 수집 |

→ **재수집 없이 로직 수정만으로 P0 대부분 처리 가능**

---

## fix-spec 과제별 수정 파일 매핑

| 과제 | 주요 수정 파일 |
|---|---|
| P0-1 미완결 월 감지 | main.py + builder/dashboard.py |
| P0-2 배치 정규화 | brand_config.py + analyzer/chain_link.py |
| P0-3 코웨이 비렉스 | collector/google_collector.py + builder/dashboard.py |
| P1-1 SoS 분모 이원화 | brand_config.py + analyzer/stats.py + builder/dashboard.py |
| P1-2 Gap 재정의 | analyzer/stats.py + builder/dashboard.py |
| P1-3 시몬스 SoM | collector/dart_collector.py + builder/dashboard.py |
| P1-4 ESOV 대각선 | builder/dashboard.py |
| P1-5 SoS 목표 재설정 | builder/dashboard.py |
| P2-1~P2-5 라벨/표기 | builder/dashboard.py |
