"""Isolated v0.6.31 online GPU integration probe: no production state writes."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

from online_train import pair_fingerprint

def model_digest(path):
    checkpoint=torch.load(path,map_location="cpu",weights_only=False)
    state=checkpoint.get("model_state_dict")
    if state is None:
        state=checkpoint.get("state_dict")
    if state is None:
        return None
    h=hashlib.sha256()
    for name,tensor in sorted(state.items()):
        if torch.is_tensor(tensor):
            h.update(name.encode())
            h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def run_probe(base_model,tokenizer,trainer="online_train.py",output_report="results/gpu_online_integrity_v0631.json"):
    base_model=Path(base_model).resolve()
    tokenizer=Path(tokenizer).resolve()
    if not base_model.is_file() or not tokenizer.is_file():
        raise FileNotFoundError("Base model and tokenizer must exist")
    original_hash=hashlib.sha256(base_model.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="llm_cha_v0631_") as temp:
        root=Path(temp)
        pair=("v0631統合試験の合言葉は何ですか","検証専用の合言葉です。")
        chat=root/"training.jsonl"
        chat.write_text(json.dumps({"user":pair[0],"assistant":pair[1],
                                    "source":"chat-manual"},ensure_ascii=False)+"\n",encoding="utf-8")
        state=root/"training_state.json"
        output=root/"probe-model.pt"
        command=[sys.executable,str(Path(trainer).resolve()),
                 "--chat-data",str(chat),"--replay-data",str(root/"empty.txt"),
                 "--stability-data",str(root/"missing.jsonl"),
                 "--base-model",str(base_model),"--tokenizer",str(tokenizer),
                 "--output",str(output),"--state",str(state),
                 "--epochs","2","--batch-size","1","--tiny-threshold","10",
                 "--manual-weight","1","--recovery-stabilization-epochs","0"]
        first=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace")
        result={"first_returncode":first.returncode,
                "base_checkpoint_unchanged":hashlib.sha256(base_model.read_bytes()).hexdigest()==original_hash,
                "first_stdout_tail":first.stdout[-2500:],"first_stderr_tail":first.stderr[-2000:]}
        if first.returncode==0 and output.exists():
            ckpt=torch.load(output,map_location="cpu",weights_only=False)
            metadata=ckpt.get("metadata",{})
            fp=pair_fingerprint(*pair)
            counts=metadata.get("training_exposure_counts_v0630",{})
            result["pending_fingerprint_exposure"]=counts.get(fp,0)
            result["fingerprint_checkpoint_recorded"]=fp in metadata.get("trained_fingerprints",[])
            result["fingerprint_state_recorded"]=fp in json.loads(state.read_text(encoding="utf-8")).get("trained_fingerprints",[])
            result["model_weights_differ"]=model_digest(base_model)!=model_digest(output)
            next_command=list(command)
            next_command[next_command.index("--base-model")+1]=str(output)
            second=subprocess.run(next_command,capture_output=True,text=True,encoding="utf-8",errors="replace")
            result["second_returncode"]=second.returncode
            result["second_skipped"]=second.returncode==3 and "training skipped" in second.stdout
            result["pass"]=all((result["base_checkpoint_unchanged"],
                 result["pending_fingerprint_exposure"]>0,
                 result["fingerprint_checkpoint_recorded"],
                 result["fingerprint_state_recorded"],
                 result["model_weights_differ"],result["second_skipped"]))
        else:
            result["pass"]=False
    dest=Path(output_report)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base-model",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--trainer",default="online_train.py")
    p.add_argument("--report",default="results/gpu_online_integrity_v0631.json")
    a=p.parse_args()
    result=run_probe(a.base_model,a.tokenizer,a.trainer,a.report)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result["pass"] else 1)
if __name__=="__main__":main()
