"""v0.4.28.39: non-destructive quality gate over v0.4.28.38 proposals.

REJECT: identity template and demonstrably malformed questions.
HOLD: otherwise plausible source-grounded proposals, pending manual review.
ACCEPT: reserved exclusively for externally human-reviewed data; never automatic.
"""
import argparse,collections,hashlib,json,re,unicodedata
from pathlib import Path
from build_japanese_foundation_qa_v042837 import PII
from build_japanese_foundation_qa_v042838 import normalized

PRONOUNS=("それ","これ","あれ","そう","こんな","そんな","何","どれ","あなた")
LEADING=re.compile(r"^(?:ああ|あー|ええ|はい|いや|いえ|なるほど|そうですね|そうなんですね|わかります|通ですね|おお)[!！、,。\s]*")
SUBJECT=re.compile(r"^(?:私は|わたしは|僕は|ぼくは|自分は)[、,\s]*")
VERB={"likes":"好き","dislikes":"苦手"}

def evaluate(item):
    """Return a reviewed *proposal* without ever certifying its label."""
    record=dict(item)
    rule=item.get("generation_rule")
    original=normalized(item.get("answer",""))
    reasons=[]
    status="HOLD"
    if rule=="identity":
        status="REJECT";reasons.append("INVALID_IDENTITY_TEMPLATE")
    elif rule not in VERB:
        status="REJECT";reasons.append("UNSUPPORTED_GENERATION_RULE")
    else:
        term=VERB[rule]
        # Only final simple clause can be made into a question; never join
        # prior sentences or material with an embedded clause.
        tail=re.split(r"[。!?！？]",original)[-1].strip()
        if not tail:
            parts=[p.strip() for p in re.split(r"[。!?！？]",original) if p.strip()]
            tail=parts[-1] if parts else ""
        tail=LEADING.sub("",tail)
        tail=SUBJECT.sub("",tail)
        # "Xが好きです" only; "YはXが好き" contains ungrounded context.
        m=re.fullmatch(r"(.{2,40}?)が"+term+r"です",tail)
        if m:
            topic=m.group(1).strip(" 、,。")
            if any(x in topic for x in PRONOUNS) or PII.search(topic):
                status="REJECT";reasons.append("AMBIGUOUS_OR_PRIVATE_TOPIC")
            elif len(topic)>24 or re.search(r"[、,]|(?:ですね|ですが|なので|だから|と思い|けど)",topic):
                status="REJECT";reasons.append("COMPOUND_OR_CONTEXT_DEPENDENT")
            else:
                record["suggested_question"]=f"{topic}が{term}ですか。"
                reasons.append("SINGLE_CLAUSE_REWRITE_PENDING_REVIEW")
        else:
            status="REJECT";reasons.append("NO_SIMPLE_EXPLICIT_PREFERENCE_CLAUSE")
    record.update({"gate_status":status,"gate_reasons":reasons,"human_verified":False,
                   "review_required":True,"usage":"REVIEW_ONLY","train_ready":False,
                   "proposed_label":item.get("proposed_label")})
    return record

def gate(data):
    if data.get("version")!="v0.4.28.38" or not isinstance(data.get("candidates"),list):
        raise ValueError("expected v0.4.28.38 review-pool JSON")
    rows=[evaluate(x) for x in data["candidates"]]
    counts=collections.Counter(x["gate_status"] for x in rows)
    return {"version":"v0.4.28.39","mode":"QA_CANDIDATE_QUALITY_GATE",
      "source_version":data["version"],"source_sha256":data.get("source_sha256"),
      "total":len(rows),"accepted":counts["ACCEPT"],"held":counts["HOLD"],"rejected":counts["REJECT"],
      "human_verified":False,"train_ready":False,"evaluation_ready":False,
      "auto_learning":False,"runtime_modified":False,"candidates":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/japanese_foundation_qa_candidates_v042838.json")
    p.add_argument("--output",default="results/japanese_foundation_qa_quality_v042839.json")
    a=p.parse_args()
    try:
        src,dst=Path(a.input),Path(a.output)
        if not src.is_file() or src.is_symlink() or dst.exists() or dst.is_symlink():
            raise ValueError("input missing or output exists")
        raw=src.read_bytes();data=json.loads(raw.decode("utf-8-sig"))
        result=gate(data);result["input_sha256"]=hashlib.sha256(raw).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total","accepted","held","rejected")}))
    except (OSError,ValueError,KeyError,TypeError) as e:p.exit(1,f"quality gate failed: {e}\n")
if __name__=="__main__":main()
