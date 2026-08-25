import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('data/latest.json', encoding='utf-8') as f:
    d = json.load(f)

gap = d.get('gap', [])
print('=== Gap 전체 ===')
for g in gap:
    brand = g.get('brand', '')
    naver = g.get('naver', 0)
    google = g.get('google', 0)
    gap_v = g.get('gap', 0)
    sign = '+' if gap_v > 0 else ''
    print(f'  {brand}: 네이버={naver:.1f} / 구글={google:.1f} / Gap={sign}{gap_v:.1f}')

print()
# monthly data check
monthly = d.get('google', {}).get('monthly_series', {})
print('=== 월별 시계열 브랜드 목록 ===')
print(list(monthly.keys())[:10])
