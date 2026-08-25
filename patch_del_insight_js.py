import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# JS 블록 시작: insight-simmons 참조 앞
# 찾을 패턴: 임원 요약 JS 블록 전체
START_JS = "  // ── 임원 요약 인사이트"
END_JS   = "  // ── 이번 달 변화점 끝"

s = src.find(START_JS)
e = src.find(END_JS)

if s != -1 and e != -1:
    print(f'임원요약 JS 블록: {s}~{e+len(END_JS)}')
    result = src[:s] + src[e+len(END_JS):]
else:
    # 대안: insight-simmons 참조 전체 블록 수동 찾기
    print('대안 탐색...')
    SEARCH = "document.getElementById('insight-simmons')"
    idx = src.find(SEARCH)
    if idx == -1:
        print('insight-simmons 없음 — 이미 제거됨')
        sys.exit(0)
    # 블록 앞쪽 찾기 (// 주석으로 시작하는 부분)
    block_start = src.rfind('\n  //', 0, idx)
    # 블록 끝 찾기 (이번 달 변화점 섹션 끝)
    block_end_marker = "  // ── 순위 변동"
    block_end = src.find(block_end_marker, idx)
    if block_end == -1:
        # 대안 끝 마커
        block_end_marker = "\n\n  function render"
        block_end = src.find(block_end_marker, idx)
    print(f'블록 범위: {block_start}~{block_end}')
    print('앞부분:', repr(src[block_start:block_start+100]))
    print('끝부분:', repr(src[block_end:block_end+100]))
    result = None

if result is None:
    print('JS 블록 자동 제거 실패 — null 가드 방식으로 대체')
    # 안전하게 null 체크 추가
    old1 = "document.getElementById('insight-simmons').innerHTML"
    new1 = "(document.getElementById('insight-simmons') || {}).innerHTML"
    old2 = "document.getElementById('insight-findings').innerHTML"
    new2 = "(document.getElementById('insight-findings') || {}).innerHTML"
    result = src.replace(old1, new1).replace(old2, new2)
    # changeEl null 가드
    old3 = "  if (changeEl) changeEl.innerHTML"
    # 이미 있으면 ok, 없으면 추가
    ce_idx = src.find("const changeEl = document.getElementById('insight-changes')")
    if ce_idx != -1:
        print('changeEl 이미 null 가드 확인')
    count = result.count(new1) + result.count(new2)
    print(f'null 가드 적용: {count}개')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
