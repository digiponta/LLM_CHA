"""v0.13.50 conservative ruby-candidate classification.

No automatic text edits. A reviewed mapping of kanji -> reading provides
positive evidence; morphological ambiguities remain for human review.
Default mapping is demonstrative, not a comprehensive pronunciation dictionary.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path

KANJI_KANA=re.compile(r"([一-龯々〆ヶ]{1,8})([ぁ-ゖ]{1,12})")
DEFAULT_READINGS={"見当":"けんとう","掌":"てのひら","吾輩":"わがはい",
                  "大":"おお","獰悪":"どうあく","肝心":"かんじん"}
NORMAL={"見ると","云って","思って","見えて","大きな","聞いて","知れない"}

def classify(surface,readings):
    if surface in NORMAL:return "NORMAL_TEXT","known conventional text"
    for word,reading in sorted(readings.items(),key=lambda p:len(p[0]),reverse=True):
        if surface.startswith(word+reading):
            extra=surface[len(word+reading):]
            # Exact reading followed by arbitrary kana may be an inflection.
            # Never assert that all such occurrences are ruby.
            if not extra:return "CONFIRMED_RUBY","dictionary reading exact; requires human acceptance"
            return "AMBIGUOUS","reading prefix followed by kana; context needed"
    return "AMBIGUOUS","no unambiguous dictionary-backed match"

def analyze(lines,readings,max_examples=50):
    counts=collections.Counter();examples=[];category_counts=collections.Counter()
    for i,line in enumerate(lines,1):
        for match in KANJI_KANA.finditer(line):
            s=match.group()
            label,reason=classify(s,readings)
            category_counts[label]+=1
            counts[(label,s)]+=1
            if len(examples)<max_examples or label=="CONFIRMED_RUBY":
                examples.append({"line":i,"text":s,"label":label,"reason":reason,
                                 "context":line[max(0,match.start()-12):match.end()+12]})
    return {"version":"v0.13.50","status":"REVIEW_REQUIRED",
            "categories":dict(category_counts),
            "top":[{"label":k[0],"surface":k[1],"count":v} for k,v in counts.most_common(50)],
            "examples":examples[:max_examples],
            "training_approved":False,"automatic_replacements":0,
            "notes":["Dictionary exact reading is evidence, not proof of ruby.",
                     "Regex token boundaries may be wrong; results must be reviewed.",
                     "Original and v0.13.49 curated texts are unchanged."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/aozora_789_curated_v01349.txt"))
    p.add_argument("--readings",type=Path)
    p.add_argument("--output",type=Path,default=Path("results/aozora_789_ruby_classes_v01350.json"))
    a=p.parse_args()
    if a.output.exists():p.error("refusing overwrite")
    lines=a.input.read_text(encoding="utf-8-sig").splitlines()
    readings=dict(DEFAULT_READINGS)
    if a.readings:
        additional=json.loads(a.readings.read_text(encoding="utf-8-sig"))
        if not isinstance(additional,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in additional.items()):
            p.error("readings must be a JSON object of strings")
        readings.update(additional)
    result=analyze(lines,readings)
    result["sha256"]=hashlib.sha256(a.input.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"categories":result["categories"],
                      "automatic_replacements":0},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
