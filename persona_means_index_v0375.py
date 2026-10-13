"""v0.3.7.5: read-only bidirectional MEANS_OF persona index.

Only licensed grammatical transformations from source lines, never factual promotion.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from means_centric_semantics_v0372 import parse, transform
from persona_semantic_memory_v0371 import segments

@dataclass(frozen=True)
class MeansEvidence:
    agent: str
    means: str
    predicate: str
    original: str
    derived: str
    source: str
    line: int
    segment: int
    factual_truth: str = "NOT_ASSESSED"

def build_index(source: str | Path):
    source=Path(source)
    rows=[]
    for line_no,line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(),1):
        for part_no,part in enumerate(segments(line),1):
            relation=parse(part)
            if relation is None:
                continue
            changed=transform(part)
            if changed["status"]!="DERIVED":
                continue
            rows.append(MeansEvidence(relation.agent,relation.means,relation.predicate,
                                     part,changed["derived"],str(source),line_no,part_no))
    return rows

def query_focus(question: str):
    text=question.strip().rstrip("。？！!? ")
    for pattern,role in (
        (r"(.+?)は(?:何をする(?:もの)?|どのように役立つ)(?:の)?(?:ですか|だろう|か)?", "means"),
        (r"(.+?)によって(?:誰が|何が|何を)(?:する|できる)(?:の)?(?:ですか|か)?", "means"),
        (r"(.+?)は(?:何によって|どんな手段で)(?:.+)?", "agent"),
    ):
        match=re.fullmatch(pattern,text)
        if match:
            return role,match.group(1).strip()
    return None

def lookup(source: str | Path, question: str):
    intent=query_focus(question)
    if intent is None:return None
    role,focus=intent
    matches=[row for row in build_index(source)
             if (row.means if role=="means" else row.agent)==focus]
    if not matches:return None
    row=matches[0]
    return {"focus":focus,"role":role,"answer":row.derived if role=="means" else row.original,
            "line":row.line,"segment":row.segment,"source":row.source,
            "original":row.original,"derived":row.derived,"relation":"MEANS_OF",
            "factual_truth":row.factual_truth,"count":len(matches)}
