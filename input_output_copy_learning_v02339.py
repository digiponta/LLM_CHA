"""v0.2.33.9: copy learning pilot with strict synthetic split.

Does not modify DSS, Semantic Memory, Bridge or existing checkpoints.
Copying is an input-output skill, not proof of semantic understanding.
"""
import argparse,json,random,hashlib
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY
from dialogue_guided_generation_v02322 import CheckpointGenerator

# Held-out complete strings and novel pairs, not permutations of train targets.
TRAIN_TEXTS=[
 "赤い本を机に置きます。","青い箱を棚に運びます。","白い紙を封筒に入れます。",
 "小さな犬が庭を走ります。","黒い猫が窓から外を見ます。","黄色い花が風に揺れます。",
 "今日は駅まで歩きました。","明日は図書館へ行きます。","昨日は公園で休みました。",
 "CPUは命令を実行します。","GPUは計算を並列に処理します。","Pythonはプログラミング言語です。",
 "温度を測って記録します。","光の強さを調べます。","電源を切って確認します。",
 "まず道具を準備します。次に部品を調べます。","まず文章を読みます。次に誤字を直します。",
 "朝はお茶を飲みました。","昼は音楽を聞きました。","夜は本を読みました。",
]
VAL_TEXTS=[
 "緑の袋を玄関に置きます。","茶色い鳥が木の上で鳴きます。",
 "来週は美術館を訪ねます。","湿度を測って表にまとめます。",
 "まず写真を集めます。次に日付で分類します。",
]
TESTS=[
 ("unseen","紫の傘を入口に置きました。"),
 ("unseen","金色の魚が水槽を泳いでいます。"),
 ("unseen","来月は科学館で展示を見ます。"),
 ("novel_combination","青い猫が棚の上で休みました。"),
 ("novel_combination","昨日はPythonの本を読みました。"),
 ("novel_combination","GPUの温度を記録します。"),
 ("length","まず資料を集めます。次に内容を分類します。最後に結果を保存します。"),
 ("length","機器の電源を確認し、表示を読み取り、異常がある場合は作業を中断して担当者に知らせます。"),
]
PROMPT_PREFIX="人: 次の文章を一字一句そのまま出力してください。説明は不要です。\n文章: "
PROMPT_SUFFIX="\nAI: "
def prompt(text):return PROMPT_PREFIX+text+PROMPT_SUFFIX
def rows(texts):
    return [{"id":hashlib.sha256(s.encode()).hexdigest()[:16],
             "prompt":prompt(s),"answer":s} for s in texts]
def validate_splits():
    tr=set(TRAIN_TEXTS);va=set(VAL_TEXTS);te={s for _,s in TESTS}
    if len(tr)!=len(TRAIN_TEXTS) or len(va)!=len(VAL_TEXTS) or len(te)!=len(TESTS):
        raise ValueError("Duplicate copy targets")
    if tr&va or tr&te or va&te:raise ValueError("Copy target leakage")
    return True
def train(a):
    validate_splits()
    if Path(a.output).exists() or Path(a.report).exists():raise FileExistsError("Output already exists")
    random.seed(a.seed);torch.manual_seed(a.seed)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer);model,_=LanguageModel.load_checkpoint(a.base,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Vocabulary mismatch")
    tr=[encode_row(tok,r,model.context_length) for r in rows(TRAIN_TEXTS)]
    va=[encode_row(tok,r,model.context_length) for r in rows(VAL_TEXTS)]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    opt=torch.optim.AdamW([{"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":a.lr},
       {"params":[model.lm_head.weight],"lr":a.head_lr}],weight_decay=.01)
    best=float("inf");state=None;epoch_best=None;wait=0;history=[]
    for epoch in range(1,a.epochs+1):
        model.train();order=list(range(len(tr)));random.shuffle(order)
        for i in order:
            opt.zero_grad(set_to_none=True)
            loss=loss_rows(model,[tr[i]],device)
            if replay and a.replay_weight:loss=loss+a.replay_weight*loss_rows(model,[random.choice(replay)],device)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
        model.eval()
        with torch.inference_mode():
            tl=float(loss_rows(model,tr,device));vl=float(loss_rows(model,va,device))
        history.append({"epoch":epoch,"train_nll":tl,"val_nll":vl})
        print(f"epoch={epoch} train_nll={tl:.4f} val_nll={vl:.4f}")
        if vl<best-a.min_delta:
            best=vl;state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};epoch_best=epoch;wait=0
        else:
            wait+=1
            if wait>=a.patience:
                print("Early stopping:",epoch);break
    model.load_state_dict(state)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(a.output,epoch=epoch_best,loss=best,
         metadata={"version":"v0.2.33.9","task":"copy","train_items":len(tr),"validation_items":len(va)})
    path=Path(a.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"best_epoch":epoch_best,"best_val_nll":best,"history":history,
       "train_items":len(tr),"validation_items":len(va)},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",a.output,a.report)
def evaluate(a):
    validate_splits()
    if Path(a.evaluation).exists():raise FileExistsError("Evaluation already exists")
    gens={"base":CheckpointGenerator(a.base,a.tokenizer,a.device),
          "copy":CheckpointGenerator(a.output,a.tokenizer,a.device)}
    result=[]
    cases=[("seen",s) for s in TRAIN_TEXTS[:4]]+TESTS
    for kind,s in cases:
        out={}
        for name,g in gens.items():
            response=g.generate(prompt(s),max_new_tokens=a.max_new_tokens,temperature=0)
            out[name]={**response,"exact_match":response["text"]==s}
        result.append({"kind":kind,"input":s,"prompt":prompt(s),"outputs":out})
        print(f"[{kind}] input={s!r}")
        for name,r in out.items():print(" ",name,repr(r["text"]),"exact=",r["exact_match"])
    path=Path(a.evaluation);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"results":result,"training_performed":False,"promotion_eligible":False,
       "warning":"Small manually authored copy dataset. Exact match is literal copy fidelity, not meaning."},
       ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",path)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("train","evaluate"))
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--output",default="model/model-llm-cha-copy-v02339.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--report",default="results/copy_learning_train_v02339.json")
    p.add_argument("--evaluation",default="results/copy_learning_eval_v02339.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--epochs",type=int,default=25)
    p.add_argument("--patience",type=int,default=5)
    p.add_argument("--min-delta",type=float,default=.003)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--head-lr",type=float,default=1e-6)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--max-new-tokens",type=int,default=100)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.epochs<1 or a.patience<1 or min(a.lr,a.head_lr)<=0 or a.replay_weight<0 or a.min_delta<0 or a.max_new_tokens<1:
        raise ValueError("Invalid options")
    (train if a.command=="train" else evaluate)(a)
if __name__=="__main__":main()
