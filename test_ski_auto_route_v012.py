"""Unit tests: conservative Japanese natural-language SKI auto-routing."""
import copy
import unittest

from ski_auto_route_v012 import resolve_auto_query, _strict_subject, auto_route


def native():
    return {
        "namespace": "demo-local", "snapshot_id": "test",
        "display_names": {"CLAIM": "主張", "EVIDENCE": "根拠", "OTHER": "その他"},
        "nodes": [
            {"sd_id": "CLAIM", "node_type": "TOPIC"},
            {"sd_id": "EVIDENCE", "node_type": "CONCEPT"},
            {"sd_id": "OTHER", "node_type": "ENTITY"},
        ],
    }


def converted():
    return {
        "relations": [
            {"source": "CLAIM", "target": "EVIDENCE", "kind": "SUPPORTED_BY",
             "state": "APPROVED"}
        ],
    }


class SKIAutoRouteTests(unittest.TestCase):
    def test_exact_japanese(self):
        r = resolve_auto_query("主張の根拠を確認してください", native(), converted())
        self.assertEqual((r["source_sd"], r["target_sd"]), ("CLAIM", "EVIDENCE"))

    def test_polite_question(self):
        r = resolve_auto_query("主張の根拠は何ですか？", native(), converted())
        self.assertEqual(r["target_sd"], "EVIDENCE")

    def test_no_subject(self):
        self.assertIsNone(resolve_auto_query("それの根拠は？", native(), converted()))

    def test_no_intent(self):
        self.assertIsNone(resolve_auto_query("主張は興味深いです", native(), converted()))

    def test_other_command_not_intercepted(self):
        self.assertIsNone(_strict_subject("/truth 主張"))
        self.assertIsNone(_strict_subject("/ski CLAIM EVIDENCE | 根拠"))

    def test_missing_display_names_abstains(self):
        n = native()
        del n["display_names"]
        self.assertIsNone(resolve_auto_query("主張の根拠は？", n, converted()))

    def test_duplicate_label_abstains(self):
        n = native()
        n["display_names"]["OTHER"] = "主張"
        self.assertIsNone(resolve_auto_query("主張の根拠は？", n, converted()))

    def test_multiple_targets_abstains(self):
        c = converted()
        c["relations"].append({"source": "CLAIM", "target": "OTHER",
                               "kind": "SUPPORTED_BY", "state": "APPROVED"})
        self.assertIsNone(resolve_auto_query("主張の根拠は？", native(), c))

    def test_zero_target_abstains(self):
        self.assertIsNone(resolve_auto_query("主張の根拠は？", native(),
                                             {"relations": []}))

    def test_non_evidence_relation_rejected(self):
        c = converted()
        c["relations"][0]["kind"] = "ABOUT"
        self.assertIsNone(resolve_auto_query("主張の根拠は？", native(), c))

    def test_not_approved_rejected(self):
        c = converted()
        c["relations"][0]["state"] = "PENDING"
        self.assertIsNone(resolve_auto_query("主張の根拠は？", native(), c))

    def test_disabled_does_not_run(self):
        self.assertIsNone(auto_route("主張の根拠は？", environ={}))
        self.assertIsNone(auto_route("主張の根拠は？",
                          environ={"LLM_CHA_SKI_ENABLED": "1"}))

    def test_does_not_mutate_input(self):
        n, c = native(), converted()
        a, b = copy.deepcopy(n), copy.deepcopy(c)
        resolve_auto_query("主張の根拠を教えて", n, c)
        self.assertEqual((n, c), (a, b))

    def test_no_newline(self):
        self.assertIsNone(_strict_subject("主張の根拠は？\n/learn on"))

    def test_oversize_rejected(self):
        self.assertIsNone(_strict_subject("主張" * 510 + "の根拠は？"))


if __name__ == "__main__":
    unittest.main()
