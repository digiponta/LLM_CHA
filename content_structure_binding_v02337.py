"""v0.2.33.7 Content-Structure Binding pilot.

Fact and format conditioned instruction SFT. Distinguishes supplied knowledge
from latent world knowledge using unseen combinations and negative controls.
"""
import argparse,json,random,hashlib
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY
from dialogue_guided_generation_v02322 import CheckpointGenerator

FACTS={
 "CPU":"CPUはプログラムの命令を実行する演算装置です。",
 "GPU":"GPUは多数の計算を並列に処理する演算装置です。",
 "センサー":"センサーは温度や光などを検出して信号に変換する装置です。",
 "マイク":"マイクは音を検出して電気信号に変換する装置です。",
 "ブラウザ":"ブラウザはWebページを表示するソフトウェアです。",
 "電池":"電池は化学エネルギーを電気エネルギーに変換する装置です。",
}
STEPS={
 "写真整理":("写真を集める","日付ごとに分類する","不要な写真を確認する"),
 "掃除":("掃除する場所を決める","道具を用意して掃除する","片付けを確認する"),
 "文章作成":("書く目的を決める","構成に沿って文章を書く","読み直して修正する"),
 "機器点検":("点検項目を整理する","順番に動作を確かめる","結果を記録する"),
}
# Disjoint *items* by split; same formatting task learned across items.
TRAIN_ITEMS={"definition":["CPU","GPU","センサー"],"procedure":["写真整理","文章作成"]}
VAL_ITEMS={"definition":["マイク"],"procedure":["掃除"]}
TEST_ITEMS={"definition":["ブラウザ","電池"],"procedure":["機器点検"]}
FORMATS=("definition","procedure")

def request(kind,topic,facts=None):
    if facts is None:return f"人: {topic}について説明してください。\nAI: " if kind=="definition" else f"人: {topic}の手順を教えてください。\nAI: "
    structure="定義を一文で" if kind=="definition" else "まず、次に、最後にの順で"
    return f"内容: {facts}\n文章形式: {structure}\n人: {topic}について答えてください。\nAI: "

def known_info(kind,topic):
    if kind=="definition":return FACTS[topic]
    a,b,c=STEPS[topic]
    return f"開始={a}; 実施={b}; 確認={c}"

def response(kind,topic):
    if kind=="definition":return FACTS[topic]
    a,b,c=STEPS[topic]
    return f"まず{a}。次に{b}。最後に{c}。"

def construct(items):
    rows=[]
    for kind,topics in items.items():
        for topic in topics:
            # The same answer is supervised with and without external knowledge.
            # Test prompts never appear in these training pairs.
            for grounded in (False,True):
                p=request(kind,topic,known_info(kind,topic) if grounded else None)
                a=response(kind,topic)
                rows.append({"id":hashlib.sha256((p+a).encode()).hexdigest()[:16],
                             "prompt":p,"answer":a,"kind":kind,"topic":topic,"grounded":grounded})
    return rows

def validate():
    for kind in FORMATS:
        sets=[set(d[kind]) for d in (TRAIN_ITEMS,VAL_ITEMS,TEST_ITEMS)]
        if sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2]:
            raise ValueError("Topic leakage")
    train,val,test=(construct(d) for d in (TRAIN_ITEMS,VAL_ITEMS,TEST_ITEMS))
    prompts=[r["prompt"] for r in train+val+test]
    if len(prompts)!=len(set(prompts)):raise ValueError("Prompt leakage")
    return True

def train(args):
    validate()
    if Path(args.output).exists() or Path(args.report).exists():raise FileExistsError("Output exists")
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    random.seed(args.seed);torch.manual_seed(args.seed)
    tok=Tokenizer.load(args.tokenizer)
    model,_=LanguageModel.load_checkpoint(args.base,device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("Vocabulary mismatch")
    trainrows=construct(TRAIN_ITEMS);valrows=construct(VAL_ITEMS)
    tr=[encode_row(tok,r,model.context_length) for r in trainrows]
    va=[encode_row(tok,r,model.context_length) for r in valrows]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    opt=torch.optim.AdamW([
       {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
       {"params":[model.lm_head.weight],"lr":args.head_lr}],weight_decay=.01)
    best=float("inf");state=None;best_epoch=0;waiting=0;history=[]
    for epoch in range(args.epochs):
        model.train();order=list(range(len(tr)));random.shuffle(order)
        for i in order:
            opt.zero_grad(set_to_none=True)
            loss=loss_rows(model,[tr[i]],device)+args.replay_weight*loss_rows(model,[replay[i%len(replay)]],device)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step()
        model.eval()
        with torch.inference_mode():
            train_nll=float(loss_rows(model,tr,device));val_nll=float(loss_rows(model,va,device))
        history.append({"epoch":epoch+1,"train_nll":train_nll,"val_nll":val_nll})
        print(f"epoch={epoch+1} train_nll={train_nll:.4f} val_nll={val_nll:.4f}")
        if val_nll<best-args.min_delta:
            best=val_nll;best_epoch=epoch+1;waiting=0
            state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else:
            waiting+=1
            if waiting>=args.patience:
                print("Early stopping",epoch+1);break
    model.load_state_dict(state)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(args.output,epoch=best_epoch,loss=best,
        metadata={"version":"v0.2.33.7","trained_examples":len(tr),"validation_examples":len(va)})
    result={"best_epoch":best_epoch,"best_val_nll":best,"history":history,"train_rows":len(tr),"val_rows":len(va)}
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",args.output,args.report)

def evaluate(args):
    validate()
    models={
      "base":CheckpointGenerator(args.base,args.tokenizer,args.device),
      "binding":CheckpointGenerator(args.output,args.tokenizer,args.device)}
    results=[]
    for row in construct(TEST_ITEMS):
        outputs={name:g.generate(row["prompt"],max_new_tokens=args.max_new_tokens,temperature=0)
                 for name,g in models.items()}
        results.append({"id":row["id"],"kind":row["kind"],"topic":row["topic"],
                        "grounded":row["grounded"],"prompt":row["prompt"],
                        "expected":row["answer"],"outputs":outputs,"manual_review":None})
        print(f"[{row['kind']} {row['topic']} grounded={row['grounded']}]")
        for name,v in outputs.items():print(" ",name,repr(v["text"]))
    p=Path(args.evaluation)
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({"results":results,"promotion_eligible":False,
        "note":"Exploratory test, manually review correctness; conditioned outputs use externally provided facts."},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",p)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("train","evaluate"))
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--output",default="model/model-llm-cha-content-structure-v02337.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--report",default="results/content_structure_train_v02337.json")
    p.add_argument("--evaluation",default="results/content_structure_eval_v02337.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--epochs",type=int,default=25)
    p.add_argument("--patience",type=int,default=5)
    p.add_argument("--min-delta",type=float,default=.003)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--head-lr",type=float,default=1e-6)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.epochs<1 or a.patience<1 or min(a.lr,a.head_lr)<=0 or a.min_delta<0 or a.replay_weight<0:raise ValueError("Invalid options")
    (train if a.command=="train" else evaluate)(a)
if __name__=="__main__":main()
