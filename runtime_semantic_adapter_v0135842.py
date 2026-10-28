"""v0.13.58.42 — read-only adapter for real proposition + truth stores.

Fail-closed: existing propositions and truth overlays are NOT approvals.
Only explicitly approved matching proposition rows can become eligible
experimental answer facts. No writes to source stores or model.
"""
import argparse,json,hashlib
from pathlib import Path
from semantic_proposition_v1090 import load_propositions
from truth_state_v10103 import load_truth_records,truth_record_for_concept
from provenance_semantic_memory_v0135841 import answer,SUBJECT,ALLOWED
from text_integrity_gate_v0135837 import defects

RELS=("author","narrator","theme","title")
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_manifest(path):
 data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
 if data.get("format")!="cha-runtime-adapter-manifest-v0.13.58.42":raise ValueError("invalid manifest format")
 records=data.get("records",[])
 if not isinstance(records,list):raise ValueError("manifest records not list")
 return records
def adapter(propositions,truth,manifest):
 """The manifest is explicit per-proposition eligibility, never inferred."""
 pairs={(p.subject,p.value) for p in propositions}
 out=[];denied=[];seen=set()
 for m in manifest:
  if not isinstance(m,dict):raise ValueError("manifest record not object")
  record_id=m.get("record_id");rel=m.get("relation");sub=m.get("subject");value=m.get("value")
  if not all(isinstance(x,str) and x for x in (record_id,rel,sub,value)):
   raise ValueError("missing manifest identity")
  if record_id in seen:raise ValueError("duplicate record id")
  seen.add(record_id)
  reasons=[]
  if rel not in RELS:reasons.append("UNKNOWN_RELATION")
  if sub!=SUBJECT:reasons.append("SUBJECT_NOT_ALLOWED")
  if defects(value) or defects(sub):reasons.append("TEXT_INTEGRITY_FAIL")
  if (sub,value) not in pairs:reasons.append("PROPOSITION_NOT_FOUND")
  if m.get("approval_state")!=ALLOWED or m.get("production_approved") is not False:
   reasons.append("NOT_EXPERIMENTALLY_APPROVED")
  if m.get("active") is not True:reasons.append("INACTIVE")
  state=truth_record_for_concept(truth,sub)
  # An absent or UNVERIFIED overlay is not truth attestation.
  if state is None or state.state!="TRUE":reasons.append("TRUTH_NOT_VERIFIED")
  if reasons:
   denied.append({"record_id":record_id,"reasons":reasons})
  else:
   out.append({"record_id":record_id,"subject":sub,"relation":rel,"value":value,
    "source_id":str(m.get("source_id") or record_id),
    "approval_state":ALLOWED,"production_approved":False,"active":True,
    "runtime_source":"SEMANTIC_PROPOSITION_READ_ONLY"})
 return out,denied

def run(prop_path,truth_path,manifest_path,output):
 if output.exists():raise FileExistsError(output)
 if not prop_path.is_file() or not truth_path.is_file() or not manifest_path.is_file():
  raise FileNotFoundError("explicit proposition, truth and manifest files required")
 originals={str(p):digest(p) for p in (prop_path,truth_path,manifest_path)}
 props=load_propositions(prop_path);truth=load_truth_records(truth_path)
 approved,denied=adapter(props,truth,read_manifest(manifest_path))
 questions=("『吾輩は猫である』の著者と語り手を教えて。",
            "夏目漱石の『吾輩は猫である』の視点とテーマを説明して。",
            "『吾輩は猫である』の作者は夏目漱石ではない？")
 cases=[{"question":q,"result":answer(q,approved)} for q in questions]
 if originals!={str(p):digest(p) for p in (prop_path,truth_path,manifest_path)}:
  raise RuntimeError("source stores changed during read")
 report={"version":"v0.13.58.42","status":"RUNTIME_ADAPTER_AUDIT_COMPLETE",
   "source_format":"EXISTING_SEMANTIC_PROPOSITIONS_AND_TRUTH_OVERLAY",
   "note":"Read-only adapter, not chat.py runtime wiring or production promotion",
   "source_sha256":originals,"propositions_loaded":len(props),
   "eligible_records":len(approved),"denied_records":denied,
   "eligible":approved,"cases":cases,"training_performed":False,
   "production_promotion_allowed":False,"source_modified":False}
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--propositions",type=Path,required=True)
 p.add_argument("--truth",type=Path,required=True)
 p.add_argument("--manifest",type=Path,required=True)
 p.add_argument("--output",type=Path,default=Path("results/runtime_adapter_v0135842.json"))
 a=p.parse_args();r=run(a.propositions,a.truth,a.manifest,a.output)
 print(json.dumps({"status":r["status"],"loaded":r["propositions_loaded"],
  "eligible":r["eligible_records"],"denied":len(r["denied_records"]),
  "case_statuses":[x["result"]["status"] for x in r["cases"]]},ensure_ascii=False))
 print("report:",a.output)
if __name__=="__main__":main()
