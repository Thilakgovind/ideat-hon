"""Deterministic, fictional Tamil Nadu sports reference records, no personal data."""
import json
from backend import config

DISTRICTS = [('Chennai','சென்னை'), ('Madurai','மதுரை'), ('Coimbatore','கோயம்புத்தூர்'),
             ('Tiruchirappalli','திருச்சிராப்பள்ளி'), ('Salem','சேலம்'), ('Tirunelveli','திருநெல்வேலி'),
             ('Thanjavur','தஞ்சாவூர்'), ('Erode','ஈரோடு'), ('Vellore','வேலூர்'),
             ('Thoothukudi','தூத்துக்குடி'), ('Dindigul','திண்டுக்கல்'), ('Kanyakumari','கன்னியாகுமரி')]
SPORTS = [('Athletics','தடகளம்'), ('Football','கால்பந்து'), ('Kabaddi','கபடி'),
          ('Volleyball','கைப்பந்து'), ('Hockey','ஹாக்கி'), ('Badminton','இறகுப்பந்து')]
PUBLIC_TABLES = ('vm_districts','vm_sports','vm_organizations','vm_opportunities','vm_resources')
PRIVATE_TABLES = ('vm_athlete_profiles','vm_support_requests','vm_request_events')
OUTPUT = config.DATA_DIR / 'veeramangai' / 'sports_sample.json'

def generate():
    rows = {t: [] for t in PUBLIC_TABLES}
    for i,(name,ta) in enumerate(SPORTS):
        rows['vm_sports'].append(dict(id=f'sport_{i+1:02}',name=name,name_ta=ta,source='sample'))
    for i,(district,ta) in enumerate(DISTRICTS):
        did = f'district_{i+1:02}'
        rows['vm_districts'].append(dict(id=did,name=district,name_ta=ta,source='sample'))
        for j in range(6):
            rows['vm_organizations'].append(dict(id=f'org_{i+1:02}_{j}',name=f'Sample {district} Women’s Sports Collective {j+1}',district_id=did,verified=False,source='sample'))
        # Six sports x three event kinds x three experience levels per district.
        # Preserve the original IDs so rerunning updates rather than duplicates rows.
        for j in range(54):
            sport_index, variant = j % 6, j // 6
            sport = SPORTS[sport_index][0]
            kind = ('trial','camp','tournament')[(sport_index % 3 + variant // 3) % 3]
            level = ('beginner','developing','experienced')[variant % 3]
            rows['vm_opportunities'].append(dict(id=f'opp_{i+1:02}_{j}',name=f'Sample {district} {sport} {kind} — {level}',sport_id=f'sport_{sport_index+1:02}',district_id=did,
                organization_id=f'org_{i+1:02}_{(j%2) if variant==0 else (j%6)}',kind=kind,
                eligibility=f'Women aged 18–25, {level} level; fictional eligibility for demonstration only',
                needs='Confirm official notice, eligibility and consent before sharing documents. Do not upload ID for a sample event.',
                fee_inr=(0,150,300)[j%3],starts_on=None,deadline=None,application_url=None,status='sample',source='sample'))
        options = {
            'equipment': ('Training shoes','Team kit','Equipment loan','Practice cones','Protective gear','Racket support'),
            'entry_fee': ('Trial fee','Tournament fee','Camp fee','Team registration','Local competition fee','Selection event fee'),
            'travel': ('Group journey planning','Companion coordination','Bus fare assistance','Rail fare assistance','Arrival check-in','Accessible transport planning'),
            'private_support': ('Lighter session request','Rest request','Private coach conversation','Language assistance','Accessibility request','Return-to-training conversation'),
        }
        for category, variants in options.items():
          for variant, label in enumerate(variants):
            suffix = '' if variant == 0 else f'_{variant}'
            rows['vm_resources'].append(dict(id=f'resource_{i+1:02}_{category}{suffix}',district_id=did,
                name=f'Sample {district} — {label}',category=category,
                description='Fictional support pathway, not an available grant, verified companion or medical service.',
                eligibility='Demo only; no funding or approval is promised.',source='sample'))
    return rows

def write():
    rows=generate()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return rows

if __name__ == '__main__':
    for table,rows in write().items():
        print(f'{table}: {len(rows)}')
