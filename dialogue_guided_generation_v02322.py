"""v0.2.32.2 DSS-guided real checkpoint inference.

Controller responses and neural outputs remain separately visible. No
training, no simulated LLM responses, no automatic semantic accuracy claims.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import step,generation_context

LABEL={"learning":"学習","development":"開発","troubleshooting":"問題解決","casual":"雑談"}
def prompt_raw(user):
    return f"人: {user}\nAI: "

def prompt_guided(ctx,turns=2):
    topic=ctx["topic"] or "未確定"
    purposes=" → ".join(LABEL.get(x,x) for x in ctx["purposes"]) or "未確定"
    relation=ctx["relation"]
    action=ctx["action"]
    history=ctx["history"][:-1][-max(0,turns):] if turns>0 else []
    parts=[f"会話の話題: {topic}",f"ユーザーの目的: {purposes}",
           f"目的間の関係: {relation}",f"会話行動: {action}",
           "回答方針: 話題と目的を維持して自然な日本語で具体的に回答する。知らない事実は作らない。"]
    for item in history:
        parts.extend([f"人: {item['user']}",f"AI: {item['response']}"])
    parts.append(prompt_raw(ctx["user_input"]))
    return "\n".join(parts)

def template_reply(ctx,controller_reply):
    # Deterministic reference, not neural generation.
    return controller_reply

class CheckpointGenerator:
    def __init__(self,model_path,tokenizer_path,device="auto"):
        import torch
        from model import LanguageModel
        from tokenizer_bpe import Tokenizer
        self.torch=torch
        self.device=torch.device("cuda" if device=="auto" and torch.cuda.is_available() else
                                 "cpu" if device=="auto" else device)
        mp=Path(model_path);tp=Path(tokenizer_path)
        for path in (mp,tp):
            if not path.is_file():
                raise FileNotFoundError(f"Required inference asset missing: {path}")
        self.tokenizer=Tokenizer.load(str(tp))
        self.model,self.checkpoint=LanguageModel.load_checkpoint(str(mp),device=self.device)
        if self.model.vocab_size!=self.tokenizer.vocab_size:
            raise ValueError("Checkpoint/tokenizer vocabulary size mismatch")
        self.model.eval()
    def generate(self,prompt,max_new_tokens=80,temperature=0.0,top_k=20):
        ids=self.tokenizer.encode(prompt,add_bos=True)
        if not ids: raise ValueError("Tokenizer returned empty prompt IDs")
        start=time.perf_counter()
        with self.torch.inference_mode():
            output=self.model.generate(ids,max_new_tokens=max_new_tokens,
                  eos_id=self.tokenizer.eos_id,temperature=temperature,top_k=top_k,
                  repetition_penalty=1.05)
        tokens=output[len(ids):]
        text=self.tokenizer.decode(tokens).split("\n人:",1)[0].split("\nAI:",1)[0].strip()
        return {"text":text,"generated_tokens":len(tokens),
                "elapsed_seconds":round(time.perf_counter()-start,4)}

def evaluate_turn(state,utterance,generator=None,max_new_tokens=80,temperature=0.0):
    state,action,controller_reply=step(state,utterance)
    ctx=generation_context(state,action,utterance)
    result={"user":utterance,"action":action,"dss_topic":state.topic,
            "dss_purposes":list(state.purposes),"controller_reply":controller_reply,
            "variants":{"template":{"text":template_reply(ctx,controller_reply),
                                    "source":"deterministic_controller"}}}
    if action.startswith("ASK"):
        result["variants"]["raw"]={"text":None,"source":"not_called_controller_owned"}
        result["variants"]["guided"]={"text":None,"source":"not_called_controller_owned"}
    elif generator is not None:
        result["variants"]["raw"]={**generator.generate(prompt_raw(utterance),
            max_new_tokens=max_new_tokens,temperature=temperature),"source":"checkpoint"}
        result["variants"]["guided"]={**generator.generate(prompt_guided(ctx),
            max_new_tokens=max_new_tokens,temperature=temperature),"source":"checkpoint"}
    else:
        result["variants"]["raw"]={"text":None,"source":"checkpoint_not_loaded"}
        result["variants"]["guided"]={"text":None,"source":"checkpoint_not_loaded"}
    return state,result

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--temperature",type=float,default=0.0)
    p.add_argument("--controller-only",action="store_true",help="No checkpoint loaded; display only DSS reference output")
    p.add_argument("--show-prompts",action="store_true")
    return p.parse_args()
def main():
    a=parse_args()
    generator=None if a.controller_only else CheckpointGenerator(a.model,a.tokenizer,a.device)
    d=DialogueState()
    print("LLM_CHA v0.2.32.2 Dialogue-Guided Generation; /quit /reset /state")
    while True:
        try:user=input("You> ").strip()
        except (EOFError,KeyboardInterrupt):break
        if user=="/quit":break
        if user=="/reset":d=DialogueState();print("DSS reset");continue
        if user=="/state":
            from dataclasses import asdict
            print(json.dumps(asdict(d),ensure_ascii=False,indent=2));continue
        if not user:continue
        d,record=evaluate_turn(d,user,generator,a.max_new_tokens,a.temperature)
        if a.show_prompts and generator is not None and not record["action"].startswith("ASK"):
            print("RAW PROMPT:",prompt_raw(user))
            print("GUIDED PROMPT:",prompt_guided(generation_context(d,record["action"],user)))
        print(json.dumps(record,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
