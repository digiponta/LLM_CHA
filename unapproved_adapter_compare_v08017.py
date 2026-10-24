"""v0.8.0.17: compare frozen base and isolated unapproved Wikipedia adapter.

Diagnostic generation only. Outputs remain unverified and are never added
to trusted conversation history or Semantic Memory.
"""
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel, frozen_digest
from unapproved_wiki_sleep_v08015 import sleep_unapproved_wikipedia

def greedy(model,tokenizer,prompt,device,max_new_tokens=64,route=None):
    ids=tokenizer.encode(prompt,add_bos=True)
    if not ids:raise ValueError("empty prompt tokens")
    context=model.base.context_length if route else model.context_length
    eos=tokenizer.eos_id
    generated=[]
    with torch.inference_mode():
        for _ in range(max_new_tokens):
            x=torch.tensor([ids[-context:]],dtype=torch.long,device=device)
            logits=model(x,route=route) if route else model(x)
            nxt=int(logits[0,-1].argmax().item())
            if nxt==eos:break
            ids.append(nxt)
            generated.append(nxt)
    return tokenizer.decode(generated).strip()

def compare(question,base_path,tokenizer_path,adapter_path,max_new_tokens=64):
    if not question.strip():return {"status":"INVALID_QUESTION"}
    if not 1<=max_new_tokens<=256:raise ValueError("invalid token limit")
    base_path=Path(base_path)
    adapter_path=Path(adapter_path)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    ck=torch.load(adapter_path,map_location="cpu",weights_only=True)
    if (ck.get("route")!="unapproved_wikipedia" or ck.get("approved") is not False
        or ck.get("trusted_deployable") is not False):
        raise ValueError("not a safe unapproved Wikipedia adapter")
    if ck.get("base_hash")!=frozen_digest(base):raise ValueError("base hash mismatch")
    model=DualAdapterModel(base,rank=int(ck["rank"])).to(device)
    model.experimental.load_state_dict(ck["adapter"],strict=True)
    model.eval()
    prefix=question.strip()
    # Match the prompt format used by ConversationDataset during /sleep.\n    prompt=prefix
    plain=greedy(base,tokenizer,prompt,device,max_new_tokens)
    adapted=greedy(model,tokenizer,prompt,device,max_new_tokens,route="experimental")
    return {"status":"COMPARED","question":prefix,
       "base_response":plain,"unapproved_adapter_response":adapted,
       "candidate_count":len(ck.get("candidate_ids",[])),
       "adapter_checkpoint":str(adapter_path),
       "truth_state":"EXTERNAL_UNVERIFIED","generation_verified":False,
       "auto_promote":False,"train_ready":False,
       "note":"Raw model generations; correctness is not implied."}
