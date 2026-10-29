"""v0.13.58.65: retrieval-grounded response evaluation.

Compares unchanged base LLM generation, directly retrieved *training* answers,
and optional context-grounded generation. Unknown gate is deliberately
conservative and marked uncalibrated; scores are NOT probabilities.
No holdout references are used in retrieval or generation.
"""
import argparse,csv,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from compare_japanese_semantic_v0135863 import MODEL,MODES,topk
from rerank_question_intent_v0135864 import rerank
from retrieve_question_top3_v0135861 import norm

def decide(ranked,min_score=0.85,min_margin=0.0):
    if not ranked:return {"accepted":False,"reason":"NO_CANDIDATES","hit":None}
    h=ranked[0]
    if h["score"]<min_score:return {"accepted":False,"reason":"LOW_BASE_SCORE","hit":None}
    if len(ranked)>1 and h["adjusted_score"]-ranked[1]["adjusted_score"]<min_margin:
        return {"accepted":False,"reason":"LOW_MARGIN","hit":None}
    return {"accepted":True,"reason":"HEURISTIC_ACCEPT_UNCALIBRATED","hit":h}

def encode_context(question,hit):
    return ("参考会話（現在の質問とは異なる可能性があります）\n"
            f"利用者: {hit['question']}\n応答: {hit['answer']}\n"
            f"現在の利用者: {question}\n応答: ")

def compare(a):
    if a.output.exists():raise FileExistsError(a.output)
    train,held,protected=dataset(a.source)
    if len(train)!=56 or len(held)!=8:raise ValueError("requires 56 train/8 holdout")
    if {norm(x["user"]) for x in train}&{norm(x["user"]) for x in held}:
        raise ValueError("question leakage")
    import torch
    from sentence_transformers import SentenceTransformer
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from train_token_equivalence_v0135852 import predict
    device="cpu" if a.cpu or not torch.cuda.is_available() else "cuda"
    sem=SentenceTransformer(MODEL,device=device,trust_remote_code=False)
    qp,dp=MODES["semantic"]
    emb_train=sem.encode([dp+x["user"] for x in train],batch_size=16,normalize_embeddings=True)
    emb_held=sem.encode([qp+x["user"] for x in held],batch_size=16,normalize_embeddings=True)
    tok=Tokenizer.load(str(a.tokenizer))
    llm,_=LanguageModel.load_checkpoint(str(a.base),device=torch.device(device))
    if llm.vocab_size!=tok.vocab_size:raise ValueError("tokenizer mismatch")
    llm.eval()
    rows=[]
    with torch.inference_mode():
        for q,hits in zip(held,topk(emb_held,emb_train,train,k=56)):
            ranked=rerank(q["user"],hits,a.intent_penalty,a.valence_penalty)
            gate=decide(ranked,a.min_score,a.min_margin)
            baseline=predict(llm,tok,q,a.max_new_tokens)["generated"]
            direct=(gate["hit"]["answer"] if gate["accepted"] else None)
            # Prompt-grounded generation is experimental; do not present as supported
            # or proven unless actually run with --grounded. It never uses gold response.
            grounded=None
            if a.grounded and gate["accepted"]:
                from dialogue_format_v0135817 import prompt_for
                context=encode_context(q["user"],gate["hit"])
                prefix=tok.encode(prompt_for(context),add_bos=True)
                ids=llm.generate(prefix,max_new_tokens=a.max_new_tokens,
                     eos_id=tok.eos_id,temperature=0.0,repetition_penalty=1.0)[len(prefix):]
                if ids and ids[-1]==tok.eos_id:ids=ids[:-1]
                grounded=tok.decode(ids)
            rows.append({"id":q["id"],"question":q["user"],"reference":q["assistant"],
                "baseline":baseline,"retrieval_direct":direct,"grounded_llm":grounded,
                "accepted":gate["accepted"],"decision":gate["reason"],
                "retrieval_hit_id":gate["hit"]["id"] if gate["accepted"] else None,
                "retrieval_hit_question":gate["hit"]["question"] if gate["accepted"] else None,
                "base_score":gate["hit"]["score"] if gate["accepted"] else None,
                "adjusted_score":gate["hit"]["adjusted_score"] if gate["accepted"] else None,
                "top3":ranked[:3]})
    a.output.mkdir(parents=True,exist_ok=False)
    payload={"version":"v0.13.58.65","model":MODEL,"query_count":len(rows),
        "accepted_count":sum(r["accepted"] for r in rows),
        "unknown_count":sum(not r["accepted"] for r in rows),
        "gate_is_calibrated":False,"grounded_generation_enabled":a.grounded,
        "development_only":True,"production_approved":False,
        "warning":"Do not treat high cosine as evidence that a retrieved answer is valid. Human relevance and answer correctness review required.",
        "results":rows}
    (a.output/"comparison.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (a.output/"review.csv").open("w",encoding="utf-8-sig",newline="") as f:
        cols=["id","question","reference","accepted","decision","retrieval_hit_id","retrieval_hit_question",
            "baseline","retrieval_direct","grounded_llm","baseline_quality","direct_quality","grounded_quality",
            "review_notes"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in rows:w.writerow({k:r.get(k) for k in cols})
    print(json.dumps({"accepted":payload["accepted_count"],"unknown":payload["unknown_count"],
       "grounded":a.grounded,"output":str(a.output)},ensure_ascii=False))
    for r in rows:
        print(f'{r["id"]}: {r["question"]}\n BASE: {r["baseline"]}\n HIT: {r["retrieval_hit_question"]}\n DIRECT: {r["retrieval_direct"]}\n GROUNDED: {r["grounded_llm"]}')
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/retrieval_response_v0135865"))
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--min-score",type=float,default=.85)
    p.add_argument("--min-margin",type=float,default=0)
    p.add_argument("--intent-penalty",type=float,default=.12)
    p.add_argument("--valence-penalty",type=float,default=.08)
    p.add_argument("--cpu",action="store_true")
    p.add_argument("--grounded",action="store_true",help="experimental context prompt; not trained for in-context instructions")
    a=p.parse_args()
    if not 0<=a.min_score<=1 or not 0<=a.min_margin<=1: p.error("invalid gate thresholds")
    compare(a)
if __name__=="__main__":main()
