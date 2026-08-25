import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08_v2.html', encoding='utf-8') as f:
    src = f.read()

# changeEl 관련 코드 전체 추출
idx = src.find('const changeEl = document.getElementById')
end = src.find('\n\n  //', idx + 100)
print('changeEl 블록:')
print(src[idx:end if end != -1 else idx+1500])
