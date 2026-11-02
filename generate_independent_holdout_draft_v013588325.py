"""Create an UNREVIEWED draft; it is never valid independent evidence as generated."""
import argparse
import json
from pathlib import Path

QUESTIONS = {
 "paraphrase": ["少し話せますか？","ちょっと雑談したいです","会話に付き合ってくれますか","お話ししませんか","何かおしゃべりしよう","今少し会話できる？","気軽に話したい","ちょっとだけ相手をして","話し相手になって","何か話題を出して"],
 "negation": ["今は話したくない","会話の誘いではありません","雑談を始めないで","今何してるかは聞いていません","話しかけないでください","会話をしたいわけではない","返事はまだ不要です","話題の提案はいりません","今日は雑談しない","今は活動状況を尋ねていない"],
 "ambiguity": ["少しだけ","どうかな","それについて","今は？","何かない？","そうなの？","もう少し","次は","気になる","教えて"],
 "multi_turn": ["スファレライトについて話そう","スファレライトの成分は？","今は量子力学の話をしたい","その特徴を説明して","昨日の話に戻ろう","それは何のこと？","今は雑談の時間？","さっきの話を続けて","宝石はきれいですね","では化学組成は？"],
 "knowledge_collision": ["スファレライトの化学式は？","CPUの意味は？","量子力学とは何ですか","吾輩は猫であるの著者は？","亜鉛の原子番号は？","SQUIDとは何か","宝石の硬度とは何ですか","地球の衛星は？","水の分子式は？","RSEは何の略称ですか"],
}
def build():
    cases = []
    for category, questions in QUESTIONS.items():
        for number, question in enumerate(questions, 1):
            cases.append({"id": f"{category}-{number:02d}", "category": category,
                          "turns": [{"role": "user", "text": question}],
                          "expected_decision": None, "expected_answer_criteria": "",
                          "protected_knowledge": False, "unknown_expected": False,
                          "review_state": "PENDING", "reviewer": None, "reviewed_at": None})
    return {"schema": "llm-cha-independent-holdout-v1",
            "notice": "DEVELOPMENT DRAFT ONLY: cannot count as independent holdout until independently sourced and human reviewed; replace contaminated prompts.",
            "independence": {"human_attested": False, "reviewer": None,
                             "training_overlap": None, "development_overlap": None,
                             "evidence_notes": ""},
            "cases": cases}
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="data/independent_holdout_draft_v013588325.json")
    args = p.parse_args()
    path = Path(args.output)
    if path.exists():
        raise SystemExit("REFUSE_OVERWRITE")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"DRAFT_ONLY: {path} 50 cases, human review and independence required")
if __name__ == "__main__":
    main()
