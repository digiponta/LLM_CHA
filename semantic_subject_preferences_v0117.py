"""v0.11.7 subject/context/memory-keyed reconciliation preference reuse.

Reuse is restricted to prefer_b (stable memory side), never prefer_a when
generated A changes. Candidate history remains immutable and unapproved.
"""
import hashlib
import json
from pathlib import Path
from semantic_dialogue_bridge_v0112 import DialogueBridge, _key
from semantic_equivalence_router_v0111 import resolve
from semantic_reconciliation_v0110 import canonical_form, _save, render_question

def preference_key(question, subject, context, memory_answer):
    values=[canonical_form(x) for x in (question,subject,context,memory_answer)]
    return hashlib.sha256(json.dumps(values,ensure_ascii=False).encode("utf-8")).hexdigest()

class SubjectPreferenceBridge(DialogueBridge):
    def __init__(self, root="data/semantic_dialogue_v0113"):
        super().__init__(root)
        self.subject_index=self.root/"subject_preference_index"
        self.pending_index=self.root/"subject_preference_pending"

    def lookup_preference(self, question, subject, context, memory_answer):
        """Return reviewed prefer_b only for this exact question/subject/context/memory."""
        key=preference_key(question,subject,context,memory_answer)
        index=self.subject_index/(key+".json")
        if not index.is_file():
            return None
        entry=json.loads(index.read_text(encoding="utf-8"))
        ticket=self.tickets.get(entry["ticket_id"])
        if (ticket["state"]=="USER_REVIEWED" and ticket["review"]["decision"]=="prefer_b"
            and canonical_form(ticket["candidates"]["b"]["text"])==canonical_form(memory_answer)
            and canonical_form(ticket["question"])==canonical_form(question)
            and ticket["review"]["context"]==context):
            return {"action":"USER_PREFERENCE","answer":memory_answer,
                    "ticket_id":ticket["id"],"approval_state":"NOT_APPROVED",
                    "factual_truth":"UNVERIFIED",
                    "reuse_scope":"QUESTION_SUBJECT_CONTEXT_MEMORY"}
        return None

    def compare(self, question, generated_answer, memory_answer, assertion=None, *, context="", subject=None):
        subject=subject or question
        existing=self.lookup_preference(question,subject,context,memory_answer)
        if existing is not None:
            return existing
        key=preference_key(question,subject,context,memory_answer)
        # Do not use the legacy three-text preference cache here: it omits
        # subject and context and can silently reuse a decision in the wrong scope.
        result=resolve(question,generated_answer,memory_answer,assertion,store=self.tickets)
        if result["action"]=="ASK_USER":
            result["message"]=render_question(self.tickets.get(result["ticket_id"]))
            result["session_key"]=_key(question,generated_answer,memory_answer)
        if result["action"]=="ASK_USER":
            _save(self.pending_index/(result["ticket_id"]+".json"),
                  {"preference_key":key,"context":context,"subject":subject})
        return result

    def review(self, ticket_id, decision, *, context=""):
        result=super().review(ticket_id,decision,context=context)
        sidecar=self.pending_index/(ticket_id+".json")
        if sidecar.exists() and decision=="prefer_b":
            meta=json.loads(sidecar.read_text(encoding="utf-8"))
            if meta["context"]==context:
                _save(self.subject_index/(meta["preference_key"]+".json"),{"ticket_id":ticket_id})
        return result
