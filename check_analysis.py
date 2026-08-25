import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('data/latest.json', encoding='utf-8') as f:
    d = json.load(f)

dart = d.get('dart', {})

# caution=False인 매트리스 전업만 SoM 계산
mattress_only = {b: v['amount'] for b, v in dart.items() if not v.get('caution', True)}
total_mattress = sum(mattress_only.values())

print('=== SoM 계산 (매트리스 전업만, caution=False) ===')
for b, amt in sorted(mattress_only.items(), key=lambda x: -x[1]):
    som = round(amt/total_mattress*100, 1)
    print(f'  {b}: {amt:,}억 → SoM {som}%')
print(f'  합계: {total_mattress:,}억')

# SoS (침대전업)
g = d.get('google', {}).get('linked', {})
bed_brands = ['시몬스', '에이스침대', '씰리침대', '지누스', '템퍼']
bed_g = {b: g[b] for b in bed_brands if b in g and g[b] and g[b] > 0}
total_bed = sum(bed_g.values())
sos_bed = {b: round(v/total_bed*100, 1) for b, v in bed_g.items()}

print()
print('=== ESOV (침대전업 SoS - 매트리스전업 SoM) ===')
for b in mattress_only:
    sos = sos_bed.get(b, None)
    som = round(mattress_only[b]/total_mattress*100, 1)
    esov = round(sos - som, 1) if sos else None
    print(f'  {b}: SoS={sos}% - SoM={som}% = ESOV {esov}%p')

# DataLab age
dl = d.get('naver_datalab', {})
sim_age = dl.get('시몬스', {}).get('age', {})
total_age = sum(sim_age.values()) or 1
print()
print('=== 시몬스 연령 분포 ===')
for k, v in sorted(sim_age.items()):
    print(f'  {k}: {v/total_age*100:.1f}%')
young = (sim_age.get('20대', 0) + sim_age.get('30대', 0)) / total_age * 100
print(f'  20+30대 합계: {young:.1f}%')
older = (sim_age.get('40대', 0) + sim_age.get('50대', 0) + sim_age.get('60대+', 0)) / total_age * 100
print(f'  40+대 합계: {older:.1f}%')

# Gap data
gap = d.get('gap', [])
print()
print('=== Gap 데이터 (검색 대비 콘텐츠) ===')
for g_item in gap[:5]:
    print(f'  {g_item}')
