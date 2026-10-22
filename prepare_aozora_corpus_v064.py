#!/usr/bin/env python3
"""Aozora Bunko -> auditable Japanese training corpus for LLM_CHA.

Explicit allowlisted work manifest only. No auto-promotion, /sleep, or GPU
fine-tuning. All source text and rights metadata remain traceable.
"""
import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

VERSION = "v0.6.4"
MAX_ZIP_BYTES = 16 * 1024 * 1024
MAX_TEXT_BYTES = 12 * 1024 * 1024
AOZORA_HOSTS = {"www.aozora.gr.jp", "aozora.gr.jp"}
RUBY = re.compile(r"《[^》\n]*》")
ANNOTATION = re.compile(r"［＃[^］\n]*］")
BLANKS = re.compile(r"\n{3,}")


def validate_work(item):
    required = ("work_id", "title", "author", "zip_url", "rights_checked",
                "rights_basis", "card_url")
    if not isinstance(item, dict) or any(not item.get(k) for k in required):
        raise ValueError("work requires ID/title/author/URL/card/rights")
    if item["rights_checked"] is not True or item["rights_basis"] != "public_domain":
        raise ValueError("only explicitly reviewed public-domain works supported")
    if not re.fullmatch(r"[0-9A-Za-z_-]{1,64}", str(item["work_id"])):
        raise ValueError("unsafe work_id")
    for key in ("zip_url", "card_url"):
        url = urllib.parse.urlsplit(item[key])
        if (url.scheme != "https" or url.hostname not in AOZORA_HOSTS
                or url.username or url.password or url.port not in (None, 443)):
            raise ValueError("only official HTTPS Aozora URLs permitted")
    if not item["zip_url"].lower().split("?")[0].endswith(".zip"):
        raise ValueError("zip_url must end in .zip")
    return item


def decode_aozora(raw):
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("cannot decode work as UTF-8 or CP932")


def extract_zip(blob):
    if len(blob) > MAX_ZIP_BYTES:
        raise ValueError("archive too large")
    with zipfile.ZipFile(BytesIO(blob)) as archive:
        candidates = [n for n in archive.namelist()
                      if n.lower().endswith(".txt") and not n.startswith("__MACOSX/")]
        if len(candidates) != 1:
            raise ValueError("expected exactly one text file in archive")
        info = archive.getinfo(candidates[0])
        if info.file_size > MAX_TEXT_BYTES:
            raise ValueError("uncompressed text too large")
        with archive.open(info) as fp:
            raw = fp.read(MAX_TEXT_BYTES + 1)
        if len(raw) > MAX_TEXT_BYTES:
            raise ValueError("uncompressed text too large")
    return decode_aozora(raw)


def clean_aozora(text):
    """Retain original text separately; produce a conservative reading view."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Header/footer separators in the standard Aozora text format.
    parts = re.split(r"(?m)^-{10,}\s*$", text)
    if len(parts) >= 3:
        text = "\n".join(parts[2:])
    text = re.split(r"(?m)^底本[：:]|^入力[：:]|^校正[：:]", text, maxsplit=1)[0]
    text = ANNOTATION.sub("", text)
    text = RUBY.sub("", text).replace("｜", "")
    return BLANKS.sub("\n\n", text).strip()


def chunk_text(text, max_chars=900):
    """Split by paragraph without dropping any text; long paragraphs are split."""
    if max_chars < 64:
        raise ValueError("max_chars must be >= 64")
    out, current = [], ""
    for paragraph in text.split("\n"):
        line = paragraph + "\n"
        if current and len(current) + len(line) > max_chars:
            out.append(current.rstrip("\n"))
            current = ""
        while len(line) > max_chars:
            if current:
                out.append(current.rstrip("\n"))
                current = ""
            out.append(line[:max_chars])
            line = line[max_chars:]
        current += line
    if current.strip():
        out.append(current.rstrip("\n"))
    return [x for x in out if x.strip()]


def download_zip(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "LLM_CHA-AozoraCorpus/0.6.4 (research; limited requests)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if urllib.parse.urlsplit(response.geturl()).hostname not in AOZORA_HOSTS:
            raise ValueError("redirect outside official Aozora domain")
        data = response.read(MAX_ZIP_BYTES + 1)
    if len(data) > MAX_ZIP_BYTES:
        raise ValueError("archive too large")
    return data


def process_work(work, blob, max_chars=900):
    validate_work(work)
    raw = extract_zip(blob)
    cleaned = clean_aozora(raw)
    if not cleaned:
        raise ValueError("empty cleaned work")
    source_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    records = []
    for i, fragment in enumerate(chunk_text(cleaned, max_chars), 1):
        digest = hashlib.sha256(fragment.encode("utf-8")).hexdigest()
        records.append({
            "dataset_version": VERSION,
            "semantic_id": f"AOZORA-{work['work_id']}-{i:06}",
            "llm_id": "LLM_CHA",
            "text": fragment,
            "language": "ja",
            "truth_state": "EXTERNAL_UNVERIFIED",
            "train_ready": False,
            "auto_promote": False,
            "natural_language_refs": [{
                "text_id": f"TXT-{digest[:24]}",
                "language": "ja", "relation": "source",
                "uri": f"nl://LLM_CHA/aozora/{work['work_id']}/{i:06}",
                "version": 1, "content_hash": "sha256:" + digest
            }],
            "provenance": {
                "work_id": work["work_id"], "title": work["title"],
                "author": work["author"], "card_url": work["card_url"],
                "zip_url": work["zip_url"], "source_sha256": source_sha,
                "rights_basis": work["rights_basis"], "chunk_index": i
            }
        })
    return raw, records


def build(manifest_path, output_dir, max_works=10, max_chars=900, delay=2.0):
    if max_works < 1 or max_works > 100 or delay < 0:
        raise ValueError("invalid max_works or delay")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise ValueError("manifest must be a JSON array")
    selected = manifest[:max_works]
    for item in selected:
        validate_work(item)
    ids = [str(item["work_id"]) for item in selected]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate work_id")
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    data_path = dest / "aozora_semantic_corpus.jsonl"
    raw_dir = dest / "raw"
    raw_dir.mkdir(exist_ok=True)
    records = []
    for i, item in enumerate(selected):
        if i and delay:
            time.sleep(delay)
        blob = download_zip(item["zip_url"])
        raw, chunks = process_work(item, blob, max_chars=max_chars)
        (raw_dir / (str(item["work_id"]) + ".txt")).write_text(raw, encoding="utf-8")
        records.extend(chunks)
        print(f"{item['work_id']}: {len(chunks)} chunks")
    # Only publish full dataset after all works succeed.
    temp = data_path.with_suffix(".tmp")
    temp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                    encoding="utf-8")
    temp.replace(data_path)
    print(json.dumps({"works": len(selected), "chunks": len(records),
                      "output": str(data_path), "weights_modified": False},
                     ensure_ascii=False, indent=2))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="data/aozora_v064")
    parser.add_argument("--max-works", type=int, default=10)
    parser.add_argument("--chunk-chars", type=int, default=900)
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    build(args.manifest, args.output, max_works=args.max_works,
          max_chars=args.chunk_chars, delay=args.delay)


if __name__ == "__main__":
    main()
