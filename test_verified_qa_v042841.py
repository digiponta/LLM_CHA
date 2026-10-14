import copy
import unittest
from build_verified_qa_v042841 import build, split_group

BASE = {'mode': 'HUMAN_REVIEWED_POSITIVE_EXPORT', 'runtime_modified': False, 'positives': [], 'pending': 26}

def record(rid='p1', kind='positive', group='物理'):
    r = {'id': rid, 'subject_group': group, 'question': '量子力学とは', 'answer': '物理学の理論',
         'source_id': 'source1', 'license': 'reviewed_license', 'review_status': 'approved',
         'human_verified': True, 'license_audited': True, 'privacy_audited': True}
    if kind != 'positive':
        r.update(answer='間違った回答', gold_positive_id='p1', negative_verified=True)
    return r

class VerifiedDatasetTests(unittest.TestCase):
    def test_pending_stays_empty(self):
        result = build(BASE)
        self.assertEqual(result['counts'], {'positives': 0, 'negatives': 0, 'hard_negatives': 0})
        self.assertFalse(result['train_ready'])
        self.assertEqual(result['source_pending'], 26)

    def test_no_implicit_approval(self):
        data = copy.deepcopy(BASE)
        r = record()
        r['review_status'] = 'pending'
        data['positives'] = [r]
        self.assertEqual(build(data)['counts']['positives'], 0)

    def test_requires_rights_privacy(self):
        data = copy.deepcopy(BASE)
        r = record()
        r['privacy_audited'] = False
        data['positives'] = [r]
        self.assertEqual(build(data)['rejected_invalid'], 1)

    def test_negative_requires_verified_gold(self):
        data = copy.deepcopy(BASE)
        data['positives'] = [record()]
        pool = {'negatives': [record('n1', 'negative')], 'hard_negatives': []}
        self.assertEqual(build(data, pool)['counts']['negatives'], 1)
        pool['negatives'][0]['gold_positive_id'] = 'missing'
        self.assertEqual(build(data, pool)['counts']['negatives'], 0)

    def test_group_split_stable(self):
        self.assertEqual(split_group('数学'), split_group('数学'))
        self.assertIn(split_group('数学'), ('train', 'val', 'test'))

    def test_no_duplicate_id(self):
        data = copy.deepcopy(BASE)
        data['positives'] = [record(), record()]
        self.assertEqual(build(data)['rejected_invalid'], 1)

    def test_reject_matching_wrong_answer(self):
        data = copy.deepcopy(BASE)
        data['positives'] = [record()]
        wrong = record('n1', 'negative')
        wrong['answer'] = '物理学の理論'
        self.assertEqual(build(data, {'negatives': [wrong]})['counts']['negatives'], 0)

if __name__ == '__main__':
    unittest.main()
