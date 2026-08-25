import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

# renderThisMonthChanges IIFE 전체를 null 체크로 감싸기
OLD = "  (function renderThisMonthChanges() {"
NEW = "  if (!changeEl) return;\n  (function renderThisMonthChanges() {"

count = src.count(OLD)
print(f'패턴 발견: {count}개')

if count == 0:
    print('ERROR: 패턴 없음')
    sys.exit(1)

result = src.replace(OLD, NEW, 1)

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
