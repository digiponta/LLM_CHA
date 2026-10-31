"""Read-only structural inventory of local persona conversations. No content exported."""
import argparse,collections,json
from pathlib import Path
EXT={".json",".jsonl",".txt",".csv",".tsv",".md"}
def inspect(root):
    root=Path(root)
    if not root.is_dir():return {"status":"MISSING_LOCAL_DIRECTORY","path":str(root)}
    files=[p for p in root.rglob("*") if p.is_file()]
    kinds=collections.Counter(p.suffix.lower() or "<none>" for p in files)
    examples=[]
    for p in sorted(files):
        if p.suffix.lower() not in EXT:continue
        row={"relative_path":str(p.relative_to(root)),"bytes":p.stat().st_size,"extension":p.suffix.lower()}
        try:
            if p.suffix.lower()==".json":
                data=json.loads(p.read_text(encoding="utf-8-sig"))
                row["root_type"]=type(data).__name__
                if isinstance(data,dict):row["root_keys"]=list(data)[:20]
                if isinstance(data,list):row["root_count"]=len(data);row["first_record_keys"]=list(data[0])[:20] if data and isinstance(data[0],dict) else []
            elif p.suffix.lower()==".jsonl":
                with p.open(encoding="utf-8-sig") as f:
                    first=next((line for line in f if line.strip()),"")
                if first:
                    obj=json.loads(first)
                    row["first_record_type"]=type(obj).__name__
                    if isinstance(obj,dict):row["first_record_keys"]=list(obj)[:20]
            elif p.suffix.lower() in (".csv",".tsv"):
                with p.open(encoding="utf-8-sig") as f:
                    row["header_columns"]=f.readline().rstrip("\r\n").split("," if p.suffix.lower()==".csv" else "\t")[:20]
            else:row["structural_note"]="Unstructured text; inspect manually before pairing"
        except (OSError,UnicodeError,ValueError,StopIteration) as e:row["parse_error"]=type(e).__name__
        examples.append(row)
    return {"status":"INVENTORY_ONLY","path":str(root),"file_count":len(files),
            "extensions":dict(kinds),"recognized_files":examples,
            "raw_content_exported":False,"training_started":False}
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",default="data-src/real-persona-chat")
    a.add_argument("--output",default="results/real_persona_inventory_v013588290.json")
    x=a.parse_args();result=inspect(x.source)
    out=Path(x.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
