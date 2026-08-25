import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('data/latest.json', encoding='utf-8') as f:
    d = json.load(f)

# ── Google SoS ────────────────────────────────────────────────
g = d.get('google', {}).get('linked', {})
total_g = sum(v for v in g.values() if v and v > 0)
sos_all = {b: round(v/total_g*100, 1) for b, v in g.items() if v and v > 0}

bed_brands = ['시몬스', '에이스침대', '씰리침대', '지누스', '템퍼']
bed_g = {b: g[b] for b in bed_brands if b in g and g[b] and g[b] > 0}
total_bed = sum(bed_g.values())
sos_bed = {b: round(v/total_bed*100, 1) for b, v in bed_g.items()}

print('=== SoS 전체 ===')
for b, v in sorted(sos_all.items(), key=lambda x: -x[1]):
    print(f'  {b}: {v}%')

print()
print('=== SoS 침대전업 ===')
for b, v in sorted(sos_bed.items(), key=lambda x: -x[1]):
    print(f'  {b}: {v}%')

# ── DART ─────────────────────────────────────────────────────
dart = d.get('dart', {})
total_rev = sum(v.get('revenue', 0) for v in dart.values())
print()
print('=== DART 매출 (SoM) ===')
for b, v in sorted(dart.items(), key=lambda x: -x[1].get('revenue', 0)):
    rev = v.get('revenue', 0)
    yr = v.get('year', '')
    som = round(rev/total_rev*100, 1) if total_rev else 0
    print(f'  {b}: {rev:,}억 ({yr}) → SoM {som}%')
print(f'  [합계] {total_rev:,}억')

# ── ESOV ─────────────────────────────────────────────────────
print()
print('=== ESOV 계산 (침대전업 SoS - SoM) ===')
for b in bed_brands:
    sos = sos_bed.get(b, None)
    rev = dart.get(b, {}).get('revenue', None)
    som = round(rev/total_rev*100, 1) if rev and total_rev else None
    esov = round(sos - som, 1) if sos is not None and som is not None else None
    print(f'  {b}: SoS={sos}% SoM={som}% ESOV={esov}%p')

# ── DataLab ──────────────────────────────────────────────────
dl = d.get('naver_datalab', {})
print()
print('=== DataLab 연령 시몬스 ===')
sim = dl.get('시몬스', {})
age = sim.get('age', {})
total_a = sum(age.values()) or 1
for k, v in sorted(age.items()):
    print(f'  {k}: {v/total_a*100:.1f}%')

print()
print('=== DataLab 연령 에이스침대 ===')
ace = dl.get('에이스침대', {})
age2 = ace.get('age', {})
total_a2 = sum(age2.values()) or 1
for k, v in sorted(age2.items()):
    print(f'  {k}: {v/total_a2*100:.1f}%')

# ── YouTube ──────────────────────────────────────────────────
yt = d.get('youtube', {})
print()
print('=== YouTube ===')
for b, v in yt.items():
    print(f'  {b}: {v}')
