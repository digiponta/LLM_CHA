"""v0.4.15 explicit /wiki route: read-only article evidence -> wiki> output.

Not automatic search, learning, truth verification or promotion.
"""
from __future__ import annotations
import json
from pathlib import Path
from article_proposition_alignment_v0412 import align
from wikipedia_answer_prefix_v04141 import from_article_alignment

def render_wikipedia_evidence(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>128_000:
        raise ValueError("Wikipedia evidence missing or too large")
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("version")!="v0.4.9" or data.get("human_article_reviewed") is not False:
        raise ValueError("expected unreviewed v0.4.9 article evidence")
    if data.get("extract_kind")!="PLAIN_TEXT_INTRO" or data.get("is_full_article") is not False:
        raise ValueError("not a Wikipedia lead excerpt")
    if (data.get("truth_promotions")!=0 or data.get("semantic_memory_writes")!=0
            or data.get("eligible_for_training") is not False):
        raise ValueError("unsafe evidence state")
    result=align(data)
    if not result["propositions"]:
        return "[wiki-route=NO_EXTRACTIVE_DEFINITION, no wiki answer]"
    return from_article_alignment(result["propositions"][0],result,
                                  explicit_source_request=True)
