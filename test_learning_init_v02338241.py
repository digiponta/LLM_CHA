"""v0.2.33.82.4.1 regression for learning_enabled initialization."""
import ast
from pathlib import Path
import unittest

class LearningInitRegression(unittest.TestCase):
    def test_learning_enabled_initialized_before_loop(self):
        source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        loop_index = next(i for i, node in enumerate(main.body) if isinstance(node, ast.While))
        initializations = [n for n in main.body[:loop_index]
                           if isinstance(n, ast.Assign)
                           and any(isinstance(target, ast.Name) and target.id == "learning_enabled"
                                   for target in n.targets)]
        self.assertTrue(initializations, "learning_enabled must be initialized before the chat loop")

    def test_syntax(self):
        ast.parse(Path(__file__).with_name("chat.py").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
