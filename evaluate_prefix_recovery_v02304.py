"""Evaluate explicit recovery-command learning on matched prompts.

No unsupported claim of autonomous failure detection: labels are supplied
by the test case. This measures ability to follow CONTINUE/RESTART requests.
"""
import argparse,json,re
from collections import defaultdict
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from prepare_prefix_recovery_v02304 import build,CONTINUE

def score(topic,mode,output):
    text=re.sub(r"\s+","",output)
    key_tokens={
        "宇宙探査":("探査機","惑星","観測"),
        "カレー":("香辛料","辛さ","香り"),
        "クラシック音楽":("楽器","旋律","音楽"),
        "ゲーム開発":("操作","遊び","ゲーム"),
        "歴史小説":("時代","歴史","人物"),
        "写真撮影":("光","写真","構図"),
    }
    lexical=any(k in text for k in key_tokens[topic])
    topic_exact=topic in text
    # A restart is expected to identify the topic; a continuation need
    # not repeat the entire topic string.
    return {"lexical_topic":lexical,"topic_exact":topic_exact,
            "nonempty":bool(text),"restart_topic_mention":mode=="restart" and topic_exact}

@torch.no_grad()
def generate(model,tok,user,max_new_tokens):
    prefix=tok.encode(user+"\nAI: ",add_bos=True)
    output=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                          temperature=0.0,repetition_penalty=1.15)
    return tok.decode(output[len(prefix):],skip_special_tokens=True).strip()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",action="append",help="NAME=CHECKPOINT")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--max-new-tokens",type=int,default=96)
    p.add_argument("--out",default="results/prefix_recovery_eval_v02304.jsonl")
    a=p.parse_args()
    if a.max_new_tokens<1:p.error("max-new-tokens must be positive")
    models={"continuation":"model/model-llm-cha-topic-continuation-v02302.pt",
            "recovery":"model/model-llm-cha-prefix-recovery-v02304.pt"}
    if a.model:
        models={}
        for s in a.model:
            name,sep,path=s.partition("=")
            if not sep or not name or not path:p.error("expected NAME=CHECKPOINT")
            models[name]=path
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cases=build()
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    aggregate=defaultdict(lambda:{"n":0,"lexical":0,"exact":0})
    with out.open("w",encoding="utf-8") as stream:
        for name,path in models.items():
            model,_=LanguageModel.load_checkpoint(path,device=device)
            model.eval()
            for case in cases:
                text=generate(model,tok,case["user"],a.max_new_tokens)
                values=score(case["topic"],case["mode"],text)
                result={"model":name,"topic":case["topic"],"mode":case["mode"],
                        "input":case["user"],"reference":case["assistant"],
                        "generated":text,**values}
                stream.write(json.dumps(result,ensure_ascii=False)+"\n")
                s=aggregate[(name,case["mode"])]
                s["n"]+=1;s["lexical"]+=int(values["lexical_topic"])
                s["exact"]+=int(values["topic_exact"])
                print(f'{name} {case["mode"]} {case["topic"]}: {text!r} lexical={values["lexical_topic"]}')
    for (name,mode),s in aggregate.items():
        print(f'{name}/{mode}: lexical={s["lexical"]}/{s["n"]} exact={s["exact"]}/{s["n"]}')
    print("Saved:",out)
if __name__=="__main__":main()
