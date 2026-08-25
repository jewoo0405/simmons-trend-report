import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

OLD = '\n\n  <!-- 근거 데이터 구분선 -->\n  <div class="section-divider">근거 데이터</div>\n'
NEW = '\n'

count = src.count(OLD)
print(f'패턴 발견: {count}개')

result = src.replace(OLD, NEW, 1)
with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
