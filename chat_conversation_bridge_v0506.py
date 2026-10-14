#!/usr/bin/env python3
"""Opt-in v0.5.6 conversation memory bridge for legacy chat.py.

Do not alter model inference, semantic sleep learning or truth gates.
Conversation storage: A=user; B=assistant (explicit legacy extractor mapping).
Only accepted responses are recorded; other paths are deliberately omitted.
Single writer; no automatic model training, promotion or eviction.
"""
import json
import uuid
from pathlib import Path
from conversation_resource_memory_v042866 import new_conversation,append_turn,close_session,write_json_atomic,validate
from checkpoint_optimization_v0504 import commit as incremental_commit
from benchmark_compact_evidence_v0502 import pack,verify
from safe_storage_migration_v0506 import migrate
from conversation_retrieval_v0509 import retrieve,restore_user_context

VERSION="v0.5.6-chat-bridge"

class ConversationBridge:
    def __init__(self,root):
        self.root=Path(root)
        self.source=None
        self.enabled=False

    def start(self,conversation_id=None):
        if self.enabled:raise ValueError("close current conversation first")
        cid=conversation_id or uuid.uuid4().hex
        if not cid or not all(x.isalnum() or x in "-_" for x in cid):
            raise ValueError("conversation ID must be alphanumeric, hyphen or underscore")
        self.root.mkdir(parents=True,exist_ok=True)
        source=self.root/(cid+".conversation.json")
        if source.exists():raise ValueError("conversation already exists; refusing overwrite")
        write_json_atomic(new_conversation(cid),source)
        self.source=source
        self.enabled=True
        return cid

    def load_closed(self,conversation_id):
        if self.enabled:raise ValueError("close active conversation first")
        if not conversation_id or not all(c.isalnum() or c in "-_" for c in conversation_id):
            raise ValueError("invalid conversation ID")
        path=self.root/(conversation_id+".conversation.json")
        if not path.is_file() or path.is_symlink():raise ValueError("conversation not found")
        record=json.loads(path.read_text(encoding="utf-8-sig"))
        validate(record)
        if record["conversation_id"]!=conversation_id or record["active"]:
            raise ValueError("only completed conversations may be loaded")
        self.source=path
        self.enabled=False
        return self.status()

    def recall(self,query,limit=3):
        if self.source is None:return []
        return retrieve(self.source,query,limit=limit)

    def _load(self):
        if self.source is None:raise ValueError("no conversation started")
        record=json.loads(self.source.read_text(encoding="utf-8-sig"))
        validate(record)
        return record

    def record_user(self,text):
        if not self.enabled:return False
        if not text.strip():return False
        record=self._load()
        if not record["active"]:raise ValueError("conversation closed")
        append_turn(record,"A",text)
        write_json_atomic(record,self.source)
        return True

    def record_assistant(self,text):
        if not self.enabled:return False
        if not text.strip():return False
        record=self._load()
        if not record["active"]:raise ValueError("conversation closed")
        append_turn(record,"B",text)
        write_json_atomic(record,self.source)
        return True

    def record_accepted(self,user_text,assistant_text):
        if not self.enabled:return False
        if not user_text.strip() or not assistant_text.strip():return False
        record=self._load()
        if not record["active"]:raise ValueError("conversation closed")
        # Mapping for current extraction rules, not a claim about a person.
        append_turn(record,"A",user_text)
        append_turn(record,"B",assistant_text)
        write_json_atomic(record,self.source)
        return True

    def status(self):
        if self.source is None:
            return {"version":VERSION,"enabled":False,"conversation_id":None}
        r=self._load()
        return {"version":VERSION,"enabled":self.enabled,
            "conversation_id":r["conversation_id"],"turns":r["last_turn"],
            "status":r["status"],"active":r["active"],"path":str(self.source)}

    def close(self):
        if not self.enabled:raise ValueError("conversation is not active")
        r=self._load();close_session(r)
        write_json_atomic(r,self.source)
        self.enabled=False
        return self.status()

    def sleep(self):
        r=self._load()
        if r["active"]:raise ValueError("close the session before /cha-sleep")
        checkpoint=self.root.parent/"cha_checkpoints"/(r["conversation_id"]+".incremental.json")
        result=incremental_commit(r,checkpoint)
        result["checkpoint_path"]=str(checkpoint)
        return result

    def migrate(self):
        r=self._load()
        if r["active"]:raise ValueError("close the session before /cha-migrate")
        target=self.root.parent/"cha_compact"/(r["conversation_id"]+".compact.json")
        receipt=self.root.parent/"cha_compact"/(r["conversation_id"]+".receipt.json")
        return migrate(self.source,target,receipt)
