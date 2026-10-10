"""v0.2.33.17: frozen-checkpoint out-of-distribution copy robustness.

This script never trains or overwrites a checkpoint.
"""
import argparse,json,datetime
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from input_output_copy_learning_v02339 import TESTS,prompt
from generalized_copy_learning_v023316 import split_corpus

PROBES={
 "unseen_vocabulary":[
   "銀色の望遠鏡を研究室に置きます。",
   "透明な容器を実験台に運びます。",
   "橙色の顕微鏡を廊下に移します。",
   "細長い温度計を作業室に入れます。",
   "丸い地球儀を教室に置きます。",
   "古い計算尺を引き出しにしまいます。",
   "新しい測定器を倉庫に運びます。",
   "大きな発電機を屋外に設置します。"],
 "unseen_syntax":[
   "机に赤い本があります。",
   "棚へ移したのは青い箱です。",
   "白い紙が封筒の中にあります。",
   "玄関にある緑の袋を取ってください。",
   "なぜ黒い本を机に置きましたか。",
   "箱が青い場合は、棚に運びます。",
   "ノートを机に置いたあと、傘を玄関に移します。",
   "まず赤い本を取り、次に白い紙を入れます。"],
 "longer_sentences":[
   "赤い本を机に置きます。青い箱を棚に運びます。白い紙を封筒に入れます。黄色い傘を玄関に移します。",
   "緑のノートを机に置きます。黒い冊子を棚に運びます。紫の袋をかごに入れます。",
   "赤い本を棚に移します。青い本を机に置きます。白い本を入口に運びます。",
   "黄色い箱を玄関に置きます。茶色い紙を窓際に移します。黒い傘を引き出しに入れます。"],
 "multiple_sentences":[
   "今日は雨です。明日は晴れです。",
   "CPUは命令を実行します。GPUは計算を処理します。",
   "まず準備します。次に確認します。最後に保存します。",
   "本を読みました。感想を書きました。"],
 "symbols_numbers":[
   "CPU-3070Tiは8GBです。",
   "温度は23.5℃、湿度は48%です。",
   "A/Bテストの結果は12/20でした。",
   "Python 3.13 + CUDA 12.4",
   "URL: https://example.org/a?x=1&y=2",
   "JSON: {\"ok\":true,\"count\":3}",
   "括弧（A）と記号［B］を確認します。",
   "ID=00123; X<Y; Z>=2"],
 "original_benchmark":[text for _,text in TESTS],
}
def validate_groups(groups):
    if not groups or any(not arr for arr in groups.values()):
        raise ValueError("All evaluation groups must have at least one item")
    seen=set()
    for name,arr in groups.items():
        for text in arr:
            if not isinstance(text,str) or not text:raise ValueError("Empty test text")
            if text in seen:raise ValueError(f"Duplicate test sentence: {text}")
            seen.add(text)
    return True

def eval_case(model,tok,source,max_new_tokens):
    input_ids=tok.encode(prompt(source),add_bos=True)
    target=tok.encode(source,add_eos=True)
    if len(input_ids)>=model.context_length:
        return {"source":source,"skipped":True,"reason":"prompt exceeds context",
                "prompt_tokens":len(input_ids),"target_tokens":len(target)}
    with torch.inference_mode():
        generated=model.generate(input_ids,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                                temperature=0,repetition_penalty=1.)
    tail=generated[len(input_ids):]
    decoded=tok.decode(tail).strip()
    prefix=0
    for a,b in zip(tail,target):
        if a!=b:break
        prefix+=1
    return {"source":source,"skipped":False,"prompt_tokens":len(input_ids),
            "target_tokens":len(target),"generated_tokens":len(tail),
            "tokenizer_roundtrip":tok.decode(tok.encode(source))==source,
            "exact_text":decoded==source,"exact_tokens":tail==target,
            "matched_prefix_tokens":prefix,
            "generated":decoded,"stopped_on_eos":bool(tail and tail[-1]==tok.eos_id)}

def summarize(results):
    checked=[r for r in results if not r["skipped"]]
    return {"evaluated":len(checked),"skipped":len(results)-len(checked),
            "exact_text":sum(r["exact_text"] for r in checked),
            "exact_tokens":sum(r["exact_tokens"] for r in checked),
            "roundtrip":sum(r["tokenizer_roundtrip"] for r in checked),
            "exact_accuracy":sum(r["exact_text"] for r in checked)/len(checked) if checked else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-general-copy-v023316.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=180)
    p.add_argument("--out",default="results/copy_ood_robustness_v023317.json")
    a=p.parse_args()
    if a.max_new_tokens<1:raise ValueError("Invalid maximum tokens")
    dest=Path(a.out)
    if dest.exists():raise FileExistsError(f"Refusing overwrite: {dest}")
    validate_groups(PROBES)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    model,ckpt=LanguageModel.load_checkpoint(a.model,dev)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer vocab mismatch")
    model.eval()
    # Sanity check on previously held-out in-grammar combinations. Never used
    # for re-selection; first 20 validation examples are fixed by the old seed.
    _,old_val,_=split_corpus(seed=42)
    groups={"in_grammar_control":old_val[:20],**PROBES}
    validate_groups(groups)
    reports={}
    for name,items in groups.items():
        data=[eval_case(model,tok,source,a.max_new_tokens) for source in items]
        stats=summarize(data)
        reports[name]={"summary":stats,"cases":data}
        print(f"{name}: {stats['exact_text']}/{stats['evaluated']} exact "
              f"({stats['skipped']} skipped), roundtrip={stats['roundtrip']}/{stats['evaluated']}")
        for d in data:
            if not d["skipped"] and not d["exact_text"]:
                print(" FAIL:",repr(d["source"]),"->",repr(d["generated"]))
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"version":"v0.2.33.17",
      "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "model":a.model,"checkpoint_epoch":ckpt.get("epoch"),
      "no_training":True,"no_model_selection":True,
      "limitations":["Small hand-crafted diagnostic groups rather than a population-representative benchmark",
        "Categories overlap linguistically; tests are grouped by main stressor only",
        "A successful in-grammar control does not prove arbitrary free-text copying",
        "NFKC tokenizer normalization may alter compatibility characters",
        "Original benchmark overlaps earlier developer-known evaluation cases",
        "Strict text matching uses decoded output with surrounding whitespace stripped"],
      "groups":reports},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",dest)
if __name__=="__main__":main()
