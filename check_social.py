import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08_v2.html', encoding='utf-8') as f:
    src = f.read()

# null 가드 적용 확인
guard1 = "(document.getElementById('insight-simmons') || {}).innerHTML"
guard2 = "(document.getElementById('insight-findings') || {}).innerHTML"
print('null 가드 insight-simmons:', guard1 in src)
print('null 가드 insight-findings:', guard2 in src)

# changeEl 주변 코드
ce_idx = src.find('const changeEl')
print('\nchangeEl 코드:')
print(src[ce_idx:ce_idx+300])

# renderSocialChart 바로 전후 확인
rs_idx = src.find('renderSocialChart();')
print('\nrenderSocialChart 호출 주변:')
print(src[rs_idx-200:rs_idx+80])

# section-social 위치
ss_idx = src.find('id="section-social"')
print(f'\nsection-social 위치: {ss_idx}')
