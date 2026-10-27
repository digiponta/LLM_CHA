"""v0.13.51 dictionary-guided ruby boundary analysis (read-only).
Finds embedded kanji+reading even when kana particles follow. Detection is
heuristic; every candidate needs review. No substitutions or approvals.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from classify_inline_ruby_v01350 import DEFAULT_READINGS

CANDIDATE=re.compile(r"([一-龯々〆ヶ]{1,10})([ぁ-ゖ]{1,15})")
def inspect_match(match,readings):
    kanji,kana=match.groups()
    # Prefer longest suffix of extracted kanji that matches a dictionary entry.
    for word,reading in sorted(readings.items(),key=lambda x:len(x[0]),reverse=True):
        if kanji.endswith(word) and kana.startswith(reading):
            if len(reading)<2:
                return {"label":"AMBIGUOUS","kanji":word,"reading":reading,
                        "following":kana[len(reading):],"reason":"single-kana reading cannot disambiguate okurigana"}
            return {"label":"RUBY_CANDIDATE","kanji":word,"reading":reading,
                    "following":kana[len(reading):],"reason":"dictionary reading prefix; manual review required"}
    return {"label":"AMBIGUOUS","kanji":kanji,"reading":None,
            "following":kana,"reason":"no dictionary-backed reading prefix"}

def classify_lines(lines,readings,max_examples=50):
    totals=collections.Counter();surfaces=collections.Counter();samples=[]
    for line_number,line in enumerate(lines,1):
        for match in CANDIDATE.finditer(line):
            result=inspect_match(match,readings)
            totals[result["label"]]+=1
            surfaces[(result["label"],match.group())]+=1
            if len(samples)<max_examples:
                samples.append({"line":line_number,"surface":match.group(),
                                "context":line[max(0,match.start()-12):match.end()+12],**result})
    return {"version":"v0.13.51","status":"REVIEW_REQUIRED",
            "categories":dict(totals),
            "examples":samples,
            "top":[{"label":k[0],"surface":k[1],"count":n}
                   for k,n in surfaces.most_common(50)],
            "automatic_replacements":0,"training_approved":False,
            "limitations":["Regex segmentation is not full Japanese morphological analysis.",
                           "Even dictionary matches may occur in conventional text.",
                           "Human review required before writing any curated training text."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/aozora_789_curated_v01349.txt"))
    p.add_argument("--readings",type=Path)
    p.add_argument("--output",type=Path,default=Path("results/aozora_789_ruby_boundaries_v01351.json"))
    p.add_argument("--max-examples",type=int,default=50)
    a=p.parse_args()
    if not a.input.is_file():p.error(f"missing input: {a.input}")
    if a.output.exists():p.error("refusing to overwrite report")
    if a.max_examples<1:p.error("max-examples must be positive")
    readings=dict(DEFAULT_READINGS)
    if a.readings:
        additions=json.loads(a.readings.read_text(encoding="utf-8-sig"))
        if not isinstance(additions,dict) or not all(isinstance(k,str) and isinstance(v,str) and k and v for k,v in additions.items()):
            p.error("readings must be a nonempty string-to-string JSON mapping")
        readings.update(additions)
    lines=a.input.read_text(encoding="utf-8-sig").splitlines()
    report=classify_lines(lines,readings,a.max_examples)
    report["input_sha256"]=hashlib.sha256(a.input.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"categories":report["categories"],
                      "automatic_replacements":0},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
