"""Compare corpus vs deterministic generated generic fraction using v0.2.14 outputs."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from diagnose_tokenizer_distribution_v0215 import analyze,read_rows
from tokenizer_bpe import Tokenizer
from conversation_diagnostics_v026 import classify_quality

def compare(generation,source,tok):
    gold=read_rows(source)
    by_prompt={r["user"]:r["assistant"] for r in gold if "user" in r and "assistant" in r}
    result={}
    for model,entry in generation.items():
        samples=entry["samples"]
        matched=[{"user":r["prompt"],"assistant":by_prompt[r["prompt"]]} for r in samples if r["prompt"] in by_prompt]
        if len(matched)!=len(samples):raise ValueError("Mismatch between generation and reference dataset")
        reference=analyze(matched,tok)
        generated=[{"user":r["prompt"],"assistant":r["generated"]} for r in samples]
        pred=analyze(generated,tok)
        result[model]={"samples":len(samples),"reference_generic_fraction":reference["generic_fraction"],
          "generated_generic_fraction":pred["generic_fraction"],
          "generic_amplification_pp":round(100*(pred["generic_fraction"]-reference["generic_fraction"]),3),
          "reference_chars_per_token":reference["chars_per_token"],
          "generated_chars_per_token":pred["chars_per_token"],
          "reference_short_fraction":reference["short_under_8_chars_fraction"],
          "generated_short_fraction":pred["short_under_8_chars_fraction"]}
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--generations",default="results/generation_v0214.json")
    p.add_argument("--references",default="data/dialogue_generalization_v0212/test.jsonl")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/generic_amplification_v0215.json")
    a=p.parse_args()
    tok=Tokenizer.load(a.tokenizer)
    result=compare(json.loads(Path(a.generations).read_text(encoding="utf-8")),a.references,tok)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
