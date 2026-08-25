import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

START = '<!-- ② 시몬스 포지셔닝 + 주요 발견 (T1-1, T1-4) -->'
END   = '\n\n  <!-- 근거 데이터 구분선 -->'

s = src.find(START)
e = src.find(END, s)

if s == -1 or e == -1:
    print(f'ERROR: start={s}, end={e}')
    sys.exit(1)

print(f'삭제 범위: {s} ~ {e} ({e-s}자)')
print('삭제 내용 앞부분:', repr(src[s:s+80]))
print('삭제 내용 끝부분:', repr(src[e-80:e]))

result = src[:s] + src[e:]
print(f'원본: {len(src):,}자 → 수정: {len(result):,}자')

with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
