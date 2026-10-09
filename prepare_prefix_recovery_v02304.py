"""v0.2.30.4: deterministic recovery-mode labels and training pairs.

Safety constraint: a broken prefix is never concatenated with a clean answer
as if it were a fluent continuation. It becomes an explicit restart command.
"""
import argparse,json
from pathlib import Path
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT

# Curated controlled CONTINUE stems and observed-style RESTART examples.
OBSERVED={
 "宇宙探査":("宇宙探査は、","宇宙には、まだ解明されていない現象が多くある。"),
 "カレー":("カレーは、","長門有希。"),
 "クラシック音楽":("クラシック音楽では、","それなら、いえばすね。"),
 "ゲーム開発":("ゲーム開発では、","ゲームとか、感じですね。"),
 "歴史小説":("歴史小説では、","宇宙には、まだ解明されていない現象が多くある。"),
 "写真撮影":("写真撮影では、","モデルを使って処理するのが好きです。"),
}
CONTINUE={
 "宇宙探査":"探査機から届く観測データを調べると、惑星の環境が分かる。",
 "カレー":"香辛料の組み合わせで、香りや辛さが変わる。",
 "クラシック音楽":"楽器の重なりと旋律の移り変わりが聴きどころになる。",
 "ゲーム開発":"操作に対する反応を試しながら遊びやすさを改善する。",
 "歴史小説":"時代背景と登場人物の判断を重ねて楽しめる。",
 "写真撮影":"光の向きや構図を変えると写真の印象が変化する。",
}
def classify(topic,prefix):
    """Conservative label: short on-topic stem is continuable; else restart."""
    stems=(topic+"は、",topic+"では、",topic+"について、")
    if prefix in stems:return "continue"
    return "restart"

def build():
    if set(TRAIN)&set(HOLDOUT):raise ValueError("topic leakage")
    result=[]
    for topic,(stem,bad) in OBSERVED.items():
        for mode,prefix in (("continue",stem),("restart",bad)):
            if classify(topic,prefix)!=mode:raise ValueError("mode inconsistent")
            if mode=="continue":
                # Explicit special dialogue tag; prefix is context, never
                # falsely presented as generated portion of the answer.
                prompt=f"人: {topic}について話を続けて\nAI: {prefix}\n人: [CONTINUE] 同じ話題を続けて"
                answer=CONTINUE[topic]
            else:
                prompt=f"人: {topic}について話を続けて\nAI: {prefix}\n人: [RESTART] 最初から話題に沿って答え直して"
                answer=f"{topic}について、{CONTINUE[topic]}"
            result.append({"user":prompt,"assistant":answer,"topic":topic,"mode":mode,"prefix":prefix})
    if len(result)!=12:raise ValueError("expected 12 recovery rows")
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="data/prefix_recovery_v02304/train_preformatted.jsonl")
    p.add_argument("--audit",default="data/prefix_recovery_v02304/mode_audit.jsonl")
    a=p.parse_args()
    rows=build()
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("".join(json.dumps({"user":r["user"],"assistant":r["assistant"]},ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    audit=Path(a.audit);audit.parent.mkdir(parents=True,exist_ok=True)
    audit.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print("Recovery examples: 12 (continue=6, restart=6)")
    print("Output:",output)
if __name__=="__main__":main()
