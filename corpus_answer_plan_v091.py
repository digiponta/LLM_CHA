"""v0.9.1 — Read-only corpus-first answer plan (no runtime monkey-patching).

Separates topical mentions from direct definitions. The output is a routing
plan, not a generated factual answer or proof of model internalization.
"""
import argparse
import json
import re
from pathlib import Path

def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[。！？!?])|\n", text) if s.strip()]

def normalize(text):
    return re.sub(r"\s+", "", str(text or "")).rstrip("、。？！?!")

def route(question, corpus):
    q=normalize(question)
    if not q:
        return {"route":"INVALID_INPUT","reason":"EMPTY_QUESTION","corpus_evidence":[]}
    # Keep the original text and provenance; topical mentions are not direct definitions.
    topic=q
    for suffix in ("とは","って何","について教えて","について"):
        if topic.endswith(suffix):
            topic=topic[:-len(suffix)]
            break
    topic=topic.strip()
    if not topic:
        return {"route":"INVALID_INPUT","reason":"EMPTY_SUBJECT","corpus_evidence":[]}
    hits=[{"source":"data/data-nagato.txt","text":s}
          for s in sentences(corpus) if topic in s]
    # Strict enough to avoid promoting analogies or incidental mentions.
    definition=re.compile(r"^"+re.escape(topic)+r"(?:とは|は|というのは)[、\s]*(?:[^。]{2,})(?:である|です|を指す|のこと)(?:。|$)")
    direct=[h for h in hits if definition.search(h["text"])]
    is_definition=q.endswith(("とは","って何"))
    if is_definition and hits and not direct:
        return {"route":"CORPUS_THEN_EXTERNAL_DEFINITION",
                "reason":"TOPIC_MENTIONED_BUT_NO_DIRECT_DEFINITION",
                "topic":topic,"corpus_evidence":hits,
                "external_lookup_required":True,
                "corpus_is_verified_fact":False}
    if direct:
        return {"route":"CORPUS_DEFINITION_CANDIDATE","reason":"DIRECT_DEFINITION_PATTERN",
                "topic":topic,"corpus_evidence":direct,
                "external_lookup_required":False,
                "corpus_is_verified_fact":False}
    if hits:
        return {"route":"CORPUS_CONTEXT_CANDIDATE","reason":"TOPIC_MENTIONED",
                "topic":topic,"corpus_evidence":hits,
                "external_lookup_required":False,
                "corpus_is_verified_fact":False}
    return {"route":"EXTERNAL_FALLBACK_CANDIDATE","reason":"TOPIC_NOT_IN_CORPUS",
            "topic":topic,"corpus_evidence":[],
            "external_lookup_required":True,"corpus_is_verified_fact":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--corpus",default="data/data-nagato.txt")
    args=parser.parse_args()
    path=Path(args.corpus)
    if not path.is_file():
        print(json.dumps({"route":"CORPUS_NOT_FOUND","path":str(path)},ensure_ascii=False,indent=2))
        return
    result=route(args.question,path.read_text(encoding="utf-8-sig"))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
