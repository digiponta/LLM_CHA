"""v0.4.24 opt-in quality capture; append only, separate from training.

Never records commands, persona fixed replies, Wikipedia or retrieval routes.
Write failures raise to caller, which must contain them without disrupting chat.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
from uuid import uuid4

DEFAULT_PATH=Path("results/persona_capture_new.jsonl")
MAX_BYTES=2_000_000

class QualityCapture:
    def __init__(self,path=DEFAULT_PATH):
        self.path=Path(path)
        self.enabled=False
    def command(self,text):
        if text not in ("/capture on","/capture off","/capture status"):
            return None
        if text=="/capture on":self.enabled=True
        if text=="/capture off":self.enabled=False
        count=0
        if self.path.is_file():
            count=sum(bool(line.strip()) for line in
                      self.path.read_text(encoding="utf-8-sig").splitlines())
        return {"enabled":self.enabled,"path":str(self.path),"records":count}
    def record(self,question,answer,*,agreement,semantic_agreement,runtime_accepted):
        if not self.enabled:return None
        if not isinstance(question,str) or not question.strip() or not isinstance(answer,str):
            raise ValueError("text")
        for value in (agreement,semantic_agreement):
            if type(value) not in (float,int) or not math.isfinite(value) or not 0<=value<=1:
                raise ValueError("score")
        if type(runtime_accepted) is not bool:raise ValueError("runtime_accepted")
        row={"id":"capture-"+uuid4().hex,"question":question,"answer":answer,
             "agreement":agreement,"semantic_agreement":semantic_agreement,
             "runtime_accepted":runtime_accepted}
        encoded=(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")
        if self.path.is_symlink():raise OSError("capture path is symlink")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        current=self.path.stat().st_size if self.path.exists() else 0
        if current+len(encoded)>MAX_BYTES:raise OSError("capture file size limit")
        with self.path.open("ab") as f:
            f.write(encoded)
            f.flush()
        return row["id"]
