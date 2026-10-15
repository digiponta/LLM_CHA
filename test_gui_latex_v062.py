import unittest
from unittest.mock import patch
from gui_latex_v062 import split_latex, render_formula_png, insert_gui_message

class LatexGuiTests(unittest.TestCase):
    def test_split_two_formulas(self):
        text = r"状態 LATEX( |\psi \rangle ) と LATEX( \alpha+\beta )。"
        self.assertEqual(split_latex(text), [
            (False, "状態 "),
            (True, r"|\psi \rangle"),
            (False, " と "),
            (True, r"\alpha+\beta"),
            (False, "。")])

    def test_plain_text(self):
        self.assertEqual(split_latex("こんにちは。"), [(False, "こんにちは。")])

    def test_bad_formula_length(self):
        with self.assertRaises(ValueError):
            render_formula_png("x" * 501)

    def test_png_optional(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest("matplotlib is optional")
        png = render_formula_png(r"|\psi \rangle")
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))

if __name__ == "__main__":
    unittest.main()
