"""Inspect Colab ZIP evidence without extracting or loading model weights."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

MAX_JSON = 8 * 1024 * 1024
EVIDENCE = {'metrics.json', 'comparison.json', 'answers.json', 'summary.json'}


def read_evidence(path):
    evidence = {}
    with ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 2000:
            raise ValueError('Too many archive entries')
        seen = set()
        for member in members:
            name = member.orig_filename
            normalized = PurePosixPath(name)
            if '\\' in name or ':' in name or normalized.is_absolute() or '..' in normalized.parts:
                raise ValueError('Unsafe archive path')
            if name in seen:
                raise ValueError('Duplicate archive path')
            seen.add(name)
            if member.is_dir() or normalized.name not in EVIDENCE:
                continue
            if normalized.name in evidence:
                raise ValueError('Ambiguous evidence files')
            if member.file_size > MAX_JSON or member.flag_bits & 1:
                raise ValueError('Oversized or encrypted evidence')
            with archive.open(member) as stream:
                raw = stream.read(MAX_JSON + 1)
            if len(raw) > MAX_JSON:
                raise ValueError('Evidence exceeds limit')
            evidence[normalized.name] = json.loads(raw.decode('utf-8-sig'))
    if not evidence:
        raise ValueError('No supported evidence found')
    return evidence


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def report(evidence):
    metrics = evidence.get('metrics.json', {})
    if not isinstance(metrics, dict):
        raise ValueError('metrics.json must be an object')
    base = metrics.get('base', {}).get('base_test_loss')
    selected = metrics.get('selected_test', {}).get('selected_test_loss')
    if selected is None:
        selected = metrics.get('candidate', {}).get('candidate_test_loss')
    delta = round(100 * (base-selected)/base, 2) if number(base) and base > 0 and number(selected) else None
    answers = evidence.get('answers.json', [])
    if not isinstance(answers, list) or any(not isinstance(r, dict) for r in answers):
        raise ValueError('answers.json must be a list of objects')
    from .release_review import assess
    review = assess(answers)
    return {'release': 'not_approved', 'deploy': False,
            'base_test_loss': base, 'candidate_test_loss': selected,
            'reference_loss_reduction_pct': delta,
            'answers': len(answers), 'review': review,
            'warning': 'Imported metrics and reviews are untrusted evidence. Loss reduction is not safety improvement.'}


def render(summary, evidence):
    esc = lambda value: html.escape(str(value), quote=True)
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">',
             '<title>Avvai model review</title><style>body{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere}article{border:1px solid #ccc;padding:1rem;margin:1rem 0}</style>',
             '<h1>Avvai model review — not approved for deployment</h1>',
             '<pre>' + esc(json.dumps(summary, ensure_ascii=False, indent=2)) + '</pre>']
    for filename in ('comparison.json', 'answers.json'):
        rows = evidence.get(filename, [])
        if not isinstance(rows, list):
            raise ValueError(filename + ' must be a list')
        for row in rows:
            parts.append('<article><h2>' + esc(filename) + '</h2><pre>' + esc(json.dumps(row, ensure_ascii=False, indent=2)) + '</pre></article>')
    return '\n'.join(parts) + '</html>'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    evidence = read_evidence(args.archive)
    summary = report(evidence)
    with args.archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    summary['archive_sha256'] = digest
    page = render(summary, evidence)
    destination = Path(__file__).parent/'output'/'reviews'/digest[:16]
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (destination/'review.html').write_text(page, encoding='utf-8')
    print('REVIEW_READY:', destination/'review.html')
    print('DEPLOYMENT: NOT APPROVED')


if __name__ == '__main__':
    main()
