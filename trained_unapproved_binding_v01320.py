"""v0.13.20 checkpoint-bound unapproved evidence lookup.

Conservative: returns SOURCE QUOTATIONS, never a generated definition.
The checkpoint must contain the exact QA pair fingerprint, and explicit
truth blocking / REJECTED approval remains authoritative.
"""
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl
from online_train import pair_fingerprint, checkpoint_trained_fingerprints

QA_SOURCES=(Path("results/unapproved_semantic_qa_v01314.jsonl"),
            Path("results/unapproved_mention_qa_v01315.jsonl"),
            Path("results/unapproved_stratified_pairs_v01318.jsonl"))

def lookup(focus,checkpoint,ledger_path,qa_paths=QA_SOURCES,truth_block=False):
    if truth_block or not focus or not Path(checkpoint).exists():
        return None
    state={x["knowledge_id"]:x.get("approval_state","UNAPPROVED")
           for x in load_jsonl(Path(ledger_path))}
    bound=checkpoint_trained_fingerprints(Path(checkpoint))
    for path in qa_paths:
        for row in load_jsonl(Path(path)):
            if row.get("subject")!=focus:continue
            kid=row.get("knowledge_id")
            approval=state.get(kid,row.get("approval_state","UNAPPROVED"))
            if approval!="UNAPPROVED":continue
            if row.get("truth_state") not in ("UNVERIFIED",None):continue
            fp=pair_fingerprint(str(row.get("user","")),str(row.get("assistant","")))
            if fp not in bound:continue
            source_text=str(row.get("source_text","")).strip()
            if not source_text:continue
            return {"state":"TRAINED_UNAPPROVED","subject":focus,
                    "knowledge_id":kid,"source_text":source_text,
                    "source":row.get("source",""),
                    "pair_fingerprint":fp,"approval_state":approval,
                    "truth_state":"UNVERIFIED"}
    return None

def format_quotation(evidence):
    return "【未承認・事実未検証の原文】"+evidence["source_text"]
