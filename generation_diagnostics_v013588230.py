"""Session-only diagnostics for evidence-conditioned generation.

Counts are observational and do not claim semantic correctness.
No conversation or personal content is persisted by default.
"""
from collections import Counter
from dataclasses import dataclass,field

@dataclass
class GenerationDiagnostics:
    events:list=field(default_factory=list)
    def record(self, gate, evidence_status="EVIDENCE", topic="", candidate="", final=""):
        accepted=gate=="ACCEPT_SOURCE_EXTRACT"
        event={"gate":str(gate),"evidence_status":str(evidence_status),
               "topic":str(topic),"candidate_chars":len(candidate or ""),
               "final_chars":len(final or ""),"accepted":accepted,
               "fallback":not accepted}
        self.events.append(event)
        return event
    def report(self):
        n=len(self.events)
        counts=Counter(e["gate"] for e in self.events)
        if not n:return {"cases":0,"acceptance_rate":None,"fallback_rate":None,
                          "unknown_rate":None,"evidence_rejection_rate":None,
                          "gate_counts":{}}
        def rate(value):return round(value/n,4)
        return {"cases":n,
                "acceptance_rate":rate(sum(e["accepted"] for e in self.events)),
                "fallback_rate":rate(sum(e["fallback"] for e in self.events)),
                "unknown_rate":rate(counts["REJECT_UNKNOWN"]),
                "evidence_rejection_rate":rate(counts["REJECT_NOT_ENTAILED"]+
                   counts["REJECT_UNGROUNDED"]),
                "gate_counts":dict(sorted(counts.items()))}
    def reset(self):self.events.clear()
    def comparison(self):
        report=self.report()
        return {"baseline":"attributed_evidence_excerpt",
                "candidate":"local_transformer_with_evidence_gate",
                "note":"Quality superiority cannot be established without human-rated paired outputs.",
                "observed":report}
