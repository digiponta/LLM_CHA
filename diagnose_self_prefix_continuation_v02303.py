"""v0.2.30.3: Free-running self-prefix continuation diagnosis.

This experiment does NOT train or repair the model. For each prompt,
compare greedy continuation of a self-generated prefix with continuation
of a reference prefix, using identical prefix token budgets.
"""
import argparse,json,re
from collections import defaultdict
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from evaluate_topic_continuation_v02302 import metrics

def continuation_prompt(tok,prompt):
    return tok.encode("人: "+prompt+"\nAI: ",add_bos=True)

def split_prefix(tokens,k):
    if k<=0:raise ValueError("k must be positive")
    return tokens[:k],tokens[k:]

def analyze(topic,prefix_text,continuation_text,mode):
    full=prefix_text+continuation_text
    m=metrics(topic,full)
    continuation=metrics(topic,continuation_text)
    return {"topic":topic,"mode":mode,"prefix":prefix_text,
            "continuation":continuation_text,"full_answer":full,
            "full_topic_exact":m["topic_exact"],
            "full_topic_lexical":m["lexical_topic_coverage"],
            "continuation_topic_lexical":continuation["lexical_topic_coverage"],
            "full_two_sentences":m["two_plus_sentences"],
            "full_second_sentence_topic":m["lexical_topic_in_second_sentence"]}

@torch.no_grad()
def generation_pair(model,tok,question,reference,prefix_len,max_new_tokens):
    input_ids=continuation_prompt(tok,question)
    # Generate the first k answer tokens autonomously (no EOS sampling).
    generated=model.generate(input_ids,max_new_tokens=prefix_len,eos_id=None,
                             temperature=0.0,repetition_penalty=1.15)
    self_prefix=generated[len(input_ids):]
    gold=tok.encode(reference,add_eos=False)
    gold_prefix,_=split_prefix(gold,prefix_len)
    results=[]
    for mode,forced in (("self_prefix",self_prefix),("reference_prefix",gold_prefix)):
        model_input=input_ids+forced
        output=model.generate(model_input,max_new_tokens=max_new_tokens,
                              eos_id=tok.eos_id,temperature=0.0,
                              repetition_penalty=1.15)
        suffix=output[len(model_input):]
        prefix_text=tok.decode(forced,skip_special_tokens=True)
        suffix_text=tok.decode(suffix,skip_special_tokens=True)
        result=analyze(question["topic"],prefix_text,suffix_text,mode)
        result.update({"prefix_tokens":len(forced),"suffix_tokens":len(suffix)})
        results.append(result)
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",default="data/topic_grounded_v02290/eval.jsonl")
    p.add_argument("--model",action="append",help="NAME=CHECKPOINT, repeatable")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--prefix-tokens",type=int,default=8)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--out",default="results/self_prefix_continuation_v02303.jsonl")
    a=p.parse_args()
    if a.prefix_tokens<1 or a.max_new_tokens<1:p.error("positive token counts required")
    models={"prefix":"model/model-llm-cha-topic-prefix-v02301.pt",
            "continuation":"model/model-llm-cha-topic-continuation-v02302.pt"}
    if a.model:
        models={}
        for spec in a.model:
            name,sep,filepath=spec.partition("=")
            if not sep or not name or not filepath:p.error("expected NAME=CHECKPOINT")
            models[name]=filepath
    path=Path(a.fixture)
    if not path.is_file():p.error("run prepare_topic_grounded_v02290.py first")
    cases=[json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    stats=defaultdict(lambda:{"n":0,"topic":0,"second":0})
    with out.open("w",encoding="utf-8") as fp:
        for name,checkpoint in models.items():
            model,_=LanguageModel.load_checkpoint(checkpoint,device=device)
            model.eval()
            for case in cases:
                question={"topic":case["topic"],"prompt":case["prompt"]}
                # For the reference-prefix condition only, the gold answer is
                # used to provide the first k tokens, never as generated output.
                input_ids=continuation_prompt(tok,case["prompt"])
                first=model.generate(input_ids,max_new_tokens=a.prefix_tokens,
                                     eos_id=None,temperature=0.0,repetition_penalty=1.15)
                self_prefix=first[len(input_ids):]
                ref_prefix=tok.encode(case["reference"],add_bos=False)[:a.prefix_tokens]
                for mode,forced in (("self_prefix",self_prefix),("reference_prefix",ref_prefix)):
                    full_input=input_ids+forced
                    final=model.generate(full_input,max_new_tokens=a.max_new_tokens,
                                         eos_id=tok.eos_id,temperature=0.0,
                                         repetition_penalty=1.15)
                    generated=final[len(full_input):]
                    prefix_text=tok.decode(forced,skip_special_tokens=True)
                    suffix_text=tok.decode(generated,skip_special_tokens=True)
                    row=analyze(case["topic"],prefix_text,suffix_text,mode)
                    row.update({"model":name,"split":case["split"],"prompt":case["prompt"],
                                "prefix_tokens":len(forced),"suffix_tokens":len(generated)})
                    fp.write(json.dumps(row,ensure_ascii=False)+"\n")
                    key=(name,case["split"],mode)
                    stats[key]["n"]+=1
                    stats[key]["topic"]+=int(row["continuation_topic_lexical"])
                    stats[key]["second"]+=int(row["full_second_sentence_topic"])
                    print(f'{name:12} {case["split"]:7} {mode:16} {case["topic"]:9} '
                          f'suffix-topic={row["continuation_topic_lexical"]} | '
                          f'{suffix_text!r}')
    for (name,split,mode),s in stats.items():
        print(f'{name}/{split}/{mode}: suffix-topic={s["topic"]}/{s["n"]}, '
              f'second-sentence-topic={s["second"]}/{s["n"]}')
    print("Saved:",out)
if __name__=="__main__":main()
