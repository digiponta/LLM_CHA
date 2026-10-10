import tempfile,unittest
from pathlib import Path
from semantic_api_discovery_v023338 import discover,evaluate_contract
class DiscoveryTests(unittest.TestCase):
    def test_find_symbols_without_import(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"memory.py"
            p.write_text("def approve_candidate(candidate_id):\n    raise RuntimeError('MUST NOT EXECUTE')\n\ndef search_semantic(query):\n    return []\n",encoding="utf8")
            report=discover(td)
            names={x["name"] for x in report["symbols"]}
            self.assertIn("approve_candidate",names)
            self.assertIn("search_semantic",names)
            self.assertFalse(report["live_integration"])
            review=evaluate_contract(report)
            self.assertFalse(review["automatically_bindable"])
    def test_parse_error_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/"broken.py").write_text("def foo(\n",encoding="utf8")
            report=discover(td)
            self.assertEqual(report["errors"][0]["error"],"SyntaxError")
    def test_skips_virtual_env(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/".venv"/"fake.py";p.parent.mkdir()
            p.write_text("def approve_candidate(): pass")
            self.assertEqual(discover(td)["symbols"],[])
    def test_directory_must_exist(self):
        with self.assertRaises(ValueError):discover("/no/such/source/root")
if __name__=="__main__":unittest.main()
