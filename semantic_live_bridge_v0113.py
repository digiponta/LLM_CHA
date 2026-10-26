"""v0.11.3 experimental real model + subject-keyed memory dialogue integration.

Safe standalone CLI: does not modify chat.py, memory, checkpoint or /sleep.
A corpus hit proves retrieval only, NOT factual approval or semantic divergence.
Differences without an approved equivalence assertion are UNKNOWN, not DIVERGENT.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from semantic_subject_preferences_v0117 import SubjectPreferenceBridge
from semantic_equivalence_router_v0111 import EquivalenceAssertion
from semantic_reconciliation_v0110 import canonical_form
from generation_quality_gate_v0114 import assess_generation

def extract_subject(question):
    question=question.strip()
    for suffix in ("とは何ですか？","とは何ですか?","について教えて","とは","は何ですか？","は何ですか?"):
        if question.endswith(suffix):
            return question[:-len(suffix)].strip()
    return question

def process_turn(question, *, generate, retrieve, bridge, subject=None, context="", regenerate=None):
    """Dependency-injected integration for deterministic tests.

    retrieve(subject) must return a result with hit/answer/provenance.
    generate(question) returns text or a decoder result with .text.
    """
    if not isinstance(question,str) or not question.strip():
        raise ValueError("nonempty question required")
    resolved_subject=subject.strip() if isinstance(subject,str) and subject.strip() else extract_subject(question)
    evidence=retrieve(resolved_subject)
    generated=generate(question)
    generated_text=generated if isinstance(generated,str) else generated.text
    if not isinstance(generated_text,str) or not generated_text.strip():
        return {"action":"GENERATION_UNAVAILABLE","answer":None,"subject":resolved_subject}
    quality=assess_generation(generated)
    retries=[]
    if quality.status!="VALID" and regenerate is not None:
        for attempt in range(1,3):
            candidate=regenerate(question,attempt)
            checked=assess_generation(candidate)
            retries.append({"attempt":attempt,"status":checked.status,"reasons":list(checked.reasons)})
            if checked.status=="VALID":
                generated=candidate
                generated_text=candidate if isinstance(candidate,str) else candidate.text
                quality=checked
                break
    if quality.status!="VALID":
        return {"action":"GENERATION_QUALITY_REVIEW","answer":None,
                "subject":resolved_subject,"quality_status":quality.status,
                "quality_reasons":list(quality.reasons),
                "candidate_text":generated_text,
                "retry_history":retries,
                "memory_reference":evidence.answer if evidence.hit else None,
                "memory_approval":"NOT_ATTESTED",
                "message":"正常な生成回答を得られませんでした。未検証のSemantic Memory参考情報を表示します。生成文の調停は行いません。\n"+(evidence.answer if evidence.hit else "Semantic Memoryに該当記録がありません。") }
    if not evidence.hit or not evidence.answer.strip():
        return {"action":"MEMORY_MISS","answer":generated_text,"subject":resolved_subject,
                "warning":"Model output is unverified"}
    # No automatic proof of semantic equivalence or verified factuality.
    comparison_options={"context":context}
    if isinstance(bridge,SubjectPreferenceBridge):
        comparison_options["subject"]=resolved_subject
    outcome=bridge.compare(question,generated_text,evidence.answer,
                           EquivalenceAssertion("UNKNOWN",provenance_id=evidence.provenance),
                           **comparison_options)
    outcome["subject"]=resolved_subject
    outcome["memory_provenance"]=evidence.provenance
    outcome["memory_approval"]="NOT_ATTESTED"
    if retries:
        outcome["retry_history"]=retries
    return outcome

def build_services(checkpoint_loader, memory_path, root, max_tokens):
    from retrieval_first_runtime_v1012161 import resolve_subject
    from semantic_decode_v0101 import decode
    model,tokenizer=checkpoint_loader()
    memory=Path(memory_path)
    if not memory.is_file():
        raise FileNotFoundError(f"Memory file not found: {memory}")
    def generate(question):
        prompt="人: "+question+"\nAI: "
        return decode(model,tokenizer,prompt,beam_width=3,max_new_tokens=max_tokens)
    def retrieve(subject):
        return resolve_subject(memory,subject)
    def regenerate(question,attempt):
        prompt="人: "+question+"\nAI: "
        limit=max_tokens*(2 if attempt==1 else 3)
        width=3 if attempt==1 else 1
        return decode(model,tokenizer,prompt,beam_width=width,max_new_tokens=limit)
    return generate,retrieve,SubjectPreferenceBridge(root),regenerate

def main():
    p=argparse.ArgumentParser(description="v0.11.3 isolated live model ↔ Semantic Memory experiment")
    p.add_argument("--memory",default="data/subject_keyed_corpus_memory_v101216.jsonl")
    p.add_argument("--root",default="data/semantic_dialogue_v0113")
    p.add_argument("--max-tokens",type=int,default=48)
    p.add_argument("--factory",default="decoder_factory_v0101:load")
    args=p.parse_args()
    import importlib
    mod,name=args.factory.split(":",1)
    generate,retrieve,bridge,regenerate=build_services(getattr(importlib.import_module(mod),name),
                                              args.memory,args.root,args.max_tokens)
    print("LLM_CHA experimental semantic reconciliation /exit to quit")
    while True:
        question=input("You> ").strip()
        if question=="/exit":break
        subject=input("Subject (Enter=auto)> ").strip() or None
        result=process_turn(question,generate=generate,retrieve=retrieve,bridge=bridge,subject=subject,regenerate=regenerate)
        print(result.get("message",json.dumps(result,ensure_ascii=False)))
        if result["action"]=="ASK_USER":
            selection=input("Decision [prefer_a/prefer_b/both_contextual/neither/skip]> ").strip()
            if selection in ("prefer_a","prefer_b","both_contextual","neither"):
                context=input("Context> ").strip() if selection=="both_contextual" else ""
                try:
                    print(json.dumps(bridge.review(result["ticket_id"],selection,context=context),
                                     ensure_ascii=False))
                except ValueError as exc:
                    print("Review not saved:",exc)
            else:
                print("Pending: no decision saved")
if __name__=="__main__":main()
