import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08_v2.html', encoding='utf-8') as f:
    src = f.read()

checks = [
    ('분석하기 버튼', 'btn-analyze'),
    ('저장 버튼', 'btn-save'),
    ('수정 버튼', 'btn-edit'),
    ('저장 배너', 'an-saved-banner'),
    ('분석 내용 래퍼', 'analysis-body-content'),
    ('saveAnalysis 함수', 'function saveAnalysis()'),
    ('editAnalysis 함수', 'function editAnalysis()'),
    ('localStorage 키', 'ANALYSIS_STORAGE_KEY'),
    ('runAnalysis 함수', 'function runAnalysis()'),
]
all_ok = True
for label, pat in checks:
    ok = pat in src
    print(f'  {"✓" if ok else "✗"} {label}')
    if not ok: all_ok = False

print()
print('전체 결과:', '정상' if all_ok else '일부 누락')
