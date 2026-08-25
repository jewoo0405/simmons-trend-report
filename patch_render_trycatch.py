import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('output/report_2026_08.html', encoding='utf-8') as f:
    src = f.read()

OLD = """renderRankCharts();
renderMonthly();
renderDatalab();
renderSoS();
renderGap();
renderGender();
renderAge();
renderSoSSoM();
renderInsights();
renderSocialChart();"""

NEW = """[renderRankCharts, renderMonthly, renderDatalab, renderSoS, renderGap,
 renderGender, renderAge, renderSoSSoM, renderInsights, renderSocialChart
].forEach(fn => { try { fn(); } catch(e) { console.error('[render]', fn.name, e); } });"""

count = src.count(OLD)
print(f'패턴 발견: {count}개')

if count == 0:
    print('ERROR: 패턴 없음. 실제 코드 확인:')
    idx = src.find('renderRankCharts();')
    print(repr(src[idx:idx+300]))
    sys.exit(1)

result = src.replace(OLD, NEW, 1)
with open('output/report_2026_08.html', 'w', encoding='utf-8') as f:
    f.write(result)
print('저장 완료')
