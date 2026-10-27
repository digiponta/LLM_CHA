"""v0.13.40 multi-candidate RPC response reranking experiment.
No reference answer enters selection. No training, approval or checkpoint update.
"""
import argparse,json
from pathlib import Path
import torch
from chat import generate_reply
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import USER_PREFIX, AI_PREFIX
from sweep_rpc_decoding_v01337 import choose_probes,repetition,generic
from train_rpc_dialogue_sft_v01334 import read_rows
from evaluate_rpc_context_evidence_v01339 import encode_case,score
from evaluate_rpc_context_v01338 import char_similarity

def ranking_score(nll, rep, is_generic, empty, truncated):
    if empty:return -1e9
    return -nll-2.0*rep-0.4*int(is_generic)-0.25*int(truncated)

def rank_candidates(candidates):
    return min(candidates,key=lambda c:(-c["rank_score"],c["index"]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("results/rpc_sweep_v01336/rpc_candidate_100000.pt"))
    p.add_argument("--data",type=Path,default=Path("results/rpc_sft_full_v01333/rpc_sft_val_v01333.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_response_ranking_v01340.json"))
    p.add_argument("--limit",type=int,default=48)
    p.add_argument("--candidates",type=int,default=5)
    p.add_argument("--seed",type=int,default=1337)
    p.add_argument("--max-new-tokens",type=int,default=64)
    a=p.parse_args()
    if a.limit<1 or a.candidates<2 or a.max_new_tokens<1:p.error("invalid limits")
    for f in (a.model,a.data,a.tokenizer):
        if not f.exists():p.error(f"missing {f}")
    if a.output.exists():p.error("output exists")
    probes=choose_probes(read_rows(a.data),a.limit)
    if len(probes)<a.limit:p.error("not enough probes")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    model.eval(); details=[]
    with torch.no_grad():
        for i,row in enumerate(probes):
            generated=[]
            prompt=f"{USER_PREFIX}{row['user']}\n{AI_PREFIX}"
            for j in range(a.candidates):
                res=generate_reply(model,tok,prompt,a.max_new_tokens,0.7,20,1.2,
                                   seed=a.seed+i*1009+j)
                reply=res.text.strip()
                if reply:
                    encoded=encode_case(tok,row["user"],reply,model.context_length)
                    loss_sum,tokens=score(model,device,encoded)
                    nll=loss_sum/tokens
                    truncated=encoded[3]>0
                else:nll=1e6;truncated=False
                rep=repetition(reply);is_generic=generic(reply)
                candidate={"index":j,"text":reply,"tokens":res.token_count,
                           "conditional_nll":nll,"repetition":rep,
                           "generic_reply":is_generic,"prompt_truncated":truncated,
                           "rank_score":ranking_score(nll,rep,is_generic,not reply,truncated),
                           "reference_char3_jaccard":char_similarity(reply,row["assistant"])}
                generated.append(candidate)
            chosen=rank_candidates(generated)
            details.append({"dialogue_id":row["dialogue_id"],"utterance_id":row["utterance_id"],
                            "prompt":row["user"],"reference":row["assistant"],
                            "candidates":generated,"selected_index":chosen["index"],
                            "selected_text":chosen["text"],
                            "selected_reference_char3_jaccard":chosen["reference_char3_jaccard"],
                            "oracle_reference_char3_jaccard":max(c["reference_char3_jaccard"] for c in generated)})
    selected=[d["candidates"][d["selected_index"]] for d in details]
    first=[d["candidates"][0] for d in details]
    summary={"cases":len(details),"candidates_per_case":a.candidates,
             "selected_mean_repetition":sum(c["repetition"] for c in selected)/len(selected),
             "first_mean_repetition":sum(c["repetition"] for c in first)/len(first),
             "selected_generic":sum(c["generic_reply"] for c in selected),
             "first_generic":sum(c["generic_reply"] for c in first),
             "selected_reference_char3_jaccard":sum(d["selected_reference_char3_jaccard"] for d in details)/len(details),
             "first_reference_char3_jaccard":sum(c["reference_char3_jaccard"] for c in first)/len(first),
             "oracle_reference_char3_jaccard":sum(d["oracle_reference_char3_jaccard"] for d in details)/len(details),
             "selected_nonfirst":sum(d["selected_index"]!=0 for d in details)}
    report={"version":"v0.13.40","split":"VALIDATION","model":str(a.model),
            "selection":"conditional_nll + heuristic penalties; no reference leakage",
            "generation":{"temperature":0.7,"top_k":20,"repetition_penalty":1.2,
                          "seed":a.seed},"summary":summary,"details":details,
            "production_unchanged":True,
            "caveats":["Oracle is an upper bound on character overlap, not human judgment.",
                       "Ranking with the same generating LM may favor generic or short answers.",
                       "No semantic or linguistic quality claim without blinded human review.",
                       "Validation only; reserved test remains unused."]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
