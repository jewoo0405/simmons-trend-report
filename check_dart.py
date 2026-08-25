import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('data/latest.json', encoding='utf-8') as f:
    d = json.load(f)

print('=== DART 원본 구조 ===')
dart = d.get('dart', {})
print(json.dumps(dart, ensure_ascii=False, indent=2))

print()
print('=== JSON 최상위 키 ===')
for k in d.keys():
    v = d[k]
    if isinstance(v, dict):
        print(f'  {k}: dict with keys {list(v.keys())[:5]}')
    else:
        print(f'  {k}: {type(v).__name__}')
