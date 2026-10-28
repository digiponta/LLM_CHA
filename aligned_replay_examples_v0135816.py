"""v0.13.58.16 canonical replay samples and assistant-only masking.

For an approved dialogue serialized as '人: ...\nAI: ...', only assistant
continuation and EOS contribute to loss. Literature remains full LM loss.
The prompt is tokenized separately to match inference's prompt prefix.
"""
from dialogue_format_v0135817 import split_dialogue, ANSWER_SEPARATOR
import torch
from torch.utils.data import TensorDataset

def make_aligned_examples(mixed,tokenizer,context_length,assistant_only=True):
    if context_length<2:raise ValueError("context too short")
    xs=[];ys=[];masks=[]
    for domain,line in mixed:
        if domain=="literature":
            full=tokenizer.encode(line,add_bos=True,add_eos=True)
            start_of_answer=1
        else:
            prompt,answer=split_dialogue(line)
            prefix=tokenizer.encode(prompt,add_bos=True)
            continuation=tokenizer.encode(answer,add_bos=False,add_eos=True)
            full=prefix+continuation
            start_of_answer=len(prefix)
        if len(full)<2:continue
        # If a single sequence spans blocks, each block contains a
        # one-token overlap so targets remain contiguous.
        for begin in range(0,len(full)-1,context_length):
            section=full[begin:begin+context_length+1]
            if len(section)<2:continue
            x=section[:-1];y=section[1:]
            valid=[]
            for j in range(len(y)):
                global_target=begin+j+1
                valid.append(float(domain=="literature" or not assistant_only or global_target>=start_of_answer))
            if sum(valid)==0:continue
            n=len(x)
            xs.append(x+[tokenizer.pad_id]*(context_length-n))
            ys.append(y+[tokenizer.pad_id]*(context_length-n))
            masks.append(valid+[0.]*(context_length-n))
    if not xs:raise ValueError("no supervised tokens in sampled records")
    return TensorDataset(torch.tensor(xs,dtype=torch.long),torch.tensor(ys,dtype=torch.long),
                         torch.tensor(masks,dtype=torch.float32))
