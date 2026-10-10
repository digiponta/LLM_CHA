"""LLM_CHA v0.2.33.37 — persistent experimental candidate adapter.

File-backed shadow store only, never a production Semantic Memory store.
An injectable CandidateStore contract from v0.2.33.36 is preserved.
"""
import argparse,json,os,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from dss_unknown_adapter_v023336 import IntegrationResolver,MockDSS

def utcnow():
    return datetime.now(timezone.utc)

class JsonCandidateStore:
    def __init__(self,path,clock=utcnow,ttl_hours=24):
        if ttl_hours<=0:raise ValueError("ttl must be positive")
        self.path=Path(path);self.clock=clock;self.ttl=timedelta(hours=ttl_hours)
        self._read()
    def _read(self):
        if not self.path.exists():return {"version":1,"sequence":0,"records":[]}
        data=json.loads(self.path.read_text(encoding="utf8"))
        if data.get("version")!=1 or not isinstance(data.get("records"),list):
            raise ValueError("Unsupported shadow-store schema")
        return data
    def _write(self,data):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=str(self.path.parent),prefix=".candidate-",suffix=".tmp")
        try:
            with os.fdopen(fd,"w",encoding="utf8") as f:
                json.dump(data,f,ensure_ascii=False,indent=2)
                f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    def _valid(self,r):
        try:return self.clock()<datetime.fromisoformat(r["expires_at"])
        except (TypeError,ValueError,KeyError):return False
    def lookup(self,context,subject,slot):
        records=self._read()["records"]
        for r in reversed(records):
            if r["context"]==context and r["subject"]==subject and r["slot"]==slot and r["status"]=="approved" and self._valid(r):
                return r["value"]
        return None
    def propose(self,context,subject,slot,value):
        if not all((context,subject,slot,value)):raise ValueError("Missing candidate fields")
        data=self._read();data["sequence"]+=1
        id=f"shadow-{data['sequence']}"
        data["records"].append({"id":id,"context":context,"subject":subject,"slot":slot,
            "value":value,"status":"pending","source":"explicit_user_reply",
            "created_at":self.clock().isoformat(),"expires_at":(self.clock()+self.ttl).isoformat()})
        self._write(data);return id
    def _change(self,id,target):
        data=self._read();match=next((r for r in data["records"] if r["id"]==id),None)
        if not match or match["status"]!="pending":raise ValueError("Candidate is not pending")
        if not self._valid(match):raise ValueError("Candidate expired")
        if target=="approved":
            for r in data["records"]:
                if all(r[k]==match[k] for k in ("context","subject","slot")) and r["status"]=="approved":
                    r["status"]="superseded"
        match["status"]=target
        self._write(data)
    def approve(self,id):self._change(id,"approved")
    def reject(self,id):
        try:self._change(id,"rejected")
        except ValueError:
            # Expired pending candidates remain non-approved; rejection is idempotent.
            data=self._read()
            for r in data["records"]:
                if r["id"]==id and r["status"]=="pending":
                    r["status"]="expired";self._write(data);return
    def invalidate(self,context,subject,slot):
        data=self._read()
        for r in data["records"]:
            if (r["context"],r["subject"],r["slot"])==(context,subject,slot) and r["status"] in ("pending","approved"):
                r["status"]="invalidated"
        self._write(data)

def demo(path):
    shadow=JsonCandidateStore(path)
    r=IntegrationResolver(MockDSS(),shadow)
    transcript=[]
    for method,value in (("receive","昨日の実験の続きをやって"),
                         ("receive","cursor"),("confirm",True),
                         ("receive","前回の実験の続きをやって")):
        result=r.confirm(value,"conversation-A") if method=="confirm" else r.receive(value,"conversation-A")
        transcript.append({"method":method,"input":value,"result":result})
    r2=IntegrationResolver(MockDSS(),JsonCandidateStore(path))
    transcript.append({"method":"restart","result":r2.receive("前回の実験の続きをやって","conversation-A")})
    transcript.append({"method":"other-context","result":r2.receive("昨日の実験の続きをやって","conversation-B")})
    return transcript

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--shadow-store",default="results/unknown_candidate_shadow_v023337.json")
    p.add_argument("--out",default="results/semantic_candidate_adapter_v023337.json")
    a=p.parse_args()
    if not a.demo:print("Use --demo. No production Semantic Memory integration.");return
    if Path(a.out).exists() or Path(a.shadow_store).exists():raise FileExistsError("Refusing to overwrite shadow data")
    events=demo(a.shadow_store)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.37","events":events,
       "scope":"isolated shadow-store integration only, not production Semantic Memory",
       "not_tested":["DSS live adapter","Semantic Memory live API","multi-process concurrent writers","LLM internalization"]},
       ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(events,ensure_ascii=False,indent=2))
    print("Saved",out)
if __name__=="__main__":main()
