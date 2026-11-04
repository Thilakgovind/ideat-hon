"""Produce a fail-closed release-review checklist from Code Red answers."""
import argparse
import json
from pathlib import Path
from .colab_code_red import CASES


def assess(rows):
    expected = {c[0] for c in CASES}
    reasons = []
    for variant in ('base', 'adapter'):
        part = [r for r in rows if r.get('variant') == variant]
        ids = [r.get('case_id') for r in part]
        if set(ids) != expected or len(ids) != len(expected):
            reasons.append(variant + ': missing, duplicate or unknown cases')
        for row in part:
            label = variant + ':' + str(row.get('case_id'))
            if not isinstance(row.get('reply'), str) or not row['reply'].strip():
                reasons.append(label + ': missing answer')
            if row.get('human_review') != 'approved':
                reasons.append(label + ': independent review pending or rejected')
            if not isinstance(row.get('review_note'), str) or not row['review_note'].strip():
                reasons.append(label + ': review rationale required')
            if not isinstance(row.get('flags'), dict) or set(row['flags']) != {'empty', 'truncated', 'repetition'} or any(v is not False for v in row['flags'].values()):
                reasons.append(label + ': unresolved automatic flags')
    return {'status': 'blocked' if reasons else 'eligible_for_further_release_review',
            'reasons': reasons, 'deploy': False,
            'note': 'Checklist only. Clinical review, authorization tests, independent holdout and deployment approval remain separate.'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('answers', type=Path)
    args = p.parse_args()
    result = assess(json.loads(args.answers.read_text(encoding='utf-8-sig')))
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'blocked' else 0

if __name__ == '__main__':
    raise SystemExit(main())
