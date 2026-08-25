import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('output/report_2026_08_v2.html', encoding='utf-8') as f:
    src = f.read()

# HTML 카드 제목 안에 있는지 확인
for kw in ['시몬스 포지셔닝', '주요 발견', '이번 달 변화점']:
    # JS 주석/코드가 아닌 HTML 태그 안에 있는지
    pat = r'class="(?:section|card)-title[^"]*"[^>]*>' + re.escape(kw)
    found = bool(re.search(pat, src))
    total = src.count(kw)
    print(f'{kw}: HTML카드={found}, 전체등장={total}회 (JS주석 포함)')
