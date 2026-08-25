import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# CSV 함수 전체 제거
new_src = re.sub(
    r'// CSV 내보내기.*?function exportCSV\(\) \{.*?\}\n\n',
    '',
    src,
    flags=re.DOTALL
)

if new_src == src:
    print('패턴 미발견 — 이미 제거됐거나 패턴 불일치')
else:
    with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
        f.write(new_src)
    print('exportCSV 함수 제거 완료')
