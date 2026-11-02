"""Static compatibility smoke for the opt-in GUI/CLI RSE wiring.

Does not import torch or open a Tk display.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class RseChatWiringTests(unittest.TestCase):
    def test_python_syntax(self):
        for name in ("chat.py", "chat_gui.py"):
            with self.subTest(name=name):
                ast.parse((ROOT / name).read_text(encoding="utf-8-sig"), filename=name)
    def test_gui_passes_explicit_opt_in(self):
        source = (ROOT / "chat_gui.py").read_text(encoding="utf-8-sig")
        self.assertIn('argv.append("--rse-live-experiment")', source)
        self.assertIn('tk.BooleanVar(value=False)', source)
        self.assertIn('command=self.on_rse_toggle', source)
    def test_cli_remains_opt_in(self):
        source = (ROOT / "chat.py").read_text(encoding="utf-8-sig")
        self.assertIn('"--rse-live-experiment", action="store_true"', source)
        self.assertIn("if (\n            args.rse_live_experiment", source)
    def test_gui_existing_features_retained(self):
        source = (ROOT / "chat_gui.py").read_text(encoding="utf-8-sig")
        for label in ('text="ググる"', 'text="クリップ読込"', 'text="状態"', 'text="再起動"'):
            self.assertIn(label, source)
if __name__ == "__main__":
    unittest.main()
