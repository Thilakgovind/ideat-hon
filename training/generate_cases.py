"""1,000 synthetic variations from 25 policy families; not 1,000 expert cases."""
import json
from pathlib import Path
from backend.athlete_support import POLICIES

ROOT=Path(__file__).resolve().parent
SPORTS=['athletics','football','kabaddi','volleyball','badminton']
CONTEXTS=['before practice','after practice','during a tournament','while planning next week','at a district camp','when speaking privately','when preparing a request','while reviewing my choices']

def generate():
    rows=[]
    for index,(pid,question,words,answer,source) in enumerate(POLICIES):
        split='train' if index<17 else 'validation' if index<21 else 'test'
        for n,(sport,context) in enumerate((s,c) for s in SPORTS for c in CONTEXTS):
            # Keep trigger phrases stable for policy tests; contextual wording varies.
            prompt=f'{question} I play {sport}. This is {context}.'
            rows.append({'id':f'{pid}_{n:02}','family':pid,'split':split,'source':'synthetic',
                'clinically_reviewed':False,'language':'en','references':[source] if source else [],
                'messages':[{'role':'system','content':'You are Avvai. Support women athletes with privacy, consent and evidence-linked uncertainty. Never diagnose, prescribe, infer hormones, invent opportunities or execute actions from chat.'},
                            {'role':'user','content':prompt},{'role':'assistant','content':answer}]})
    return rows

def main():
    rows=generate(); dest=ROOT/'data';dest.mkdir(exist_ok=True)
    for split in ('train','validation','test'):
        part=[r for r in rows if r['split']==split]
        (dest/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in part),encoding='utf-8')
        print(f'{split}: {len(part)}')
    print('total: '+str(len(rows)))

if __name__=='__main__':main()
