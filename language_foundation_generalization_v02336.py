"""v0.2.33.6 topic/template transfer pilot.

Train with multiple meanings and response forms; reserve entirely new topics
and question templates. Tiny authored corpus, NOT evidence of broad fluency.
"""
import argparse,json,random,hashlib
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from prepare_purpose_sft_v02324 import REPLAY
from dialogue_guided_generation_v02322 import CheckpointGenerator

TRAIN_FACTS={
 "CPU":("プログラムの命令を実行する演算装置","処理を実行する","命令を読み取り計算する"),
 "GPU":("多数の計算を並列処理する演算装置","画像や並列計算を処理する","複数の計算を並行して進める"),
 "Python":("読みやすい構文を持つプログラミング言語","プログラムを書く","基本構文を使って処理を記述する"),
 "メモリ":("計算中のデータを一時的に保持する記憶装置","処理中の情報を保持する","必要なデータを高速に読み書きする"),
 "ネットワーク":("複数の機器を接続して情報を交換する仕組み","機器間で情報を送受信する","通信経路を通じてデータを伝える"),
 "データベース":("情報を整理して保存し検索する仕組み","情報を保存し検索する","データを構造化して管理する"),
 "センサー":("周囲の状態を測定し信号に変える装置","温度や光などを測る","物理量を検出して信号を出す"),
 "OS":("機器やアプリケーションの動作を管理する基本ソフトウェア","資源やプログラムを管理する","ハードウェアとアプリの処理を調整する"),
}
VALID_FACTS={
 "コンパイラ":("プログラムを別の実行形式に変換するソフトウェア","プログラムを変換する","ソースコードを読み取り変換する"),
 "ルーター":("ネットワーク間でデータの経路を選ぶ機器","通信の経路を選ぶ","宛先に応じてデータを転送する"),
}
HOLDOUT_TOPICS=("マイク","ブラウザ","電池")
HOLDOUT=[
 ("topic","人: マイクは何をする装置ですか？\nAI: "),
 ("topic","人: ブラウザの役割を教えてください。\nAI: "),
 ("topic","人: 電池を初心者に説明してください。\nAI: "),
 ("template","人: CPUの特徴を一文で言うと？\nAI: "),
 ("template","人: GPUの働きを例を添えて話してください。\nAI: "),
 ("procedure","人: 写真を整理する方法を順番に教えてください。\nAI: "),
 ("procedure","人: 掃除を始める手順を説明してください。\nAI: "),
 ("context","人: 私はPythonを学習しています。\nAI: 分かりました。\n人: それを使って何ができますか？\nAI: "),
 ("continuation","人: 次の文章を続けてください。\nAI: 夕方になったので、")
]
PROCEDURES_TRAIN=[
 ("コードを調べる","目的を確認する","コードを読む","結果を実行して確かめる"),
 ("文章を推敲する","文章を読む","分かりにくい箇所を直す","全文を読み直す"),
 ("料理を作る","材料をそろえる","手順に沿って調理する","完成を確認する"),
 ("旅行を計画する","目的地を決める","移動と宿泊を調べる","予定を見直す"),
 ("データを分析する","分析の目的を決める","データを整理する","結果を確認する"),
]
PROCEDURES_VALID=[("植物を育てる","育てる植物を選ぶ","水と日光の条件を整える","成長を観察する")]
def rows_for(facts,procedures):
    rows=[]
    for topic,(definition,role,mechanism) in facts.items():
        rows.extend([
           (f"人: {topic}とは何ですか？\nAI: ",f"{topic}は{definition}です。","definition",topic),
           (f"人: {topic}の役割を教えてください。\nAI: ",f"{topic}の役割は{role}ことです。","role",topic),
           (f"人: {topic}はどのように働きますか？\nAI: ",f"{topic}は{mechanism}仕組みで動作します。","mechanism",topic)])
    for topic,a,b,c in procedures:
        rows.extend([
           (f"人: {topic}手順を教えてください。\nAI: ",f"まず{a}。次に{b}。最後に{c}。","procedure",topic),
           (f"人: {topic}とき、何から始めますか？\nAI: ",f"最初に{a}。続いて{b}。終わったら{c}。","procedure",topic)])
    return [{"prompt":p,"answer":a,"skill":skill,"topic":topic,
             "id":hashlib.sha256((p+a).encode()).hexdigest()[:16]} for p,a,skill,topic in rows]

def splits():
    return rows_for(TRAIN_FACTS,PROCEDURES_TRAIN),rows_for(VALID_FACTS,PROCEDURES_VALID)

