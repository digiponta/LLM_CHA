"""v0.5.48: unified persona policy and non-mutating route audit.

Persona has authority over presentation only. It MUST NOT rewrite generated
knowledge claims, source spans, truth states, or unknown/reject decisions.
"""
from persona_priority_v0547 import style

ROUTES=("MODEL_GENERATION","SEMANTIC_MEMORY","WIKIPEDIA_REPAIR","WIKIPEDIA_GROUNDED")
def persona_for(active="nagato"):
    return style(active)["persona"]

def audit(route, answer, *, persona="nagato", source=None, persona_applied=False):
    if route not in ROUTES:raise ValueError("unknown response route")
    p=persona_for(persona)
    return {"route":route,"persona":p,"persona_applied":bool(persona_applied),
      "persona_policy":"PRESENTATION_ONLY",
      "knowledge_source":source,
      "answer_unchanged":True,
      "persona_gap":not persona_applied,
      "verified":False,"train_ready":False,"auto_lookup":False,
      "auto_promote":False}

def status(active="nagato"):
    p=persona_for(active)
    return {"active_persona":p,"policy":"PRESENTATION_ONLY",
       "routes":{
          "MODEL_GENERATION":"AUDIT_ONLY",
          "SEMANTIC_MEMORY":"AUDIT_ONLY",
          "WIKIPEDIA_REPAIR":"PERSONA_STYLED",
          "WIKIPEDIA_GROUNDED":"PERSONA_STYLED"},
       "note":"Model or semantic outputs are not rewritten without grounded intent-safe formatting."}
