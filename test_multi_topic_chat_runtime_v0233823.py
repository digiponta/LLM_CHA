"""v0.2.33.82.3 integration-boundary regression tests."""
import unittest
from multi_topic_chat_runtime_v0233823 import MultiTopicChatRuntime


class RuntimeIntegrationTests(unittest.TestCase):
    def test_verified_responder_required(self):
        with self.assertRaises(ValueError):
            MultiTopicChatRuntime(None)

    def test_multi_turn_topic_switch(self):
        observed = []
        runtime = MultiTopicChatRuntime(lambda q: observed.append(q) or "検証済み")
        for text in ("宇宙について教えて", "GPUとは", "宇宙の話に戻って", "もう少し詳しく"):
            self.assertEqual(runtime.respond(text).status, "ANSWER")
        self.assertEqual(len(observed), 4)
        self.assertIn("宇宙", observed[-1])
        self.assertNotIn("GPU", observed[-1])

    def test_ambiguous_reference_never_reaches_responder(self):
        observed = []
        runtime = MultiTopicChatRuntime(lambda q: observed.append(q) or "ok")
        runtime.respond("宇宙について教えて")
        runtime.respond("GPUとは")
        self.assertEqual(runtime.respond("それについて").status, "CLARIFY")
        self.assertEqual(len(observed), 2)

    def test_reset_does_not_call_responder(self):
        observed = []
        runtime = MultiTopicChatRuntime(lambda q: observed.append(q) or "ok")
        runtime.respond("宇宙について教えて")
        self.assertEqual(runtime.respond("/reset").status, "RESET")
        self.assertEqual(runtime.respond("もう少し詳しく").status, "NO_TOPIC")
        self.assertEqual(len(observed), 1)

    def test_unverified_response_is_preserved(self):
        # Stub models the *already verified* legacy Truth Gate response.
        # This test does NOT constitute actual legacy Truth Gate validation.
        runtime = MultiTopicChatRuntime(lambda q: "未学習です")
        result = runtime.respond("未検証分野について教えて")
        self.assertEqual(result.status, "ANSWER")
        self.assertEqual(result.text, "未学習です")

    def test_truth_state_not_modified(self):
        facts = {"宇宙": {"truth_state": "UNVERIFIED"}}
        before = repr(facts)
        runtime = MultiTopicChatRuntime(lambda q: "未学習です")
        runtime.respond("宇宙について教えて")
        runtime.respond("/reset")
        self.assertEqual(repr(facts), before)

    def test_command_isolated(self):
        invoked = []
        runtime = MultiTopicChatRuntime(
            lambda q: self.fail("command reached responder"),
            lambda command: invoked.append(command) or "handled")
        self.assertEqual(runtime.respond("/sleep").status, "COMMAND")
        self.assertEqual(invoked, ["/sleep"])

    def test_unhandled_command_fails_closed(self):
        runtime = MultiTopicChatRuntime(lambda q: self.fail("must not generate"))
        self.assertEqual(runtime.respond("/sleep").status, "COMMAND_UNHANDLED")

    def test_responder_exception_fails_closed(self):
        def bad(_):
            raise RuntimeError("backend failure")
        runtime = MultiTopicChatRuntime(bad)
        self.assertEqual(runtime.respond("宇宙について教えて").status, "ERROR")

    def test_responder_invalid_return_fails_closed(self):
        runtime = MultiTopicChatRuntime(lambda q: None)
        self.assertEqual(runtime.respond("宇宙について教えて").status, "ERROR")


if __name__ == "__main__":
    unittest.main()
