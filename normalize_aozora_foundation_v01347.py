"""v0.13.47: normalize Aozora-style Japanese prose without changing source files.

This is a preparation utility, not an authorization to train on a text.
Operator must inspect outputs, confirm usage rights and approve the v0.13.45 manifest.
"""
import argparse,json,re,unicodedata
from pathlib import Path

RUBY_BRACKET=re.compile(r"《[^》\n]*》")
ANNOTATION=re.compile(r"［＃[^］\n]*］")
HEADER_LINE=re.compile(r"^(?:底本[：:]|入力[：:]|校正[：:]|青空文庫|ファイル作成|公開日[：:]|更新日[：:])")
SEPARATOR=re.compile(r"^[\-―─=＝＊*]{5,}$")
END=re.compile(r"(?<=[。！？!?])")
def strip_aozora(text):
    text=text.lstrip("\ufeff").replace("\r\n","\n").replace("\r","\n")
    lines=text.split("\n")
    # Aozora files often have header/title metadata; support explicit body delimiters.
    start=next((i+1 for i,l in enumerate(lines) if "本文開始" in l),0)
    end=next((i for i,l in enumerate(lines[start:],start) if "底本：" in l or "底本:" in l),len(lines))
    result=[]
    stats={"ruby_removed":0,"annotations_removed":0,"lines_skipped":0}
    for line in lines[start:end]:
        line=line.strip().replace("｜","|")
        if not line or HEADER_LINE.match(line) or SEPARATOR.match(line):
            stats["lines_skipped"]+=1;continue
        stats["ruby_removed"]+=len(RUBY_BRACKET.findall(line))
        line=RUBY_BRACKET.sub("",line)
        stats["annotations_removed"]+=len(ANNOTATION.findall(line))
        line=ANNOTATION.sub("",line).replace("|","")
        line=unicodedata.normalize("NFKC",line)
        line=re.sub(r"[\t 　]+"," ",line).strip()
        if line:result.append(line)
    return "\n".join(result),stats

def extract_sentences(text,min_chars=20,max_chars=500):
    # Preserve paragraphs as boundaries; join wrapped lines only within a paragraph
    # is intentionally NOT automatic: Aozora lines may be structurally meaningful.
    sentences=[];seen=set()
    for line in text.splitlines():
        for chunk in END.split(line):
            s=chunk.strip()
            if min_chars<=len(s)<=max_chars and re.search(r"[。！？!?]$",s) and s not in seen:
                sentences.append(s);seen.add(s)
    return sentences

def convert(source,output,report,min_chars=20,max_chars=500):
    if output.exists() or report.exists():raise FileExistsError("output exists")
    raw=source.read_text(encoding="utf-8-sig")
    normalized,stats=strip_aozora(raw)
    sentences=extract_sentences(normalized,min_chars,max_chars)
    if not sentences:raise ValueError("no extracted sentences; inspect source format")
    output.parent.mkdir(parents=True,exist_ok=True)
    report.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("\n".join(sentences)+"\n",encoding="utf-8")
    meta={"version":"v0.13.47","source":str(source),"sentences":len(sentences),
          "statistics":stats,"training_approved":False,
          "needs_manual_text_and_licensing_review":True,
          "limitations":["Inline annotations on multiple lines are not supported.",
                         "Hard-wrapped prose may require paragraph-aware conversion.",
                         "Normalized text must be reviewed before training."]}
    report.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return meta

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    if not a.source.is_file():p.error(f"missing source: {a.source}")
    print(json.dumps(convert(a.source,a.output,a.report),ensure_ascii=False))
if __name__=="__main__":main()
