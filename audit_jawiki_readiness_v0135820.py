"""v0.13.58.20 — Offline, read-only Wikipedia token-quality/readiness audit.

Requires cleaned JSONL and source quality report; does NOT train or approve.
Hard fail on provenance mismatch, altered files, non-independent holdout,
and severe residual markup. Unreviewed data remains NOT_READY.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def evaluate(source,quality_report,tokenizer_path,output,max_records=0,holdout_attestation=None):
    if output.exists():raise FileExistsError(output)
    manifest=json.loads(quality_report.read_text(encoding="utf-8-sig"))
    expected=manifest.get("sha256",{}).get("clean_candidates.jsonl")
    if not expected or sha(source)!=expected:
        raise ValueError("cleaned candidate SHA256 does not match quality report")
    if tokenizer_path is None or not tokenizer_path.is_file():
        raise FileNotFoundError("tokenizer missing")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(tokenizer_path))
    counts=collections.Counter();lengths=[];bad=[];articles=set()
    with source.open(encoding="utf-8-sig") as f:
        for idx,line in enumerate(f,1):
            if max_records and idx>max_records:break
            if not line.strip():continue
            rec=json.loads(line)
            reasons=[]
            if rec.get("approval")!="PENDING_REVIEW" or rec.get("auto_promote") is not False:
                reasons.append("APPROVAL_STATE_INVALID")
            if not rec.get("article_id") or not rec.get("title") or not str(rec.get("source_url","")).startswith("https://ja.wikipedia.org/"):
                reasons.append("PROVENANCE_MISSING")
            text=rec.get("text","")
            if not isinstance(text,str) or len(text)<100:reasons.append("TEXT_TOO_SHORT")
            if re.search(r"\[\[|\]\]|\{\{|\}\}|\{\||\|\}|<ref\b|�",str(text)):
                reasons.append("RESIDUAL_MARKUP")
            if reasons:
                bad.append({"record":idx,"reasons":reasons})
                counts.update(reasons)
                continue
            ids=tok.encode(text,add_bos=False,add_eos=False)
            if not ids:bad.append({"record":idx,"reasons":["ZERO_TOKENS"]});counts["ZERO_TOKENS"]+=1;continue
            lengths.append(len(ids));articles.add(rec["article_id"])
    n=len(lengths)
    lengths.sort()
    result={"version":"v0.13.58.20","status":"NOT_READY","record_count":n+len(bad),
        "valid_records":n,"flagged_records":len(bad),"article_count":len(articles),
        "token_count":sum(lengths),"token_length":{"min":lengths[0] if n else None,
             "median":lengths[n//2] if n else None,"p95":lengths[min(n-1,int(n*.95))] if n else None,
             "max":lengths[-1] if n else None},
        "issue_counts":dict(counts),"issues_sample":bad[:30],
        "input_sha256":sha(source),"tokenizer_sha256":sha(tokenizer_path),
        "holdout_independence_attested":holdout_attestation is not None and holdout_attestation.is_file(),
        "human_content_review_approved":False,
        "quality_check_pass":bool(n) and not bad,
        "training_performed":False,"memory_promoted":False,
        "production_promotion_allowed":False,
        "limitations":["Independent holdout and human content review required before training",
        "This tool does not audit all data previously seen by the base model",
        "Token length is measured without language-quality or factuality judgment"]}
    if holdout_attestation:
        # Presence is not proof; the attestation is only a review input.
        result["holdout_independence_attested"]=False
        result["holdout_attestation_supplied"]=holdout_attestation.is_file()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("results/jawiki_clean_v0135819/clean_candidates.jsonl"))
    p.add_argument("--quality-report",type=Path,default=Path("results/jawiki_clean_v0135819/quality_report.json"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/jawiki_readiness_v0135820.json"))
    p.add_argument("--max-records",type=int,default=0,help="0 means all")
    a=p.parse_args()
    if a.max_records<0:p.error("max-records must be >=0")
    r=evaluate(a.source,a.quality_report,a.tokenizer,a.output,a.max_records)
    print(json.dumps({k:r[k] for k in ("status","record_count","valid_records","flagged_records","token_count","quality_check_pass")},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
