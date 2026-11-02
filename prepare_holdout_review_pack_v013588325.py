"""Prepare a development-only review pack from v0.13.58.83.25 draft.

Never auto-approve or label an independent holdout. Original source is untouched.
"""
import argparse
import json
from pathlib import Path

CONTEXT = {
 "multi_turn-01": ("鉱物の展示を見ました。", "どの鉱物が印象的でしたか？"),
 "multi_turn-02": ("スファレライトについて知りたい。", "どの点を知りたいですか？"),
 "multi_turn-03": ("今日は小説について話そう。", "どんな作品に関心がありますか？"),
 "multi_turn-04": ("宝石の硬度について話して。", "硬度は傷つきやすさに関係します。"),
 "multi_turn-05": ("この会話で星について話しました。", "星の話ですね。"),
 "multi_turn-06": ("屈折率について聞きたい。", "屈折率は光の進み方に関係します。"),
 "multi_turn-07": ("今は技術の説明を聞いています。", "続けましょう。"),
 "multi_turn-08": ("昨夜は天体観測の話をしたね。", "天体観測の話題ですね。"),
 "multi_turn-09": ("鉱物について話していました。", "鉱物の話を続けますか？"),
 "multi_turn-10": ("スファレライトについて説明して。", "どの性質を知りたいですか？"),
}
SUGGESTIONS = {
 "paraphrase": ("ADOPT", "Only if an approved, suitable RSE conversational response is available; otherwise abstention is acceptable."),
 "negation": ("PASS_THROUGH", "Do not adopt a conversational invitation; respect the user's negation."),
 "ambiguity": ("PASS_THROUGH", "Avoid adopting unsupported RSE content; clarify when context is insufficient."),
 "multi_turn": ("PASS_THROUGH", "Resolve referents using preceding turns; do not assume unsupported facts or RSE adoption."),
 "knowledge_collision": ("PASS_THROUGH", "Preserve the factual retrieval path and do not substitute a casual RSE answer."),
}

def prepare(source):
    if source.get("schema") != "llm-cha-independent-holdout-v1":
        raise ValueError("INVALID_SOURCE_SCHEMA")
    result = json.loads(json.dumps(source, ensure_ascii=False))
    result["notice"] = "DEVELOPMENT_REVIEW_PACK_NOT_INDEPENDENT; suggestions are not human labels"
    result["independence"] = {"human_attested": False, "reviewer": None,
                              "training_overlap": None, "development_overlap": None,
                              "evidence_notes": "Generated from existing development draft; not valid final holdout."}
    for case in result["cases"]:
        cid = case["id"]
        if cid in CONTEXT:
            user, assistant = CONTEXT[cid]
            case["turns"] = [{"role":"user","text":user},
                             {"role":"assistant","text":assistant}] + case["turns"]
        decision, rationale = SUGGESTIONS[case["category"]]
        case["suggested_decision"] = decision
        case["suggested_review_criteria"] = rationale
        case["expected_decision"] = None
        case["expected_answer_criteria"] = ""
        case["review_state"] = "PENDING"
        case["reviewer"] = None
        case["reviewed_at"] = None
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/independent_holdout_draft_v013588325.json")
    p.add_argument("--output", default="data/holdout_development_review_pack_v013588325.json")
    args = p.parse_args()
    src = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    data = prepare(src)
    dest = Path(args.output)
    if dest.exists():
        raise SystemExit("REFUSE_OVERWRITE")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":"DEVELOPMENT_REVIEW_ONLY","cases":len(data["cases"]),
      "multiturn_with_context":sum(c["category"]=="multi_turn" and sum(t["role"]=="user" for t in c["turns"])>=2 for c in data["cases"]),
      "human_approved":0,"output":str(dest)},ensure_ascii=False))
if __name__ == "__main__": main()
