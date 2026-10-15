"""v0.5.52: offline A/B/C persona study with unscored raw generations.

Uses the actual checkpoint for raw generation, and v0.5.50 for controller.
Hybrid is a conservative selector: controller for recognized non-factual
sharing, otherwise raw output (not an invented blending of claims).
No training or memory writes.
"""
import argparse
import json
from pathlib import Path
from persona_context_v0550 import PersonaContext

def study(scenarios, generate):
    rows=[]
    for scenario in scenarios:
        ctx=PersonaContext(scenario.get("persona","nagato"))
        history=[]
        for i,turn in enumerate(scenario["turns"]):
            user=turn["user"]
            prompt="".join("人: "+u+"\nAI: "+a+"\n" for u,a in history[-3:])+"人: "+user+"\nAI:"
            raw=generate(prompt)
            if not isinstance(raw,str):raise TypeError("generator must return text")
            ctrl=ctx.handle(user)
            candidate=ctrl["answer"] if ctrl else None
            hybrid=candidate if candidate is not None else raw
            expected=turn.get("expected_topic")
            rows.append({"scenario":scenario["id"],"turn":i+1,"user":user,
                "persona":ctx.persona,"raw_llm":{"reply":raw,"source":"MODEL_GENERATION"},
                "controller":{"reply":candidate,"route":ctrl["route"] if ctrl else "DELEGATE"},
                "hybrid":{"reply":hybrid,"selected":"CONTROLLER" if ctrl else "RAW_LLM"},
                "topic_required":expected is not None,
                "topic_expected":expected,
                "topic_correct":(bool(ctrl and ctrl.get("context_topic")==expected) if expected is not None else None),
                "human_persona_labels":{"raw_llm":None,"controller":None,"hybrid":None}})
            history.append((user,raw))
    required=[r for r in rows if r["topic_required"]]
    return {"version":"v0.5.52","benchmark":"RAW_VS_CONTROLLER_VS_HYBRID",
      "samples":len(rows),"topic_required":len(required),
      "controller_topic_retention":round(sum(r["topic_correct"] for r in required)/len(required),4) if required else None,
      "model_persona_consistency":None,"raw_topic_retention":None,
      "hybrid_persona_consistency":None,"human_labels_required":True,
      "hybrid_is_selector_not_model_training":True,"train_ready":False,
      "rows":rows}

def load_generator(model_path,tokenizer_path,device_name,max_tokens):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from chat import generate_reply
    device=torch.device(device_name if device_name!="auto" else ("cuda" if torch.cuda.is_available() else "cpu"))
    model,checkpoint=LanguageModel.load_checkpoint(str(model_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if model.vocab_size!=tokenizer.vocab_size:raise ValueError("vocab mismatch")
    def generate(prompt):
        return generate_reply(model,tokenizer,prompt,max_tokens,0.0,20,1.05,seed=0).text
    return generate,{"model_path":str(model_path),"tokenizer":str(tokenizer_path),
       "device":str(device),"checkpoint_epoch":checkpoint.get("epoch"),
       "checkpoint_loss":checkpoint.get("loss")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/persona_multiturn_eval_v0551.json")
    p.add_argument("--model",required=True,help="actual local checkpoint, never a mock")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",default="auto")
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--output",default="results/persona_ablation_v0552.json")
    args=p.parse_args()
    generator,meta=load_generator(args.model,args.tokenizer,args.device,args.max_new_tokens)
    cases=json.loads(Path(args.input).read_text(encoding="utf-8"))["scenarios"]
    out=study(cases,generator);out["actual_model"]=meta
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("output:",target)
if __name__=="__main__":main()
