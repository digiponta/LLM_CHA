"""v0.13.45: Convert approved Japanese plain-text sources to grouped corpus.

Input manifest is JSON with sources: id, path (relative to manifest directory),
license, provenance, approved_for_training. Each file is a source group.
No historical holdout or reserved evaluation material may be used as training.
Outputs are write-once and compatible with v0.13.44 trainer.
"""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
from prepare_japanese_foundation_v01343 import prepare,write_new

SENTENCE_END=re.compile(r"(?<=[。！？!?])")
META=re.compile(r"^(?:青空文庫|底本：|入力：|校正：|作成日：|公開日：|［＃|----------)")
def split_sentences(text,min_chars=20,max_chars=500):
    text=text.replace("\r","").replace("\ufeff","")
    parts=[];discarded=0
    for raw in text.splitlines():
        s=unicodedata.normalize("NFKC",raw).strip()
        if not s or META.match(s) or s.startswith("#"):continue
        s=re.sub(r"[ \t　]+"," ",s)
        for candidate in SENTENCE_END.split(s):
            c=candidate.strip()
            if min_chars<=len(c)<=max_chars and re.search(r"[。！？!?]$",c) and "�" not in c:
                parts.append(c)
            else:discarded+=1
    return list(dict.fromkeys(parts)),discarded

def source_path(manifest_path,entry):
    base=manifest_path.parent.resolve()
    target=(base/entry["path"]).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"path escapes manifest directory: {entry['path']}")
    return target

def expand(manifest_path,out_dir,exclude_paths=(),seed=1345,ratio=.2):
    manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    sources=manifest["sources"]
    excluded={p.resolve() for p in exclude_paths}
    expanded=[];statistics=[];seen=set()
    for row in sources:
        if not all(row.get(k) for k in ("id","path","license","provenance")):
            raise ValueError("missing required source metadata")
        if row.get("approved_for_training") is not True:
            raise ValueError(f"source requires explicit approval: {row['id']}")
        p=source_path(manifest_path,row)
        if p in excluded or "heldout" in p.name.lower() or "test" in p.name.lower():
            raise ValueError(f"forbidden evaluation input: {p}")
        if not p.is_file():raise FileNotFoundError(p)
        if p in seen:raise ValueError("duplicate source path")
        seen.add(p)
        text=p.read_text(encoding="utf-8-sig")
        sentences,discarded=split_sentences(text)
        if not sentences:raise ValueError(f"no eligible sentences: {p}")
        staged=out_dir/"staged"/(row["id"]+".txt")
        if "/" in row["id"] or "\\" in row["id"] or row["id"] in (".",".."):
            raise ValueError("unsafe source ID")
        expanded.append({**row,"path":str(staged.relative_to(out_dir))})
        statistics.append({"source_id":row["id"],"original_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                           "extracted":len(sentences),"discarded_fragments":discarded,
                           "sentences":sentences})
    # No files are written before all source files and split controls validate.
    # Prepare the audit in a temporary directory with the normalized manifest.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        temp_rows=[]
        for row,info in zip(expanded,statistics):
            name=row["id"]+".txt"
            (folder/name).write_text("\n".join(info["sentences"])+"\n",encoding="utf-8")
            temp_rows.append({**row,"path":name})
        prepared,audit=prepare({"sources":temp_rows},folder,ratio,seed)
    files=[out_dir/"train.txt",out_dir/"val.txt",out_dir/"audit.json"]
    if any(p.exists() for p in files):raise FileExistsError("output exists; refusing overwrite")
    for info,row in zip(statistics,expanded):
        write_new(out_dir/row["path"],"\n".join(info.pop("sentences"))+"\n")
    audit["version"]="v0.13.43"  # compatibility with guarded v0.13.44 trainer
    audit["pipeline_version"]="v0.13.45"
    audit["source_audit_original"]=statistics
    audit["holdout_independence_verified"]=False
    for key in ("train","val"):
        write_new(out_dir/(key+".txt"),"\n".join(prepared[key])+"\n")
    write_new(out_dir/"audit.json",json.dumps(audit,ensure_ascii=False,indent=2)+"\n")
    return audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,default=Path("results/japanese_foundation_corpus_v01345"))
    p.add_argument("--exclude",type=Path,action="append",default=[])
    p.add_argument("--seed",type=int,default=1345)
    a=p.parse_args()
    if not a.manifest.is_file():p.error(f"missing manifest: {a.manifest}")
    result=expand(a.manifest,a.output_dir,a.exclude,a.seed)
    print(json.dumps({"counts":result["counts"],"sources":len(result["source_audit_original"]),
                      "cross_source_duplicates":len(result["cross_source_duplicates_dropped"])},ensure_ascii=False))
    print("audit:",a.output_dir/"audit.json")
if __name__=="__main__":main()
