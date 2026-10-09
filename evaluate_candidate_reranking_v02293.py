"""v0.2.29.3 multi-candidate raw generation and diagnostic reranking.

No training. Evaluate candidate availability separately from selection quality.
The topic-string signal is an explicit lexical feature, NOT semantic validity.
"""
import argparse,json,random,re
from collections import defaultdict
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from analyze_topic_contrastive_v02292 import answer_nll

def normalized(s):
    return re.sub(r"\s+","",s).casefold()

def features(topic,answer,nll):
    mentions=normalized(topic) in normalized(answer)
    bad_patterns=("長門有希。","そうですね。","はい。","よろしくお願いします。")
    generic=normalized(answer) in {normalized(x) for x in bad_patterns}
    repeats=bool(re.search(r"(.{3,})\1{2,}",answer))
    # NLL is lower-better, but generic fluent responses may naturally rank high.
    return {"topic_mention":mentions,"generic_exact":generic,
            "repeated_span":repeats,"nll":nll}

def rerank(candidates, mode="nll"):
    if not candidates:raise ValueError("no candidates")
    if mode=="nll":
        return min(candidates,key=lambda x:(x["nll"],x["index"]))
    if mode=="lexical":
        return max(candidates,key=lambda x:(int(x["topic_mention"]),
                        -int(x["generic_exact"]),-int(x["repeated_span"]),
                        -x["nll"],-x["index"]))
    raise ValueError("invalid mode")

@torch.no_grad()
def candidates_for(model,tok,prompt,seeds,max_new_tokens):
    prefix=tok.encode("人: "+prompt+"\nAI: ",add_bos=True)
    cases=[("greedy",0.0,None,0)]
    for seed in seeds:cases.append(("sample",0.8,40,seed))
    items=[]
    for method,temp,k,seed in cases:
        # Seed each candidate independently, including CUDA if present.
        torch.manual_seed(seed)
        ids=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                           temperature=temp,top_k=k,repetition_penalty=1.15)
        answer=tok.decode(ids[len(prefix):]).strip()
        items.append({"method":method,"seed":seed,"answer":answer})
    return items

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",default="data/topic_grounded_v02290/eval.jsonl")
    p.add_argument("--model",default="model/model-llm-cha-topic-grounded-v02291.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--samples",type=int,default=8)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--out",default="results/candidate_reranking_v02293.jsonl")
    a=p.parse_args()
    if a.samples<0 or a.max_new_tokens<1:p.error("invalid samples/tokens")
    cases=[json.loads(s) for s in Path(a.fixture).read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(a.model,device=device);model.eval()
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("vocabulary mismatch")
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    stats=defaultdict(lambda:{"count":0,"oracle":0,"greedy":0,"nll":0,"lexical":0})
    with out.open("w",encoding="utf-8") as stream:
        for case in cases:
            topic,prompt=case["topic"],case["prompt"]
            seeds=range(a.seed,a.seed+a.samples)
            proposals=candidates_for(model,tok,prompt,seeds,a.max_new_tokens)
            candidates=[]
            for idx,pitem in enumerate(proposals):
                if not pitem["answer"]:continue
                nll,_=answer_nll(model,tok,prompt,pitem["answer"])
                candidates.append({"index":idx,**pitem,**features(topic,pitem["answer"],nll)})
            if not candidates:raise RuntimeError("all candidate responses empty")
            greedy=candidates[0] if candidates[0]["method"]=="greedy" else None
            best_nll=rerank(candidates,"nll")
            best_lexical=rerank(candidates,"lexical")
            oracle=any(x["topic_mention"] for x in candidates)
            result={"topic":topic,"split":case["split"],"prompt":prompt,
                    "checkpoint":a.model,"candidate_count":len(candidates),
                    "oracle_topic_available":oracle,
                    "greedy_topic_mention":bool(greedy and greedy["topic_mention"]),
                    "nll_topic_mention":best_nll["topic_mention"],
                    "lexical_topic_mention":best_lexical["topic_mention"],
                    "greedy_answer":greedy["answer"] if greedy else None,
                    "nll_selected":best_nll["answer"],
                    "lexical_selected":best_lexical["answer"],
                    "candidates":candidates}
            stream.write(json.dumps(result,ensure_ascii=False)+"\n")
            s=stats[case["split"]];s["count"]+=1;s["oracle"]+=int(oracle)
            s["greedy"]+=int(result["greedy_topic_mention"])
            s["nll"]+=int(result["nll_topic_mention"])
            s["lexical"]+=int(result["lexical_topic_mention"])
            print(f'{case["split"]:7} {topic:9} oracle={oracle} '
                  f'greedy={result["greedy_topic_mention"]} nll={result["nll_topic_mention"]} '
                  f'lexical={result["lexical_topic_mention"]} | {result["lexical_selected"]!r}')
    for split,s in stats.items():
        print(f'{split}: oracle={s["oracle"]}/{s["count"]} '
              f'greedy={s["greedy"]}/{s["count"]} nll={s["nll"]}/{s["count"]} '
              f'lexical={s["lexical"]}/{s["count"]}')
    print("Saved:",out)
if __name__=="__main__":main()
