"""v0.3.7.2 Means-Centric Semantic Transformation (conservative patterns).

Preserve semantic roles first; causative surface forms are explicitly licensed.
No claim that a tool/means always entails agency or literal causation.
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class MeansRelation:
    agent: str
    means: str
    predicate: str
    patient: str | None
    relation: str = "MEANS_OF"

# 'を' for intransitive movement/change; 'に' for transitive actions with a patient.
CAUSATIVES = {
    "移動する": ("移動させる", "を"),
    "回復する": ("回復させる", "を"),
    "作業する": ("作業させる", "に"),
    "問題を解く": ("問題を解かせる", "に"),
    "意思を伝える": ("意思を伝えさせる", "に"),
}

def parse(statement: str) -> MeansRelation | None:
    if not isinstance(statement,str):return None
    text=statement.strip().rstrip("。")
    match=re.fullmatch(r"(?P<agent>[^、。]{1,30})は、?(?P<means>[^、。]{1,30})によって、?(?P<predicate>[^、。]{1,60})",text)
    if not match:return None
    agent,means,predicate=(match.group(k).strip() for k in ("agent","means","predicate"))
    if not all((agent,means,predicate)):return None
    if predicate not in CAUSATIVES:return None
    return MeansRelation(agent,means,predicate,None)

def transform(statement: str) -> dict:
    relation=parse(statement)
    if relation is None:
        return {"status":"UNSUPPORTED","source":statement,"derived":None,
                "reason":"unsupported form; preserve original meaning"}
    verb,case=CAUSATIVES[relation.predicate]
    derived=f"{relation.means}は{relation.agent}{case}{verb}。"
    return {"status":"DERIVED","source":statement,"derived":derived,
            "semantic":{"relation":relation.relation,"agent":relation.agent,
                        "means":relation.means,"predicate":relation.predicate},
            "factual_truth":"NOT_ASSESSED","attribution":"PARAPHRASE_NOT_NEW_FACT"}
