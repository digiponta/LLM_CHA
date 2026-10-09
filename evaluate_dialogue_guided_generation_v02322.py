"""Run side-by-side generated replies. Human review required; no self-declared accuracy."""
import argparse,json
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState
from dialogue_guided_generation_v02322 import CheckpointGenerator,evaluate_turn
CASES=[
 ("learning",["LLMを勉強したい"]),
 ("development",["Pythonでアプリを開発したい"]),
 ("casual",["Pythonについて雑談したい"]),
 ("purpose-transition",["Pythonを勉強したい","それを作ってみたい"]),
 ("incremental-plan",["LLMを勉強したい","それから開発もしたい"]),
 ("confirmation",["Pythonに興味がある","いいえ","Pythonを勉強したい"]),
]
def run(generator=None,max_new_tokens=80):
    rows=[]
    for name,utterances in CASES:
        state=DialogueState()
        for utterance in utterances:
            state,result=evaluate_turn(state,utterance,generator,max_new_tokens,0.0)
            result["scenario"]=name
            rows.append(result)
    return rows
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--controller-only",action="store_true")
    p.add_argument("--out",default="results/dialogue_guided_generation_v02322.json")
    a=p.parse_args()
    gen=None if a.controller_only else CheckpointGenerator(a.model,a.tokenizer,a.device)
    rows=run(gen,a.max_new_tokens)
    for row in rows:
        print(f'{row["scenario"]}: {row["action"]} topic={row["dss_topic"]} purposes={row["dss_purposes"]}')
        for name,v in row["variants"].items():
            print(f' {name:8s} [{v["source"]}]: {v["text"]!r}')
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Saved: {path}")
    print("Human review required: topic fidelity / intent fidelity / Japanese fluency / unsupported claims.")
if __name__=="__main__":main()
