import ast
import unittest
from pathlib import Path
class AspectRuntimeTests(unittest.TestCase):
    def test_wiring(self):
        s=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(s)
        self.assertIn("expanded_aspect(wiki_for_aspect, aspect)",s)
        self.assertIn('wiki_for_aspect.get("title") != last_explicit_knowledge_topic',s)
    def test_gui(self):
        s=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(s)
        self.assertIn('env["LLM_CHA_ASPECT_EVIDENCE"] = "1"',s)
if __name__=="__main__":unittest.main()
