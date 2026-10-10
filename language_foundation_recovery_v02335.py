"""v0.2.33.5 supervised Japanese foundation pilot, frozen held-out split.

Small authored data diagnose whether language capability can be learned,
not a claim of general Japanese proficiency. DSS, Memory, Bridge unchanged.
"""
import argparse,json,random,hashlib
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY

# Templates and topics by split are deliberately distinct.
TRAIN=[
("人: CPUとは何ですか？\nAI: ","CPUはプログラムの命令を実行する中央処理装置です。"),
("人: GPUとは何ですか？\nAI: ","GPUは画像処理や多くの計算を並列に実行するプロセッサーです。"),
("人: Pythonとは何ですか？\nAI: ","Pythonは読みやすい構文を持つプログラミング言語です。"),
("人: メモリとは何ですか？\nAI: ","メモリは計算中のデータや命令を一時的に保持する装置です。"),
("人: コンピュータの仕組みを簡単に教えてください。\nAI: ","コンピュータは入力された情報を命令に従って処理し、結果を出力します。"),
("人: 初めてPythonを学ぶ手順を教えてください。\nAI: ","まず基本構文を学び、次に短いコードを書き、最後に動作を確認します。"),
("人: プログラムを作る手順を教えてください。\nAI: ","まず目的を決め、次にコードを書き、最後に実行して確認します。"),
("人: エラーを調べる手順を教えてください。\nAI: ","まずエラーメッセージを読み、次に原因を調べ、最後に修正して再実行します。"),
("人: 私はPythonを学んでいます。\nAI: いいですね。\n人: その言語を使うには何をすればいいですか？\nAI: ","Pythonの基本構文を学び、小さなプログラムを動かしてみましょう。"),
("人: GPUの使い方を知りたいです。\nAI: 分かりました。\n人: それは何に使えますか？\nAI: ","GPUは画像処理や並列計算などに利用できます。"),
("人: まずCPUの役割を短く説明してください。\nAI: ","CPUは命令を実行する装置です。"),
("人: Pythonを学んでからアプリを開発したいです。\nAI: ","まずPythonの基本を学び、次に小さなアプリを作り、最後にテストしましょう。"),
("人: 次の文章を続けてください。\nAI: 今日は天気がよいので、","外に出て散歩することにしました。"),
("人: 次の文章を続けてください。\nAI: パソコンの電源を入れた後、","必要なソフトウェアを起動しました。"),
]
VALID=[
("人: ネットワークとは何ですか？\nAI: ","ネットワークは複数の機器を接続し、情報を交換する仕組みです。"),
("人: データベースとは何ですか？\nAI: ","データベースは情報を整理して保存し、検索できるようにする仕組みです。"),
("人: 文章を確認する手順を教えてください。\nAI: ","まず全文を読み、次に誤りを探し、最後に修正を確認します。"),
("人: この文章を続けてください。\nAI: 本を読み終えたので、","内容をノートにまとめました。"),
]
# Held-out evaluation prompts are not packaged as training or validation rows.
HOLDOUT=[
("説明","人: センサーとは何ですか？\nAI: "),
("説明","人: OSとは何ですか？\nAI: "),
("手順","人: 写真を整理する手順を教えてください。\nAI: "),
("手順","人: 初めて文章を書く手順を説明してください。\nAI: "),
("文脈","人: 私はデータベースを勉強しています。\nAI: いいですね。\n人: それは何に利用できますか？\nAI: "),
("条件","人: OSについて初心者向けに短く説明してください。\nAI: "),
("条件","人: センサーを学んでから小さな装置を作る計画を教えてください。\nAI: "),
("文章継続","人: この文章を続けてください。\nAI: 雨が降り始めたため、")
]
def rowset(data):
    return [{"id":hashlib.sha256((p+a).encode()).hexdigest()[:16],
             "prompt":p,"answer":a} for p,a in data]
def validate_splits():
    sets=[{p for p,_ in split} for split in (TRAIN,VALID)]
    hold={p for _,p in HOLDOUT}
    if sets[0]&sets[1] or sets[0]&hold or sets[1]&hold:
        raise ValueError("Prompts overlap splits")
    if len(hold)!=len(HOLDOUT):raise ValueError("Duplicate holdout")
    return True

def train(args):
    validate_splits()
    if Path(args.output).exists() or Path(args.report).exists():raise FileExistsError("Refusing overwrite")
    random.seed(args.seed);torch.manual_seed(args.seed)
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    tok=Tokenizer.load(args.tokenizer)
    model,_=LanguageModel.load_checkpoint(args.base,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Vocabulary mismatch")
    trainrows=[encode_row(tok,r,model.context_length) for r in rowset(TRAIN)]
    valrows=[encode_row(tok,r,model.context_length) for r in rowset(VALID)]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    groups=[{"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
            {"params":[model.lm_head.weight],"lr":args.head_lr}]
    opt=torch.optim.AdamW(groups,weight_decay=.01)
    trace=[];best=float("inf");best_state=None
    for epoch in range(args.epochs):
        model.train();indices=list(range(len(trainrows)));random.shuffle(indices)
        for i in indices:
            opt.zero_grad(set_to_none=True)
            loss=loss_rows(model,[trainrows[i]],device)+args.replay_weight*loss_rows(model,[replay[i%len(replay)]],device)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step()
        model.eval()
        with torch.no_grad():
            tr=float(loss_rows(model,trainrows,device).item())
            va=float(loss_rows(model,valrows,device).item())
        trace.append({"epoch":epoch+1,"train_nll":tr,"val_nll":va})
        print(f"epoch={epoch+1} train_nll={tr:.4f} val_nll={va:.4f}")
        if va<best:
            best=va
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(best_state)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(args.output,epoch=args.epochs,loss=best,
                          metadata={"experiment":"v0.2.33.5","train_rows":len(TRAIN),"validation_rows":len(VALID)})
    report={"train_examples":len(TRAIN),"validation_examples":len(VALID),"heldout_probes":len(HOLDOUT),
            "best_val_nll":best,"history":trace,"output":args.output,
            "note":"Very small authored teaching corpus; heldout examples not trained."}
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",args.output,args.report)

def evaluate(args):
    from dialogue_guided_generation_v02322 import CheckpointGenerator
    gens={"base":CheckpointGenerator(args.base,args.tokenizer,args.device),
          "foundation":CheckpointGenerator(args.output,args.tokenizer,args.device)}
    out=[]
    for ability,prompt in HOLDOUT:
        replies={name:g.generate(prompt,max_new_tokens=args.max_new_tokens,temperature=0)
                 for name,g in gens.items()}
        out.append({"ability":ability,"prompt":prompt,"outputs":replies,
                    "manual_review":{"base":None,"foundation":None}})
        print(ability,repr(prompt))
        for name,r in replies.items():print(" ",name,repr(r["text"]))
    dest=Path(args.evaluation)
    if dest.exists():raise FileExistsError(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"results":out,"promotion_eligible":False,
              "warning":"Small authored pilot. Manual quality review required before bridge retraining."},
              ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",dest)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("train","evaluate"))
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-language-foundation-v02335.pt")
    p.add_argument("--report",default="results/language_foundation_train_v02335.json")
    p.add_argument("--evaluation",default="results/language_foundation_eval_v02335.json")
    p.add_argument("--epochs",type=int,default=12)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--head-lr",type=float,default=1e-6)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    a=p.parse_args()
    if a.epochs<1 or a.lr<=0 or a.head_lr<=0 or a.replay_weight<0:
        raise ValueError("Invalid hyperparameters")
    (train if a.command=="train" else evaluate)(a)
if __name__=="__main__":main()
