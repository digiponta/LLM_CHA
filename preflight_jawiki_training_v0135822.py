"""v0.13.58.22 offline Wikipedia training preflight; never trains or approves."""
import argparse,collections,hashlib,json
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect(dataset_dir,tokenizer,checkpoint,output,conversation=None,persona=None):
    if output.exists():raise FileExistsError(output)
    manifest=json.loads((dataset_dir/"manifest.json").read_text(encoding="utf-8-sig"))
    issues=[]
    if manifest.get("status")!="STAGED_NOT_APPROVED":issues.append("STAGING_STATUS_INVALID")
    if sha(tokenizer)!=manifest.get("tokenizer_sha256"):issues.append("TOKENIZER_HASH_MISMATCH")
    max_len=manifest.get("max_context_tokens",512)
    if not isinstance(max_len,int) or not 2<=max_len<=512:issues.append("CONTEXT_INVALID")
    try:
        import torch
        cp=torch.load(checkpoint,map_location="cpu",weights_only=True)
        cfg=cp["config"]
        vocab=int(cfg["vocab_size"]);context=int(cfg["context_length"])
        if context<max_len:issues.append("CHECKPOINT_CONTEXT_TOO_SHORT")
    except Exception as exc:
        issues.append("CHECKPOINT_UNREADABLE:"+type(exc).__name__)
        vocab=0;context=0
    totals={};art_ids={};rows_by_split={}
    for split in ("train","validation"):
        path=dataset_dir/(split+"_chunks.jsonl")
        if not path.is_file():raise FileNotFoundError(path)
        if sha(path)!=manifest.get("file_sha256",{}).get(path.name):
            issues.append("DATASET_HASH_MISMATCH_"+split.upper())
        stats=collections.Counter();articles=set();bad=0
        with path.open(encoding="utf-8-sig") as f:
            for index,line in enumerate(f,1):
                if not line.strip():continue
                r=json.loads(line);stats["chunks"]+=1
                ids=r.get("token_ids")
                if not isinstance(ids,list) or len(ids)<2 or len(ids)>max_len+1 or any(type(t) is not int or t<0 or t>=vocab for t in ids):
                    bad+=1;continue
                if r.get("supervised_tokens")!=len(ids)-1:bad+=1
                if r.get("approval")!="PENDING_REVIEW" or r.get("auto_promote") is not False:bad+=1
                if not r.get("article_id") or not r.get("title") or not str(r.get("url","")).startswith("https://ja.wikipedia.org/"):bad+=1
                articles.add(str(r.get("article_id")))
                stats["supervised_tokens"]+=len(ids)-1
        totals[split]=dict(stats);art_ids[split]=articles;rows_by_split[split]=bad
        if bad:issues.append("BAD_"+split.upper()+"_RECORDS")
        if stats["chunks"]!=manifest.get("chunks",{}).get(split):issues.append("CHUNK_COUNT_MISMATCH_"+split.upper())
        if stats["supervised_tokens"]!=manifest.get("supervised_tokens",{}).get(split):issues.append("TOKEN_COUNT_MISMATCH_"+split.upper())
        if len(articles)!=manifest.get("articles",{}).get(split):issues.append("ARTICLE_COUNT_MISMATCH_"+split.upper())
    if art_ids["train"] & art_ids["validation"]:issues.append("ARTICLE_LEAKAGE")
    from audit_offline_replay_v0135810 import read_file
    replay={}
    for key,path in (("conversation",conversation),("persona",persona)):
        if path is None:continue
        if not path.is_file():issues.append("REPLAY_SOURCE_MISSING_"+key.upper());continue
        try:
            lines=read_file(path)
            replay[key]={"lines":len(lines),"characters":sum(map(len,lines)),"sha256":sha(path)}
        except Exception as exc:
            issues.append("REPLAY_UNREADABLE_"+key.upper()+":"+type(exc).__name__)
    wiki_tokens=totals["train"].get("supervised_tokens",0)
    # Counts below are planning metrics only. Replay tokens are not included
    # without tokenizer-level accounting; do not invent token ratios.
    plans={
        "W":{"wiki":1.0},
        "WR":{"wiki":0.7,"conversation":0.3},
        "WRP":{"wiki":0.6,"conversation":0.3,"persona":0.1}}
    for label,weights in plans.items():
        for domain in weights:
            if domain!="wiki" and domain not in replay:issues.append("PLAN_SOURCE_MISSING_"+label+"_"+domain)
    report={"version":"v0.13.58.22","status":"PREFLIGHT_BLOCKED",
        "issues":sorted(set(issues)),"checkpoint_sha256":sha(checkpoint),
        "tokenizer_sha256":sha(tokenizer),"model_config":{"vocab_size":vocab,"context_length":context},
        "datasets":totals,"bad_rows":rows_by_split,"article_disjoint":not bool(art_ids["train"] & art_ids["validation"]),
        "replay_sources":replay,
        "experiment_weight_hypotheses":plans,
        "mixing_unit":"NOT_EXECUTED; proportions are planning hypotheses, not measured token ratios",
        "wiki_train_supervised_tokens":wiki_tokens,
        "independent_holdout_verified":False,"human_review_approved":False,
        "training_performed":False,"production_promotion_allowed":False,
        "limitations":["Same-dump validation is diagnostic, not independent.",
                       "Prior exposure of base model cannot be ruled out.",
                       "Human quality review and independent holdout still required."]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset-dir",type=Path,default=Path("results/jawiki_dataset_v0135821"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--checkpoint",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--conversation",type=Path,default=Path("data/replay_conversation_approved_v013582.jsonl"))
    p.add_argument("--persona",type=Path,default=Path("data/replay_persona_approved_v013582.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/jawiki_training_preflight_v0135822.json"))
    a=p.parse_args()
    r=inspect(a.dataset_dir,a.tokenizer,a.checkpoint,a.output,a.conversation,a.persona)
    print(json.dumps({"status":r["status"],"issues":r["issues"],"datasets":r["datasets"],
                      "article_disjoint":r["article_disjoint"]},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
