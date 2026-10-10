"""v0.2.33.19: frozen independent OOD transfer comparison.

Compare v0.2.33.16 and v0.2.33.18, with no further training.
Fixed fresh stress probes and previous OOD reference probes are reported
separately to avoid treating reused diagnostic probes as an independent test.
"""
import argparse,datetime,json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from evaluate_copy_ood_robustness_v023317 import PROBES,eval_case,summarize,validate_groups
from generalized_copy_learning_v023316 import split_corpus

FRESH={
    "new_lexicon":[
        "群青色の羅針盤を工房に置きました。",
        "金属製の振り子を実験室で動かします。",
        "透明な試験管を作業台から取り出しました。",
        "木製の模型を展示室に運びました。",
        "小型の気圧計を倉庫で点検します。",
        "大きな天体望遠鏡を屋上に設置しました。"],
    "new_syntax":[
        "机の上に置かれた本は、昨日購入したものです。",
        "本を机に置く前に、箱を棚から下ろしてください。",
        "棚に箱がなければ、机の下を確認してください。",
        "赤い本と青い箱のうち、どちらを先に運びますか。",
        "紙を封筒に入れたのは誰ですか。",
        "予定が変わったため、作業を中止することになりました。"],
    "long_context":[
        "最初に机の上の本を確認し、次に棚の箱を開き、内容物を一覧表へ書き込み、最後に確認者の署名を記録します。",
        "研究室で測定を開始します。機器を起動したあと、温度と湿度を確認します。値が安定したら、記録を保存してください。",
        "昨日は科学館を訪問しました。午前中は展示を見学しました。午後は実験教室に参加しました。帰宅後に感想をまとめました。"],
    "multi_sentence":[
        "雨が降り始めました。窓を閉めてください。",
        "計算が終わりました。結果を表にまとめます。",
        "資料を読みました。重要な部分に印を付けました。明日の会議で説明します。",
        "パソコンを起動しました。ネットワークが使えません。原因を調べます。"],
    "numeric_ascii":[
        "device=RTX3070Ti; memory=8GB; status=OK",
        "2026-10-10 14:36 JST",
        "v0.2.33.19 / accuracy=100.0%",
        "CPU:8; GPU:1; RAM:32GB",
        "file_name=report_001.json",
        "A1+B2=C3"],
    "unicode_fidelity":[
        "全角ＡＢＣ１２３と半角ABC123を区別します。",
        "①②③と123は同じではありません。",
        "記号：［確認］（終了）〈注意〉",
        "温度は２０℃、電圧は５Ｖです。"],
}

def build_groups():
    # Evaluation only. No group affects checkpoint selection.
    _,old_val,old_test=split_corpus(seed=42)
    groups={"in_grammar_control":old_test[:20],**FRESH}
    # Old OOD cases have already been exposed during development; keep separate.
    return groups,dict(PROBES)

def compare_models(models,tok,groups,budget):
    validate_groups(groups)
    output={}
    for group,examples in groups.items():
        output[group]={"cases":{}}
        for name,model in models.items():
            data=[eval_case(model,tok,s,budget) for s in examples]
            output[group]["cases"][name]=data
            output[group][name]=summarize(data)
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--baseline",default="model/model-llm-cha-general-copy-v023316.pt")
    parser.add_argument("--curriculum",default="model/model-llm-cha-copy-curriculum-v023318.pt")
    parser.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    parser.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    parser.add_argument("--max-new-tokens",type=int,default=180)
    parser.add_argument("--out",default="results/independent_ood_transfer_v023319.json")
    args=parser.parse_args()
    if args.max_new_tokens<=0:raise ValueError("Invalid max-new-tokens")
    out=Path(args.out)
    if out.exists():raise FileExistsError(f"Refusing overwrite: {out}")
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    tok=Tokenizer.load(args.tokenizer)
    models={}
    for name,path in (("baseline_v023316",args.baseline),("curriculum_v023318",args.curriculum)):
        model,_=LanguageModel.load_checkpoint(path,device)
        if model.vocab_size!=tok.vocab_size:raise ValueError("Tokenizer-model vocabulary mismatch")
        model.eval();models[name]=model
    fresh,reused=build_groups()
    validate_groups(fresh);validate_groups(reused)
    # Proactively reject accidental overlaps with reused developer-known tests.
    old={v for values in reused.values() for v in values}
    fresh_only={v for key,values in fresh.items() if key!="in_grammar_control" for v in values}
    if fresh_only&old:raise ValueError("Fresh OOD and reused OOD overlap")
    fresh_result=compare_models(models,tok,fresh,args.max_new_tokens)
    reused_result=compare_models(models,tok,reused,args.max_new_tokens)
    def print_results(tag,group_result):
        for group,d in group_result.items():
            b=d["baseline_v023316"];c=d["curriculum_v023318"]
            print(f"[{tag}] {group}: baseline={b['exact_text']}/{b['evaluated']}, curriculum={c['exact_text']}/{c['evaluated']}, "
                  f"roundtrip={c['roundtrip']}/{c['evaluated']}")
    print_results("fresh",fresh_result);print_results("reused",reused_result)
    report={"version":"v0.2.33.19","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "models":{"baseline_v023316":args.baseline,"curriculum_v023318":args.curriculum},
      "no_training":True,"no_checkpoint_selection":True,"evaluation_only":True,
      "fresh_groups":fresh_result,"reused_diagnostic_groups":reused_result,
      "limitations":["Fresh probes are manually authored and small, not a random representative test population",
                     "Previously used v0.2.33.17 questions are diagnostic references only",
                     "NFKC tokenizer normalization may prevent byte-exact Unicode copying",
                     "Cross-model comparison on fixed probes does not isolate curriculum effects from other confounds",
                     "EOS and exact generated token behavior are visible per case"]}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out)
if __name__=="__main__":main()
