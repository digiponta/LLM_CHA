"""v0.2.32.3 purpose prompt ablation over a frozen real checkpoint.

Controlled three-arm generation (raw, short purpose, full DSS) with identical
decoding. No purpose SFT or claimed gain in this version.
"""
import argparse,json
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import step,generation_context
from dialogue_guided_generation_v02322 import (
    CheckpointGenerator,prompt_raw,prompt_guided,LABEL,
)

SCENARIOS=[
    ("learn",["LLMを勉強したい"]),
    ("build",["Pythonでアプリを開発したい"]),
    ("repair",["LLMの出力がおかしい"]),
    ("chat",["Pythonについて雑談したい"]),
    ("context",["Pythonを勉強したい","それを作ってみたい"]),
    ("plan",["LLMを勉強したい","それから開発もしたい"]),
    ("confirm",["Pythonに興味がある","いいえ","Pythonを勉強したい"]),
]

def prompt_short(ctx):
    """Only the semantic labels; no long instruction or earlier dialogue."""
    topic=ctx["topic"] or "未確定"
    goals=" → ".join(LABEL.get(p,p) for p in ctx["purposes"]) or "未確定"
    return f"話題: {topic}\n目的: {goals}\n{prompt_raw(ctx['user_input'])}"

def prompt_variants(ctx):
    return {
        "raw":prompt_raw(ctx["user_input"]),
        "short":prompt_short(ctx),
        "full":prompt_guided(ctx),
    }

def execute(cases=SCENARIOS,generator=None,max_new_tokens=80,temperature=0.0):
    rows=[]
    for name,utterances in cases:
        d=DialogueState()
        for turn,utterance in enumerate(utterances):
            d,action,reply=step(d,utterance)
            ctx=generation_context(d,action,utterance)
            variants={}
            if action.startswith("ASK"):
                variants={key:{"source":"controller_skip","text":None} for key in ("raw","short","full")}
            else:
                for key,prompt in prompt_variants(ctx).items():
                    if generator is None:
                        variants[key]={"source":"checkpoint_not_loaded","text":None,
                                       "prompt_chars":len(prompt)}
                    else:
                        output=generator.generate(prompt,max_new_tokens=max_new_tokens,
                                                  temperature=temperature)
                        variants[key]={**output,"source":"checkpoint","prompt_chars":len(prompt)}
            rows.append({"scenario":name,"turn":turn+1,"user":utterance,"action":action,
                         "topic":d.topic,"purposes":list(d.purposes),"relation":d.relation,
                         "controller_reply":reply,"variants":variants})
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    p.add_argument("--controller-only",action="store_true")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--temperature",type=float,default=0.0)
    p.add_argument("--out",default="results/purpose_prompt_ablation_v02323.json")
    args=p.parse_args()
    generator=None if args.controller_only else CheckpointGenerator(args.model,args.tokenizer,args.device)
    rows=execute(generator=generator,max_new_tokens=args.max_new_tokens,temperature=args.temperature)
    for row in rows:
        print(f'[{row["scenario"]}:{row["turn"]}] action={row["action"]} topic={row["topic"]} purpose={row["purposes"]}')
        for name,output in row["variants"].items():
            print(f'  {name:5s}: {output["text"]!r} ({output["source"]})')
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",dest)
    print("Compare topical relevance, purpose fidelity, fluency, hallucinations and latency by human review.")
if __name__=="__main__":main()
