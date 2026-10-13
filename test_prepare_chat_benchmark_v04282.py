"""v0.4.28.2 manifest parser regression tests (synthetic, not quality evaluation)."""
import unittest
from prepare_chat_benchmark_v04282 import parse,EXPECTED

def fixture():
    lines=["# comment"]
    for cat,total in EXPECTED.items():
        mode="MULTI" if cat=="F" else "SINGLE"
        lines.append(f"## {cat}: fixture / {mode} ({total})")
        if cat=="F":
            for n in range(1,5):
                lines.append(f"# F{n} START")
                for turn in range(3):lines.append(f"質問 F{n}-{turn}")
                lines.append(f"# F{n} END / reset conversation")
        else:
            for n in range(1,total+1):
                lines.extend([f"# {cat}{n:02d}",f"質問 {cat}{n:02d}"])
    return "\n".join(lines)

class BenchmarkParserTests(unittest.TestCase):
    def test_expected_shape(self):
        result=parse(fixture())
        self.assertEqual(result["count"],64)
        self.assertEqual(len(result["groups"]),56)
        self.assertEqual(result["category_counts"],EXPECTED)
        self.assertFalse(result["chat_execution_enabled"])
    def test_comments_not_prompts(self):
        result=parse(fixture())
        self.assertEqual(result["groups"][0]["prompts"],["質問 A01"])
    def test_multi_grouped(self):
        result=parse(fixture())
        groups=[x for x in result["groups"] if x["category"]=="F"]
        self.assertEqual(len(groups),4)
        self.assertTrue(all(len(x["prompts"])==3 for x in groups))
    def test_missing_input_rejected(self):
        with self.assertRaises(ValueError):parse(fixture().replace("質問 A01",""))
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):parse(fixture().replace("# A02","# A01"))
    def test_unfinished_multi_rejected(self):
        with self.assertRaises(ValueError):parse(fixture().replace("# F1 END / reset conversation",""))
    def test_stray_prompt_rejected(self):
        with self.assertRaises(ValueError):parse("unexpected text\n"+fixture())
if __name__=="__main__":unittest.main()
