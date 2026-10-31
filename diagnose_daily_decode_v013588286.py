"""Compare first answer-token probabilities and greedy / sampled generation on seen SFT prompts.

Read-only: loads checkpoints but does not train or write model files.
"""
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply,build_prompt
from online_train import load_chat_jsonl

PROBES=("おはよう","雑談しよう","相談がある")
@torch.no_grad()
def inspect_model(path,tokenizer,pairs,device,seed=42):
    model,_=LanguageModel.load_checkpoint(str(path),device=device)
    model.eval()
    by_question={q:a for q,a,_ in pairs}
    results=[]
    for question in PROBES:
        target=by_question[question]
        prompt,_=build_prompt([],question,0)
        prefix=tokenizer.encode(prompt,add_bos=True)
        answer_tokens=tokenizer.encode(target,add_bos=False)
        if not answer_tokens:raise ValueError("EMPTY_TARGET_TOKENS")
        first=answer_tokens[0]
        x=torch.tensor([prefix[-model.context_length:]],dtype=torch.long,device=device)
        probs=F.softmax(model(x)[0,-1,:],dim=-1)
        first_rank=int((probs>probs[first]).sum().item())+1
        greedy=generate_reply(model,tokenizer,prompt,64,0,20,1.0,seed=seed)
        sampled=generate_reply(model,tokenizer,prompt,64,0.45,20,1.0,seed=seed)
        results.append({"question":question,"reference":target,
                        "first_target_token_id":first,"first_target_probability":round(float(probs[first]),6),
                        "first_target_rank":first_rank,
                        "greedy":greedy.text,"sampled":sampled.text,
                        "greedy_token_count":greedy.token_count,
                        "sampled_token_count":sampled.token_count})
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    ap.add_argument("--candidate",default="model/daily-sft-candidate-v013588284.pt")
    ap.add_argument("--tokenizer",required=True)
    ap.add_argument("--train",default="data/daily_sft_train_v013588284.jsonl")
    ap.add_argument("--output",default="results/daily_decode_diagnostic_v013588286.json")
    a=ap.parse_args()
    for path in (a.base,a.candidate,a.tokenizer,a.train):
        if not Path(path).is_file():raise FileNotFoundError(path)
    pairs=load_chat_jsonl(Path(a.train))
    tokenizer=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    results={"status":"DECODE_DIAGNOSTIC","device":str(device),"temperature_greedy":0,
             "temperature_sampled":0.45,"seed":42,
             "base":inspect_model(a.base,tokenizer,pairs,device),
             "candidate":inspect_model(a.candidate,tokenizer,pairs,device),
             "model_changed":False}
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
