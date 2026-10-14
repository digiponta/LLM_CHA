"""v0.4.28.37: conservative Japanese foundation QA candidate builder.

Only obvious explicit self-preference constructions yield synthetic question/
answer candidates. No adjacent-line pairing, no inferred biography,
no automatic Truth Gate labels, and no integration into production training.
"""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path

PREFER=re.compile(r"^(?:私は|わたしは|僕は|ぼくは|自分は)(.{1,36}?)(?:が|は)好きです[。！!\s]*$")
PII=re.compile(r"<[^>\n]+>|https?://|[\w.+-]+@[\w.-]+|\d{2,4}-\d{2,4}-\d{3,4}")
def normalize(s):return unicodedata.normalize("NFKC",s).strip()
def extract(lines):
    seen=set();candidates=[];unique=0;rejected=0
    for line_no,line in enumerate(lines,1):
        raw=line.strip();clean=normalize(raw)
        if not clean or clean in seen:continue
        seen.add(clean);unique+=1
        if PII.search(clean):rejected+=1;continue
        m=PREFER.fullmatch(clean)
        if not m:continue
        topic=m.group(1).strip(" 、,。")
        if not 2<=len(topic)<=24 or any(x in topic for x in ("あなた","それ","これ","あれ","私","僕","わたし")):
            continue
        answer=raw
        question=f"あなたは{topic}が好きですか。"
        candidates.append({"id":f"JF-{line_no:05d}","question":question,
          "answer":answer,"topic":topic,"label":True,
          "label_kind":"SYNTHETIC_POSITIVE_CANDIDATE",
          "human_verified":False,"source":{"file":"data/japanese_foundation_v0218.txt","line":line_no},
          "usage":"TRAIN_CANDIDATE_ONLY","character_persona":None})
    return {"version":"v0.4.28.37","mode":"FOUNDATION_QA_TRAIN_CANDIDATES_ONLY",
      "source_lines":len(lines),"unique_normalized_lines":unique,
      "pii_filtered_lines":rejected,"candidate_count":len(candidates),
      "labels_verified":False,"evaluation_holdout_created":False,
      "runtime_modified":False,"candidates":candidates}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/japanese_foundation_v0218.txt")
    p.add_argument("--output",default="results/japanese_foundation_qa_candidates_v042837.json")
    a=p.parse_args()
    try:
        src,dst=Path(a.input),Path(a.output)
        if not src.is_file() or src.is_symlink() or dst.exists() or dst.is_symlink():
            raise ValueError("input missing or output exists")
        raw=src.read_bytes()
        result=extract(raw.decode("utf-8-sig").splitlines())
        result["source_sha256"]=hashlib.sha256(raw).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("source_lines","unique_normalized_lines","pii_filtered_lines","candidate_count")}))
    except (OSError,ValueError,UnicodeError) as e:p.exit(1,f"foundation builder failed: {e}\n")
if __name__=="__main__":main()
