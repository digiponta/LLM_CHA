"""Conservative Japanese fluency repair + semantic recheck (sidecar only).

Repairs only explicitly reviewed literal patterns. No open-ended rewriting,
training-data promotion, or changes to the live chat route.
"""
from dataclasses import dataclass,asdict
from semantic_response_gate_v09744 import assess

REPAIRS=(
 ("疲れたんだね。良かったんでしたね。","お疲れ様でした。楽しかったようで良かったですね。"),
)
SUSPECT=("良かったんでしたね","でしたですね","曼し","疲しい","�")

@dataclass(frozen=True)
class RepairResult:
    decision:str
    reason:str
    original:str
    repaired:str
    selected_response:str
    first_gate:str
    second_gate:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def fluency_diagnostic(text):
    t=str(text or "").strip()
    if not t:return "FAIL","empty"
    if any(x in t for x in SUSPECT):return "FAIL","suspect-japanese-pattern"
    if len(t)<5:return "REVIEW","short-utterance"
    return "REVIEW","no-proof-of-naturalness"

def repair_and_recheck(utterance,generated):
    original=str(generated or "").strip()
    first=assess(utterance,original)
    fluency,fluency_reason=fluency_diagnostic(original)
    # Explicitly reviewed correction, exact match only.
    candidate=next((new for old,new in REPAIRS if original==old),None)
    if candidate is not None:
        second=assess(utterance,candidate)
        if second.decision=="ACCEPT":
            return RepairResult("REPAIRED","reviewed-exact-repair",original,candidate,
                                candidate,first.decision,second.decision)
        candidate=None
    if first.decision=="ABSTAIN":
        return RepairResult("ABSTAIN","semantic-gate-abstained",original,"",original,
                            first.decision,"NOT_RUN")
    if fluency=="FAIL" or first.decision=="FALLBACK":
        if first.decision=="ABSTAIN" or not first.fallback_response:
            return RepairResult("ABSTAIN","no-validated-fallback",original,"",original,
                                first.decision,"NOT_RUN")
        second=assess(utterance,first.fallback_response)
        if second.decision=="ACCEPT":
            return RepairResult("FALLBACK","gate-or-fluency-failed",original,"",
                                first.fallback_response,first.decision,second.decision)
        return RepairResult("ABSTAIN","fallback-not-validated",original,"",original,
                            first.decision,second.decision)
    return RepairResult("REVIEW",fluency_reason,original,"",original,
                        first.decision,"NOT_RUN")
