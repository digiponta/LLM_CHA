"""v0.4.28.38: auditable, conservative Japanese QA candidate augmentation.

Independent utterances are NOT conversation turns. Proposed labels are NOT
verified truth. Never merge this output into training or test automatically.
"""
import argparse,collections,hashlib,json,re,unicodedata
from pathlib import Path
from build_japanese_foundation_qa_v042837 import PII

PATTERNS=(
 ("likes",re.compile(r"^(?:私は|わたしは|僕は|ぼくは|自分は)?(.{2,30}?)が好きです[。!！]*$"),"あなたは{topic}が好きですか。"),
 ("dislikes",re.compile(r"^(?:私は|わたしは|僕は|ぼくは|自分は)?(.{2,30}?)が苦手です[。!！]*$"),"あなたは{topic}が苦手ですか。"),
 ("identity",re.compile(r"^(?:私は|わたしは|僕は|ぼくは|自分は)(.{2,28}?)です[。!！]*$"),"あなたは何者ですか。"),
)
AMBIGUOUS=("それ","これ","あれ","そう","こんな","そんな","どれ","なに","何","あなた","<",">")
QUESTION_END=re.compile(r"(?:[?？]|(?:ですか|ますか|でしょうか|ですかね|なんですか|どんな|どこ|何ですか)[。!！]?)$")
def normalized(s):return unicodedata.normalize("NFKC",s).strip()
def classify(text):
    if QUESTION_END.search(text):return "QUESTION"
    if any(text.startswith(x) for x in ("おはよう","こんにちは","こんばんは","よろしく")):return "GREETING"
    if any(x in text for x in ("好き","苦手","嫌い")):return "PREFERENCE"
    if len(text)>=12 and any(x in text for x in ("です。","ます。","でした。")):return "STATEMENT"
    return "OTHER"

def build(lines):
    seen=set();rows=[];counts=collections.Counter();filtered=0
    for idx,original in enumerate(lines,1):
        text=normalized(original)
        if not text or text in seen:continue
        seen.add(text)
        if PII.search(text):filtered+=1;continue
        role=classify(text);counts[role]+=1
        match=None
        for category,regex,template in PATTERNS:
            m=regex.fullmatch(text)
            if not m:continue
            topic=m.group(1).strip(" 、,。")
            if not 2<=len(topic)<=24 or any(x in topic for x in AMBIGUOUS):continue
            match=(category,template.format(topic=topic));break
        if match is None:continue
        category,question=match
        rows.append({"id":f"JF38-{idx:05d}","question":question,"answer":original.strip(),
          "proposed_relation":"SUPPORTS","proposed_label":True,
          "generation_rule":category,"label_source":"RULE_PROPOSAL",
          "human_verified":False,"review_required":True,"usage":"REVIEW_ONLY",
          "source":{"file":"data/japanese_foundation_v0218.txt","line":idx}})
    # Deliberately don't invent automatic negative/hard-negative gold labels.
    return {"version":"v0.4.28.38","mode":"UNVERIFIED_QA_REVIEW_POOL",
      "source_lines":len(lines),"unique_normalized":len(seen),
      "privacy_pattern_filtered":filtered,"role_counts":dict(sorted(counts.items())),
      "positive_proposals":len(rows),"negative_proposals":0,"hard_negative_proposals":0,
      "human_verified":False,"train_ready":False,"evaluation_ready":False,
      "runtime_modified":False,"candidates":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/japanese_foundation_v0218.txt")
    p.add_argument("--output",default="results/japanese_foundation_qa_candidates_v042838.json")
    a=p.parse_args()
    try:
        src,dst=Path(a.input),Path(a.output)
        if not src.is_file() or src.is_symlink() or dst.exists() or dst.is_symlink():
            raise ValueError("invalid input or output already exists")
        raw=src.read_bytes();result=build(raw.decode("utf-8-sig").splitlines())
        result["source_sha256"]=hashlib.sha256(raw).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("source_lines","unique_normalized","privacy_pattern_filtered","role_counts","positive_proposals","negative_proposals","hard_negative_proposals")},ensure_ascii=False))
    except (OSError,UnicodeError,ValueError) as e:p.exit(1,f"augmentation failed: {e}\n")
if __name__=="__main__":main()
