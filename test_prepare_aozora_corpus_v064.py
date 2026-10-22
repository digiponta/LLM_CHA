import io
import json
import unittest
import zipfile
from prepare_aozora_corpus_v064 import (
    validate_work, extract_zip, clean_aozora, process_work, chunk_text
)

WORK = {
    "work_id": "123", "title": "例題", "author": "架空",
    "zip_url": "https://www.aozora.gr.jp/cards/000001/files/123_1.zip",
    "card_url": "https://www.aozora.gr.jp/cards/000001/card123.html",
    "rights_checked": True, "rights_basis": "public_domain"
}

def archive(text):
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("sample.txt", text.encode("cp932"))
    return buff.getvalue()

class AozoraTests(unittest.TestCase):
    def test_source_reference_and_evidence(self):
        raw, rows = process_work(WORK, archive("吾輩《わがはい》は猫である。\n二行目。"), 128)
        self.assertIn("《わがはい》", raw)
        self.assertIn("吾輩は猫である。", rows[0]["text"])
        self.assertNotIn("《", rows[0]["text"])
        self.assertEqual(rows[0]["natural_language_refs"][0]["relation"], "source")
        self.assertFalse(rows[0]["train_ready"])
        self.assertFalse(rows[0]["auto_promote"])
        self.assertEqual(rows[0]["provenance"]["title"], "例題")

    def test_reject_unreviewed_rights(self):
        item = dict(WORK, rights_checked=False)
        with self.assertRaises(ValueError): validate_work(item)

    def test_reject_license_mismatch(self):
        item = dict(WORK, rights_basis="permission_only")
        with self.assertRaises(ValueError): validate_work(item)

    def test_reject_untrusted_domain(self):
        item = dict(WORK, zip_url="https://example.com/book.zip")
        with self.assertRaises(ValueError): validate_work(item)

    def test_reject_multiple_entries(self):
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w") as z:
            z.writestr("a.txt", "a")
            z.writestr("b.txt", "b")
        with self.assertRaises(ValueError): extract_zip(buff.getvalue())

    def test_chunk_preserves_text(self):
        text = "あ" * 200 + "\n" + "い" * 200
        chunks = chunk_text(text, 100)
        self.assertTrue(all(len(x) <= 100 for x in chunks))
        self.assertEqual("".join(x.replace("\n", "") for x in chunks),
                         text.replace("\n", ""))

    def test_annotations(self):
        self.assertEqual(clean_aozora("吾輩《わがはい》［＃注記］｜猫"),
                         "吾輩猫")


if __name__ == "__main__":
    unittest.main()
