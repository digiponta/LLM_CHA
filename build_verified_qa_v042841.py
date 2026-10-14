#!/usr/bin/env python3
"""LLM_CHA v0.4.28.41: fail-closed verified QA dataset builder (offline only)."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

VERSION = 'v0.4.28.41'
KINDS = ('positives', 'negatives', 'hard_negatives')


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def text_field(rec, key):
    v = rec.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f'missing non-empty {key}')
    return v.strip()


def validate(rec, kind):
    if not isinstance(rec, dict):
        raise ValueError('record must be object')
    # Do not synthesize or infer human approval, rights or privacy clearance.
    if rec.get('review_status') != 'approved':
        raise ValueError('review_status must be approved')
    if rec.get('human_verified') is not True:
        raise ValueError('human_verified must be true')
    if rec.get('license_audited') is not True or rec.get('privacy_audited') is not True:
        raise ValueError('license and privacy audits required')
    rid = text_field(rec, 'id')
    subject = text_field(rec, 'subject_group')
    q = text_field(rec, 'question')
    answer = text_field(rec, 'answer')
    if kind != 'positives':
        if rec.get('negative_verified') is not True:
            raise ValueError('negative must be independently verified')
        if rec.get('gold_positive_id') in (None, ''):
            raise ValueError('negative needs gold_positive_id')
    return {'id': rid, 'subject_group': subject, 'question': q, 'answer': answer,
            'kind': kind, 'gold_positive_id': rec.get('gold_positive_id') if kind != 'positives' else None,
            'source_id': text_field(rec, 'source_id'), 'license': text_field(rec, 'license'),
            'review_status': 'approved', 'human_verified': True,
            'license_audited': True, 'privacy_audited': True,
            **({'negative_verified': True} if kind != 'positives' else {})}


def split_group(group):
    # deterministic, order-independent, stable; only group-based, no row randomization
    p = int(hashlib.sha256(('LLM_CHA:v042841:' + group).encode()).hexdigest()[:16], 16) % 100
    return 'train' if p < 80 else ('val' if p < 90 else 'test')


def build(reviewed, negative_pool=None):
    if reviewed.get('mode') != 'HUMAN_REVIEWED_POSITIVE_EXPORT':
        raise ValueError('wrong reviewed export mode')
    if reviewed.get('runtime_modified') is not False:
        raise ValueError('runtime modified or status unknown')
    if reviewed.get('train_ready') is True and not reviewed.get('positives'):
        raise ValueError('inconsistent train_ready')
    invalid, items, ids = [], [], set()
    sources = [('positives', reviewed)]
    if negative_pool is not None:
        sources += [('negatives', negative_pool), ('hard_negatives', negative_pool)]
    for kind, source in sources:
        for index, row in enumerate(source.get(kind, [])):
            try:
                item = validate(row, kind)
                if item['id'] in ids:
                    raise ValueError('duplicate id')
                ids.add(item['id'])
                items.append(item)
            except (ValueError, TypeError) as err:
                invalid.append({'kind': kind, 'index': index, 'reason': str(err)})
    pos_by_id = {r['id']: r for r in items if r['kind'] == 'positives'}
    cleaned = []
    for rec in items:
        if rec['kind'] != 'positives':
            gold = pos_by_id.get(rec['gold_positive_id'])
            if not gold or gold['subject_group'] != rec['subject_group'] or gold['question'] != rec['question']:
                invalid.append({'kind': rec['kind'], 'id': rec['id'], 'reason': 'unmatched gold positive / subject / question'})
                continue
            if gold['answer'] == rec['answer']:
                invalid.append({'kind': rec['kind'], 'id': rec['id'], 'reason': 'negative equals gold answer'})
                continue
        cleaned.append(rec)
    counts = {k: sum(r['kind'] == k for r in cleaned) for k in KINDS}
    groups = defaultdict(list)
    for rec in cleaned:
        groups[split_group(rec['subject_group'])].append(rec)
    for split in ('train', 'val', 'test'):
        groups[split].sort(key=lambda r: (r['subject_group'], r['id']))
    # Zero accepted => no dataset; large-enough threshold is deliberately *not* inferred.
    ready = all(counts[k] > 0 for k in KINDS) and not invalid and all(groups[s] for s in ('train', 'val', 'test'))
    return {'version': VERSION, 'mode': 'VERIFIED_QA_OFFLINE_DATASET',
            'source_input_sha256': reviewed.get('source_input_sha256'),
            'reviewed_input_sha256': sha(reviewed),
            'negative_pool_sha256': sha(negative_pool) if negative_pool is not None else None,
            'source_pending': reviewed.get('pending'),
            'counts': counts, 'rejected_invalid': len(invalid), 'invalid_details': invalid,
            'split': {s: groups[s] for s in ('train', 'val', 'test')},
            'train_ready': ready, 'evaluation_ready': ready,
            'runtime_modified': False,
            'note': 'No automatic approval or auto-generated negatives. Ready means structural checks only, not scientific adequacy or legal approval.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reviewed', required=True)
    p.add_argument('--negative-pool', help='Separately human-verified negatives/hard negatives JSON')
    p.add_argument('--output', default='results/japanese_foundation_dataset_v042841.json')
    args = p.parse_args()
    result = build(read_json(args.reviewed), read_json(args.negative_pool) if args.negative_pool else None)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('version', 'source_pending', 'counts', 'rejected_invalid', 'train_ready', 'evaluation_ready', 'runtime_modified')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
