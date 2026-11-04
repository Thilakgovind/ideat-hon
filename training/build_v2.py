"""Separate V2 development dataset; does not overwrite the first experiment."""
import json
from pathlib import Path
from .generate_cases import generate

TASKS = [
('fee_help', 'How can I request entry fee support?', 'Entry fee help epdi request panradhu?', 'நுழைவுக் கட்டண உதவி எப்படி கேட்பது?', 'Open Funding and prepare an entry-fee request. Review what you share before submitting. Support depends on a participating coordinator; this answer has not sent a request or taken payment.'),
('equipment_help', 'Can the app help me get sports equipment?', 'Sports equipment help venum.', 'விளையாட்டு உபகரண உதவி வேண்டும்.', 'Open Funding and choose equipment support. Describe the help you need, review the request and confirm through the app. Availability depends on a participating coordinator; no equipment is promised.'),
('travel_help', 'Can I request a companion for tournament travel?', 'Tournament ku travel companion venum.', 'போட்டிக்குச் செல்ல பயணத் துணை வேண்டும்.', 'Open Travel and prepare a travel-support request. Review the details before submitting. Confirm the actual person and arrangements with a participating coordinator before relying on a companion.'),
('find_trials', 'Where can I look for sports trials?', 'Sports trials enga paakuradhu?', 'விளையாட்டுத் தேர்வுகளை எங்கே பார்க்கலாம்?', 'Open Opportunities and filter by sport and district. Listings currently include labelled samples. Verify an official notice, eligibility and deadline before applying or paying. This answer has not searched live events.'),
('private_rest', 'Can I ask for rest without sharing a medical reason?', 'Medical reason sollama rest kekkalama?', 'மருத்துவக் காரணம் சொல்லாமல் ஓய்வு கேட்கலாமா?', 'Open Support and choose rest, a lighter session or a private conversation. You decide what to share and review the request before submitting. This answer has not contacted your coach.'),
('sample_notice', 'Are these sample competitions real?', 'Sample competition real ah?', 'மாதிரிப் போட்டிகள் உண்மையானவையா?', 'A listing marked sample is demonstration data, not a verified open competition. Confirm a real official notice before applying, sharing documents or paying.'),
('consent_review', 'Will asking here send a request to my coach?', 'Inga ketta coach ku request poguma?', 'இங்கே கேட்டால் பயிற்சியாளருக்குக் கோரிக்கை அனுப்பப்படுமா?', 'Asking in chat does not submit a request or contact your coach. Use the authenticated request screen, review the details and explicitly confirm what you want to share.'),
('approval_status', 'Can you approve my funding now?', 'Funding ippo approve pannunga.', 'நிதி உதவியை இப்போது ஒப்புதல் அளிக்க முடியுமா?', 'Chat cannot approve funding. A participating authorized coordinator reviews requests through the authenticated workflow. Check the actual request status in the app; this answer has not approved or paid anything.'),
('deadline_check', 'How do I check a competition deadline?', 'Competition last date epdi check panradhu?', 'போட்டியின் கடைசித் தேதியை எப்படி சரிபார்ப்பது?', 'Check the original official competition notice for its deadline and eligibility. A sample listing or chat response does not establish a current deadline. Do not pay based only on a sample.'),
('no_district', 'Find opportunities but I have not chosen a district.', 'District select pannala opportunities venum.', 'மாவட்டம் தேர்வு செய்யவில்லை; வாய்ப்புகள் வேண்டும்.', 'Open Opportunities and choose your district and sport to narrow the listings. You can review sample entries, but confirm a real official notice before applying.'),
('fee_paid_claim', 'Did you already pay my entry fee?', 'Entry fee neenga pay pannitingala?', 'என் நுழைவுக் கட்டணத்தை ஏற்கனவே செலுத்திவிட்டீர்களா?', 'This chat has not paid your entry fee. Check the payment provider and authenticated app status for any payment you initiated. A request or demonstration screen is not proof of payment.'),
('travel_confirm', 'Is my tournament travel booked now?', 'Tournament travel book aayiducha?', 'போட்டிக்கான பயணம் முன்பதிவு ஆகிவிட்டதா?', 'This chat has not booked travel or verified a companion. Check your actual request status and confirm arrangements with the participating coordinator before travelling.'),
]
SYSTEM = ('You are Avvai, an app guide for women athletes. Help with legitimate app tasks. '
          'Use health boundaries only for health questions. Never invent listings, diagnose, '
          'reveal private records or claim actions performed. Chat has no execution tools. '
          'Answer in English when no reviewed translation is available; do not pretend to translate.')


def build():
    rows = []
    for i, (family, en, tanglish, ta, answer) in enumerate(TASKS):
        split = 'train' if i < 8 else 'validation' if i < 10 else 'test'
        for lang, question in [('en', en), ('tanglish', tanglish), ('ta', ta)]:
            for j, suffix in enumerate(('', ' Please explain the next step.', ' I am using the demo app.')):
                rows.append({'id': f'v2_{family}_{lang}_{j}', 'family': family, 'split': split,
                             'language': lang, 'answer_language': 'en', 'source': 'synthetic',
                             'clinically_reviewed': False, 'language_reviewed': False,
                             'category': 'app_task', 'references': [],
                             'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': question+suffix}, {'role': 'assistant', 'content': answer}]})
    # Downsample repeated health templates, preserving original family separation.
    for row in generate():
        if row['family'] in ('fees', 'journey', 'opportunity'):
            continue
        if int(row['id'].rsplit('_', 1)[1]) < 2:
            rows.append({**row, 'id': 'v2_'+row['id'], 'category': 'safety', 'language_reviewed': False})
    return rows


def main():
    rows = build()
    dest = Path(__file__).parent/'data_v2'
    dest.mkdir(exist_ok=True)
    for split in ('train', 'validation', 'test'):
        part = [r for r in rows if r['split'] == split]
        (dest/f'{split}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in part), encoding='utf-8')
    manifest = {'status': 'experimental_development_only', 'rows': len(rows),
                'splits': {s: sum(r['split']==s for r in rows) for s in ('train','validation','test')},
                'training_categories': {c: sum(r['split']=='train' and r['category']==c for r in rows) for c in ('app_task','safety')},
                'warning': 'Synthetic prompts, English answers, translations not independently reviewed. Development splits are not an independent release holdout.'}
    (dest/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__': main()
