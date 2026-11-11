"""Dependency-free tests for v0.13 session-only Semantic context routing."""
import copy
import unittest

from ski_context_route_v013 import (
    empty_context, next_context, _is_followup, context_route,
)


def native():
    return {
        "display_names": {
            "CLAIM": "主張", "EV": "根拠", "OTHER": "その他",
        },
        "nodes": [
            {"sd_id": "CLAIM", "node_type": "TOPIC"},
            {"sd_id": "EV", "node_type": "CONCEPT"},
            {"sd_id": "OTHER", "node_type": "ENTITY"},
        ]
    }


def converted():
    return {
        "relations": [
            {"source": "CLAIM", "target": "EV", "kind": "SUPPORTED_BY",
             "state": "APPROVED"}
        ]
    }


def step(text, state=None, *, n=None, c=None, resolver=None):
    return next_context(text, empty_context() if state is None else state,
                        native() if n is None else n,
                        converted() if c is None else c,
                        tmp_resolver=resolver)


class ContextRouteV013Tests(unittest.TestCase):
    def test_followup_recovers_source(self):
        state, _, reason = step("主張について教えて")
        self.assertEqual(reason, "EXPLICIT_TOPIC")
        state, request, reason = step("その根拠は？", state)
        self.assertEqual(reason, "CONTEXT_RESOLVED")
        self.assertEqual((request["source_sd"], request["target_sd"]),
                         ("CLAIM", "EV"))
        self.assertEqual(request["source_turn"], 1)

    def test_short_followup(self):
        state, _, _ = step("主張が気になる")
        _, request, _ = step("根拠は？", state)
        self.assertIsNotNone(request)

    def test_one_intervening_turn(self):
        state, _, _ = step("主張について話そう")
        state, result, _ = step("そうですね", state)
        self.assertIsNone(result)
        _, result, _ = step("その根拠は？", state)
        self.assertIsNotNone(result)

    def test_expiry(self):
        state, _, _ = step("主張について")
        for phrase in ("はい", "そうです", "わかりました"):
            state, _, _ = step(phrase, state)
        _, result, reason = step("その根拠は？", state)
        self.assertIsNone(result)
        self.assertEqual(reason, "NO_RECENT_CONTEXT")

    def test_ambiguous_explicit_clears(self):
        state, _, _ = step("主張について")
        state, _, reason = step("主張とその他について", state)
        self.assertEqual(reason, "AMBIGUOUS_TOPIC")
        self.assertIsNone(state["source_sd"])
        _, request, _ = step("その根拠は？", state)
        self.assertIsNone(request)

    def test_different_unmapped_topic_clears(self):
        state, _, _ = step("主張について")
        state, _, reason = step("その他の話です", state)
        self.assertEqual(reason, "UNMAPPED_TOPIC")
        _, request, _ = step("その根拠は？", state)
        self.assertIsNone(request)

    def test_tmp_multiple_topic_veto(self):
        veto = lambda _text: {"status": "ABSTAIN", "reason": "MULTIPLE_TOPICS"}
        state, _, reason = step("主張について", resolver=veto)
        self.assertEqual(reason, "TMP_AMBIGUITY_VETO")
        self.assertIsNone(state["source_sd"])

    def test_tmp_non_question_does_not_override(self):
        resolver = lambda _text: {"status": "NO_TARGET_QUESTION"}
        state, _, reason = step("主張について", resolver=resolver)
        self.assertEqual(reason, "EXPLICIT_TOPIC")
        _, req, _ = step("その根拠は？", state, resolver=resolver)
        self.assertIsNotNone(req)

    def test_explicit_question_keeps_antecedent(self):
        state, _, reason = step("主張の根拠は？")
        self.assertEqual(reason, "EXPLICIT_TOPIC")
        _, request, reason = step("その根拠は？", state)
        self.assertEqual(reason, "CONTEXT_RESOLVED")
        self.assertEqual(request["source_sd"], "CLAIM")

    def test_missing_context_abstains(self):
        _, request, reason = step("その根拠は？")
        self.assertIsNone(request)
        self.assertEqual(reason, "NO_RECENT_CONTEXT")

    def test_target_label_no_shadow(self):
        state, _, _ = step("主張について")
        _, request, _ = step("その根拠は？", state)
        self.assertEqual(request["source_sd"], "CLAIM")

    def test_multiple_targets_no_context(self):
        c = converted()
        c["relations"].append({
            "source": "CLAIM", "target": "OTHER", "kind": "SUPPORTED_BY",
            "state": "APPROVED"})
        state, _, reason = step("主張について", c=c)
        self.assertEqual(reason, "UNMAPPED_TOPIC")
        self.assertIsNone(state["source_sd"])

    def test_pending_not_selected(self):
        c = converted()
        c["relations"][0]["state"] = "PENDING"
        state, _, _ = step("主張について", c=c)
        self.assertIsNone(state["source_sd"])

    def test_reset(self):
        state, _, _ = step("主張について")
        state, req, reason = step("/reset", state)
        self.assertEqual(state, empty_context())
        self.assertIsNone(req)
        self.assertEqual(reason, "RESET")

    def test_no_input_mutation(self):
        s, n, c = empty_context(), native(), converted()
        old = copy.deepcopy((s, n, c))
        next_context("主張について", s, n, c)
        self.assertEqual((s, n, c), old)

    def test_commands_pass_through(self):
        s = empty_context()
        updated, result, reason = step("/status", s)
        self.assertEqual(updated, s)
        self.assertIsNone(result)
        self.assertEqual(reason, "NON_CHAT")

    def test_disabled_passes_through(self):
        s = empty_context()
        updated, result = context_route("主張について", s, environ={})
        self.assertEqual(updated, s)
        self.assertIsNone(result)

    def test_no_invented_relation_for_generic_chat(self):
        state, _, _ = step("主張について")
        _, req, reason = step("成分は？", state)
        self.assertIsNone(req)
        self.assertEqual(reason, "NON_REFERENCE_TURN")

    def test_nonexistent_display_names(self):
        n = native()
        del n["display_names"]
        state, _, reason = step("主張について", n=n)
        self.assertEqual(reason, "NO_RECENT_CONTEXT")
        self.assertIsNone(state["source_sd"])


if __name__ == "__main__":
    unittest.main()
