"""v0.2.33.38 — read-only Semantic Memory API discovery and safe integration gate.

Inspects local Python AST without importing modules, running code or accessing
production memory. Emits a reviewable candidate API inventory. Does NOT claim
that an inspected function is a valid live adapter.
"""
import argparse,ast,json
from pathlib import Path

SEARCH_TERMS=("semantic","candidate","approve","promote","reject","memory","dss","dialogue")
MUTATING_TERMS=("save","write","delete","remove","forget","approve","promote","reject","commit","store","insert","update")

def discover(root,max_files=500):
    root=Path(root).resolve()
    if not root.is_dir():raise ValueError("Repository path must be a directory")
    records=[];scanned=0;errors=[]
    for path in sorted(root.rglob("*.py")):
        if any(p in (".git",".venv","venv","__pycache__","site-packages") for p in path.parts):continue
        scanned+=1
        if scanned>max_files:
            errors.append("file limit reached");break
        try:
            source=path.read_text(encoding="utf-8-sig")
            tree=ast.parse(source,filename=str(path))
        except (OSError,UnicodeError,SyntaxError) as exc:
            errors.append({"path":str(path.relative_to(root)),"error":type(exc).__name__})
            continue
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
            name=node.name
            if not any(term in name.lower() for term in SEARCH_TERMS):continue
            if isinstance(node,ast.ClassDef):
                args=None
            else:
                args=[a.arg for a in node.args.posonlyargs+node.args.args+node.args.kwonlyargs]
            records.append({"path":str(path.relative_to(root)),"line":node.lineno,
                            "kind":"class" if isinstance(node,ast.ClassDef) else "function",
                            "name":name,"arguments":args,
                            "potential_mutation":any(t in name.lower() for t in MUTATING_TERMS)})
    return {"files_scanned":min(scanned,max_files),"symbols":records,
            "errors":errors,"status":"review_required","live_integration":False}

def evaluate_contract(inventory):
    groups={"candidate_creation":[],"approval":[],"rejection":[],"retrieval":[],"dss":[]}
    for symbol in inventory["symbols"]:
        n=symbol["name"].lower()
        for key,terms in {
            "candidate_creation":("candidate","propose","capture"),
            "approval":("approve","promote"),
            "rejection":("reject","discard"),
            "retrieval":("search","retrieve","lookup","query"),
            "dss":("dss","dialogue")}.items():
            if any(t in n for t in terms):groups[key].append(
                {"path":symbol["path"],"name":symbol["name"],"line":symbol["line"]})
    return {"potential_entrypoints":groups,
            "automatically_bindable":False,
            "reason":"AST names/signatures alone cannot establish semantic or transaction contracts"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",default="results/semantic_api_discovery_v023338.json")
    p.add_argument("--max-files",type=int,default=500)
    args=p.parse_args()
    if args.max_files<1:raise ValueError("--max-files must be positive")
    output=Path(args.out)
    if output.exists():raise FileExistsError("Refusing overwrite")
    inventory=discover(args.root,args.max_files)
    inventory["contract_review"]=evaluate_contract(inventory)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Scanned={inventory['files_scanned']}, candidate_symbols={len(inventory['symbols'])}")
    for key,values in inventory["contract_review"]["potential_entrypoints"].items():
        print(key,":",len(values))
    print("Live integration: NOT enabled; manual contract verification required")
    print("Saved",output)
if __name__=="__main__":main()
