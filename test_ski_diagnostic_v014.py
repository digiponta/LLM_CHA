"""v0.14: SKI profile visibility checks for all real chat diagnostic modes."""
import unittest

from ski_runtime_v011 import handle_ski_input, print_ski_diagnostic
from ski_auto_route_v012 import display_auto_diagnostic
from ski_context_route_v013 import display_context_diagnostic


class SKIDiagnosticProfileRuntimeTests(unittest.TestCase):
    def test_manual_displays_profile(self):
        output = []
        print_ski_diagnostic({
            "status": "FOUND", "message": "構造的照会の診断",
            "ski_diagnostic_profile": "ski-diagnostic-v0.14",
        }, printer=output.append)
        self.assertIn("ski_profile=ski-diagnostic-v0.14", output[1])

    def test_auto_displays_profile(self):
        output = []
        display_auto_diagnostic({
            "status": "FOUND", "message": "構造的照会の診断",
            "ski_diagnostic_profile": "ski-diagnostic-v0.14",
        }, printer=output.append)
        self.assertIn("ski_profile=ski-diagnostic-v0.14", output[1])

    def test_context_displays_profile(self):
        output = []
        display_context_diagnostic({
            "status": "FOUND", "message": "構造的照会の診断",
            "ski_diagnostic_profile": "ski-diagnostic-v0.14",
        }, printer=output.append)
        self.assertIn("ski_profile=ski-diagnostic-v0.14", output[1])

    def test_explicit_v011_command_preserves_v014_profile(self):
        def executor(request, **kwargs):
            return {
                "status": "FOUND", "message": "構造的照会の診断",
                "verified_fact": False, "human_approved": False,
                "llm_inference_invoked": False,
                "request_message_id": "REQ",
                "response_to_message_id": "REQ",
                "ski_diagnostic_profile": "ski-diagnostic-v0.14",
            }
        r = handle_ski_input(
            "/ski CLAIM EVIDENCE | 問い合わせ",
            environ={"LLM_CHA_SKI_ENABLED": "1"}, executor=executor)
        self.assertEqual(r["status"], "FOUND")
        self.assertEqual(r["ski_diagnostic_profile"], "ski-diagnostic-v0.14")


if __name__ == "__main__":
    unittest.main()
