"""Dependency-free checks for the v0.11 opt-in chat.py SKI hook."""
import unittest

from ski_runtime_v011 import (
    parse_ski_command, handle_ski_input, print_ski_diagnostic
)


def valid_executor(req, **kwargs):
    return {
        "status": "FOUND",
        "message": "構造的な関係のみ確認。真偽は未検証です。",
        "request_message_id": "msg-1",
        "response_to_message_id": "msg-1",
        "verified_fact": False,
        "human_approved": False,
        "llm_inference_invoked": False,
        "mapped_relations": 1,
    }


class SKIRuntimeTests(unittest.TestCase):
    def env(self):
        return {"LLM_CHA_SKI_ENABLED": "1"}

    def test_normal_chat_unaffected(self):
        self.assertIsNone(handle_ski_input("量子力学とは", environ=self.env()))

    def test_existing_status_unaffected(self):
        self.assertIsNone(handle_ski_input("/status", environ=self.env()))

    def test_parser(self):
        parsed = parse_ski_command("/ski CLAIM EVIDENCE | 成分は？")
        self.assertEqual(parsed["source_sd"], "CLAIM")
        self.assertEqual(parsed["target_sd"], "EVIDENCE")
        self.assertEqual(parsed["question"], "成分は？")

    def test_no_implicit_activation(self):
        called = []
        def executor(*args, **kwargs):
            called.append(True)
        result = handle_ski_input("/ski A B | テスト", environ={}, executor=executor)
        self.assertEqual(result["status"], "DISABLED")
        self.assertFalse(called)

    def test_real_dispatch_signature(self):
        calls = []
        def executor(req, **kwargs):
            calls.append((req, kwargs))
            return valid_executor(req, **kwargs)
        result = handle_ski_input("/ski A B | 質問", environ=self.env(), executor=executor)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(calls[0][0]["source_sd"], "A")
        self.assertEqual(calls[0][0]["target_sd"], "B")

    def test_forged_truth_rejected(self):
        def executor(req, **kwargs):
            result = valid_executor(req, **kwargs)
            result["verified_fact"] = True
            return result
        self.assertEqual(handle_ski_input("/ski A B", environ=self.env(),
                                          executor=executor)["status"], "ERROR")

    def test_forged_approval_rejected(self):
        def executor(req, **kwargs):
            result = valid_executor(req, **kwargs)
            result["human_approved"] = True
            return result
        self.assertEqual(handle_ski_input("/ski A B", environ=self.env(),
                                          executor=executor)["status"], "ERROR")

    def test_wrong_correlation_rejected(self):
        def executor(req, **kwargs):
            result = valid_executor(req, **kwargs)
            result["response_to_message_id"] = "forged"
            return result
        self.assertEqual(handle_ski_input("/ski A B", environ=self.env(),
                                          executor=executor)["status"], "ERROR")

    def test_does_not_call_model(self):
        def executor(req, **kwargs):
            result = valid_executor(req, **kwargs)
            result["llm_inference_invoked"] = True
            return result
        self.assertEqual(handle_ski_input("/ski A B", environ=self.env(),
                                          executor=executor)["status"], "ERROR")

    def test_invalid_input_fails_closed(self):
        for command in ("/ski", "/ski A", "/ski A B | ", "/ski " + "x" * 4010):
            with self.subTest(command=command[:30]):
                self.assertEqual(handle_ski_input(command, environ=self.env())["status"], "ERROR")

    def test_error_does_not_fall_through(self):
        def executor(req, **kwargs):
            raise OSError("unavailable")
        result = handle_ski_input("/ski A B", environ=self.env(), executor=executor)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["kind"], "SKI_DIAGNOSTIC")

    def test_output_is_explicitly_diagnostic(self):
        lines = []
        result = handle_ski_input("/ski A B", environ=self.env(),
                                  executor=valid_executor)
        self.assertTrue(print_ski_diagnostic(result, printer=lines.append))
        self.assertIn("事実未検証", lines[0])
        self.assertIn("SKI_DIAGNOSTIC_ONLY", lines[1])


if __name__ == "__main__":
    unittest.main()
