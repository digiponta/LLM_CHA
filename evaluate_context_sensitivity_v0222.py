"""v0.2.22 context sensitivity: likelihood, generation, and candidate selection.

No training. Controlled identical last question with 4 history variants.
Scores use independent topic-reference answers, not model-produced labels.
"""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from diagnose_models_v0213 import score_answer
from diagnose_eos_decoding_v0216 import decode_trace
from candidate_reranker_v0220 import rank_candidates
from types import SimpleNamespace

SCENARIOS=[
 {"name":"sf","history":[("最近、SF小説を読んでいます","どんな作品を読んでいるの？"),("宇宙探査がテーマです","宇宙探査のどんなところが面白い？")],
  "reference":"宇宙探査では、未知の惑星での発見や仲間との協力が物語の魅力になるね。","terms":["宇宙","探査","惑星","SF"]},
 {"name":"curry","history":[("今日は料理をしました","何を作ったの？"),("カレーを作りました","どんな具材を使ったの？")],
  "reference":"カレーなら、野菜や香辛料の組み合わせによって味わいが変わるね。","terms":["料理","カレー","野菜","香辛料"]},
 {"name":"music","history":[("音楽を聴いています","どんな音楽が好き？"),("クラシック音楽です","どんな楽器が好き？")],
  "reference":"クラシック音楽なら、演奏や楽器の音色の違いを楽しめるね。","terms":["音楽","クラシック","演奏","楽器"]},
 {"name":"none","history":[],"reference":"どの話のことか、もう少し教えて。","terms":[]},
]
QUESTION="その話を続けて"

def prompt_for(history):
    return "\n".join([x for q,a in history for x in ("人: "+q,"AI: "+a)]+["人: "+QUESTION])

def lexical_hits(text,terms):
    return [t for t in terms if t in text]

def report_for(model,tok,*,max_new_tokens=48,seed=42):
    cases=[]
    for sc in SCENARIOS:
        history=sc["history"];full=prompt_for(history)
        nll=score_answer(model,tok,full,sc["reference"])
        without=score_answer(model,tok,"人: "+QUESTION,sc["reference"])
        if nll is None or without is None:raise ValueError("Reference exceeded context")
        greedy=decode_trace(model,tok,full,temperature=0,top_k=40,seed=seed,max_new_tokens=max_new_tokens)
        # Samples support selection diagnosis, not claim quality improvement.
        samples=[decode_trace(model,tok,full,temperature=.7,top_k=40,seed=seed+i,max_new_tokens=max_new_tokens) for i in (1000,1001)]
        generated=[greedy]+samples
        cand=[SimpleNamespace(text=g["generated"],mean_confidence=1.0,min_confidence=1.0,mean_top2_margin=1.0) for g in generated]
        # Rank text features in isolation. Synthetic neutral confidences must not be mistaken
        # for model confidence; this is an explicit ranking-only ablation.
        ranked,scores=rank_candidates(QUESTION,cand,history)
        selected=next(i for i,x in enumerate(cand) if x is ranked[0])
        cases.append({"scenario":sc["name"],"prompt":full,
          "reference":sc["reference"],"nll_with_context":round(nll[0]/nll[1],5),
          "nll_without_context":round(without[0]/without[1],5),
          "nll_gain":round((without[0]-nll[0])/nll[1],5),
          "generations":[{"method":k,"text":g["generated"],"topic_hits":lexical_hits(g["generated"],sc["terms"])} for k,g in zip(("greedy","sample_1","sample_2"),generated)],
          "reranker_selected":selected,"reranker_scores":scores,
          "ranking_note":"model confidences neutralized to 1: text-feature-only ablation"})
    wrong_topic={}
    for case in cases:
        if case["scenario"]=="none":continue
        wrong_topic[case["scenario"]]=sum(bool(case["generations"][0]["topic_hits"]) for _ in [0])
    return {"cases":cases,"topic_hits_greedy_by_scenario":wrong_topic,
            "note":"Reference NLL, free generation and ranking-only ablation measure different properties. No causal proof from 4 synthetic scenarios."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-foundation-dialogue-v0218.pt","model/model-llm-cha-response-quality-v0221.pt"])
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/context_sensitivity_v0222.json")
    p.add_argument("--max-new-tokens",type=int,default=48)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(a.tokenizer);results={}
    for path in a.models:
        model,_=LanguageModel.load_checkpoint(path,device);model.eval()
        results[path]=report_for(model,tok,max_new_tokens=a.max_new_tokens,seed=a.seed)
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    output={"device":str(device),"question":QUESTION,"models":results}
    dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({m:[{"scenario":x["scenario"],"gain":x["nll_gain"],"greedy":x["generations"][0]["text"],"hits":x["generations"][0]["topic_hits"],"selected":x["reranker_selected"]} for x in r["cases"]] for m,r in results.items()},ensure_ascii=False,indent=2))
    print("Detailed records:",dst)
if __name__=="__main__":main()
