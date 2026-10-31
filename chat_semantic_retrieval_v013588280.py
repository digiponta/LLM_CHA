"""Minimal read-only routing of three registered-memory questions."""
from pathlib import Path
from sense_retrieval_probe_v013588279 import probe,QUESTIONS

def route(question,root="."):
    if str(question).strip() not in QUESTIONS:return None
    root=Path(root)
    paths=[root/"data/semantic_propositions_v1090.jsonl",
           root/"data/unified_semantic_memory_v1090.jsonl",
           root/"data/sense_registration_provenance_v013588273.json"]
    if not all(p.is_file() for p in paths):
        return {"answer":"登録知識の保存先を確認できません。","route":"MEMORY_SOURCE_NOT_FOUND"}
    try:
        result=probe(*paths,questions=(question,))
        row=result["answers"][0]
        return {"answer":row["answer"],"route":"MEMORY_"+row["route"]}
    except (OSError,ValueError,KeyError) as e:
        return {"answer":"登録知識を確認できません。","route":"MEMORY_READ_ERROR"}
