"""Audit exact v0.13.53 ruby removals and BPE change without training approval."""
import argparse,collections,hashlib,json
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def bpe_count(text,tokenizer_path):
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file(str(tokenizer_path))
    # Count per sentence, matching the foundation sentence-line convention.
    return sum(len(tok.encode(line,add_special_tokens=False).ids) for line in text.splitlines() if line.strip())

def audit(before,after,apply_audit,tokenizer=None):
    old=before.read_text(encoding="utf-8-sig").splitlines()
    new=after.read_text(encoding="utf-8-sig").splitlines()
    meta=json.loads(apply_audit.read_text(encoding="utf-8-sig"))
    if meta.get("version")!="v0.13.53" or meta.get("status")!="APPLIED_REVIEWED_ONLY":
        raise ValueError("v0.13.53 applied audit required")
    if digest(before)!=meta.get("source_sha256"):raise ValueError("before SHA256 differs from recorded source")
    if len(old)!=len(new):raise ValueError("sentence count changed")
    edits=meta.get("edits",[])
    if len(edits)!=meta.get("applied"):raise ValueError("edits count inconsistent")
    byline=collections.defaultdict(list)
    for e in edits:
        line=e["line"]
        if not isinstance(line,int) or not 1<=line<=len(old):raise ValueError("invalid edit line")
        byline[line].append(e)
    reconstructed=list(old)
    for line,items in byline.items():
        prev=len(old[line-1])+1
        for e in sorted(items,key=lambda x:x["start"],reverse=True):
            st,en=e["start"],e["end"]
            if not 0<=st<en<=len(old[line-1]) or en>prev:raise ValueError("invalid or overlapping edit")
            prev=st
            current=reconstructed[line-1]
            if current[st:en]!=e["removed"]:raise ValueError("recorded edit does not match text")
            reconstructed[line-1]=current[:st]+current[en:]
    if reconstructed!=new:raise ValueError("unexpected corpus changes not explained by audit")
    if meta.get("rejected",0)+meta.get("unsure",0)+meta.get("accepted",0)!=171:
        raise ValueError("review decision counts do not add to 171")
    removed_chars=sum(len(e["removed"]) for e in edits)
    before_chars=sum(map(len,old));after_chars=sum(map(len,new))
    if before_chars-after_chars!=removed_chars:raise ValueError("character delta inconsistent")
    result={"version":"v0.13.54","status":"DIFF_VERIFIED","before_sha256":digest(before),
            "after_sha256":digest(after),"reviewed_edits":len(edits),
            "changed_sentences":len(byline),"sentences_before":len(old),
            "sentences_after":len(new),"characters_before":before_chars,
            "characters_after":after_chars,"characters_removed":removed_chars,
            "bpe_tokens_before":None,"bpe_tokens_after":None,"bpe_token_delta":None,
            "training_approved":False,"source_independence_verified":False,
            "limitations":["Only reviewed 88 replacements are verified, not residual ruby contamination.",
                           "Same novel does not supply independent generalization evidence."]}
    if tokenizer is not None:
        x=bpe_count("\n".join(old),tokenizer);y=bpe_count("\n".join(new),tokenizer)
        result.update(bpe_tokens_before=x,bpe_tokens_after=y,bpe_token_delta=y-x)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",type=Path,required=True)
    p.add_argument("--after",type=Path,required=True)
    p.add_argument("--apply-audit",type=Path,required=True)
    p.add_argument("--tokenizer",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error("refusing overwrite")
    report=audit(a.before,a.after,a.apply_audit,a.tokenizer)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ("status","reviewed_edits","changed_sentences","characters_removed","bpe_tokens_before","bpe_tokens_after","bpe_token_delta","training_approved")},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
