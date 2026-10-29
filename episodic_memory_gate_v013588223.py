"""Approval-gated episodic semantic store (separate from model/knowledge weights).

Session snapshots become durable only upon an explicit approve command.
Persistence uses atomic replace. No auto-training or Semantic Memory injection.
"""
import copy
import json
import os
import uuid
from datetime import datetime,timezone
from pathlib import Path

SCHEMA="llm-cha-episodic-semantic-v1"
def canonical_episode(episode):
    if not episode or not episode.subject or not episode.topic:
        raise ValueError("Missing episode subject/topic")
    observations=[]
    for x in episode.observations:
        observations.append({
            "original_utterance":str(x.get("original_utterance",x.get("text","")))[:2000],
            "text":str(x.get("text",""))[:1000],
            "dimensions":list(x.get("dimensions",[])),
            "semantic":copy.deepcopy(x.get("semantic",[])),
            "provenance":"USER_SELF_REPORTED",
        })
    return {"schema":SCHEMA,"episode_id":str(uuid.uuid4()),
            "topic":episode.topic,"subject":episode.subject,
            "action":episode.action,"observations":observations,
            "provenance":"USER_SELF_REPORTED",
            "approval":"PENDING","lifecycle":"ACTIVE",
            "created_at":datetime.now(timezone.utc).isoformat()}

class EpisodicMemoryGate:
    def __init__(self,path):
        self.path=Path(path)
        self.pending={}
    def stage(self,episode):
        record=canonical_episode(episode)
        self.pending[record["episode_id"]]=record
        return copy.deepcopy(record)
    def _load(self):
        if not self.path.exists():return []
        data=json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data,list):raise ValueError("Invalid episodic store")
        return data
    def approve(self,episode_id):
        if episode_id not in self.pending:raise KeyError("Unknown pending episode ID")
        record=copy.deepcopy(self.pending[episode_id])
        record["approval"]="APPROVED"
        records=self._load()
        if any(x.get("episode_id")==episode_id for x in records):
            raise ValueError("Episode already saved")
        records.append(record)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_name(self.path.name+".tmp")
        try:
            with tmp.open("w",encoding="utf-8") as f:
                json.dump(records,f,ensure_ascii=False,indent=2)
                f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.path)
        finally:
            if tmp.exists():tmp.unlink()
        del self.pending[episode_id]
        return copy.deepcopy(record)
    def reject(self,episode_id):
        if episode_id not in self.pending:raise KeyError("Unknown pending episode ID")
        del self.pending[episode_id]
    def list_approved(self):
        return copy.deepcopy(self._load())
    def revoke(self,episode_id):
        records=self._load()
        updated=[x for x in records if x.get("episode_id")!=episode_id]
        if len(updated)==len(records):raise KeyError("Unknown approved episode ID")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_name(self.path.name+".tmp")
        try:
            tmp.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding="utf-8")
            os.replace(tmp,self.path)
        finally:
            if tmp.exists():tmp.unlink()
        return True