def validate():
    train,val=splits()
    groups=[{r["topic"] for r in rows if r["skill"]!="procedure"} for rows in (train,val)]
    if groups[0]&groups[1] or set(HOLDOUT_TOPICS)&(groups[0]|groups[1]):
        raise ValueError("Topic leakage")
    psets=[{r["prompt"] for r in rows} for rows in (train,val)]
    hold={p for _,p in HOLDOUT}
    if psets[0]&psets[1] or hold&set.union(*psets):
        raise ValueError("Exact prompt leakage")
    if len(psets[0])!=len(train) or len(psets[1])!=len(val) or len(hold)!=len(HOLDOUT):
        raise ValueError("Duplicated prompts")
    return True

def train(args):
    validate()
    if Path(args.output).exists() or Path(args.report).exists():raise FileExistsError("Refusing overwrite")
    random.seed(args.seed);torch.manual_seed(args.seed)
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    tokenizer=Tokenizer.load(args.tokenizer)
    model,_=LanguageModel.load_checkpoint(args.base,device)
    if model.vocab_size!=tokenizer.vocab_size:raise ValueError("Vocabulary mismatch")
    train_rows,val_rows=splits()
    train_pairs=[encode_row(tokenizer,r,model.context_length) for r in train_rows]
    val_pairs=[encode_row(tokenizer,r,model.context_length) for r in val_rows]
    replay=[encode_row(tokenizer,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    optimizer=torch.optim.AdamW([
      {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
      {"params":[model.lm_head.weight],"lr":args.head_lr}],weight_decay=.01)
    best=float("inf");state=None;trace=[];patience=0;best_epoch=0
    for epoch in range(args.epochs):
        model.train();order=list(range(len(train_pairs)));random.shuffle(order)
        for index in order:
            optimizer.zero_grad(set_to_none=True)
            task=loss_rows(model,[train_pairs[index]],device)
            loss=task+args.replay_weight*loss_rows(model,[replay[index%len(replay)]],device)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step()
        model.eval()
        with torch.inference_mode():
            tr=float(loss_rows(model,train_pairs,device).item())
            va=float(loss_rows(model,val_pairs,device).item())
        trace.append({"epoch":epoch+1,"train_nll":tr,"val_nll":va})
        print(f"epoch={epoch+1} train_nll={tr:.4f} val_nll={va:.4f}")
        if va<best-args.min_delta:
            best=va;best_epoch=epoch+1;patience=0
            state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else:
            patience+=1
            if patience>=args.patience:
                print("Early stopping:",epoch+1);break
    model.load_state_dict(state)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(args.output,epoch=best_epoch,loss=best,
       metadata={"version":"v0.2.33.6","train_rows":len(train_rows),"validation_rows":len(val_rows)})
    report={"train_rows":len(train_rows),"validation_rows":len(val_rows),
            "best_epoch":best_epoch,"best_val_nll":best,"history":trace,
            "caveat":"Template-defined responses; validation is topic-held-out but shares template families."}
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",args.output,args.report)

def evaluate(args):
    validate()
    gens={"base":CheckpointGenerator(args.base,args.tokenizer,args.device),
          "v02335":CheckpointGenerator(args.previous,args.tokenizer,args.device),
          "v02336":CheckpointGenerator(args.output,args.tokenizer,args.device)}
    result=[]
    for kind,prompt in HOLDOUT:
        outputs={name:g.generate(prompt,max_new_tokens=args.max_new_tokens,temperature=0)
                 for name,g in gens.items()}
        result.append({"kind":kind,"prompt":prompt,"outputs":outputs,"manual_review":None})
        print(f"[{kind}] {prompt!r}")
        for name,item in outputs.items():print(" ",name,repr(item["text"]))
    path=Path(args.evaluation)
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"results":result,"promotion_eligible":False,
      "warning":"Unseen topics but small human-designed and exposed evaluation set; no independent semantic quality certification."},
      ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("train","evaluate"))
    parser.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    parser.add_argument("--previous",default="model/model-llm-cha-language-foundation-v02335.pt")
    parser.add_argument("--output",default="model/model-llm-cha-language-generalization-v02336.pt")
    parser.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    parser.add_argument("--report",default="results/language_generalization_train_v02336.json")
    parser.add_argument("--evaluation",default="results/language_generalization_eval_v02336.json")
    parser.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    parser.add_argument("--epochs",type=int,default=20)
    parser.add_argument("--patience",type=int,default=4)
    parser.add_argument("--min-delta",type=float,default=.003)
    parser.add_argument("--lr",type=float,default=5e-6)
    parser.add_argument("--head-lr",type=float,default=1e-6)
    parser.add_argument("--replay-weight",type=float,default=.25)
    parser.add_argument("--max-new-tokens",type=int,default=80)
    parser.add_argument("--seed",type=int,default=42)
    a=parser.parse_args()
    if a.epochs<1 or a.patience<1 or min(a.lr,a.head_lr)<=0 or a.replay_weight<0 or a.min_delta<0:raise ValueError("Invalid options")
    (train if a.command=="train" else evaluate)(a)
if __name__=="__main__":main()
