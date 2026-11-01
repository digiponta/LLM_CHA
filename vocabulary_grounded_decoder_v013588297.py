"""Audit generated replies against corpus-observed lexical forms.

Does not block generation yet; avoids false claims that corpus vocabulary covers
all Japanese inflections, proper nouns or legitimate unknown words.
"""
import argparse,json,re
from pathlib import Path

def audit(text,known,tokenizer,exempt=()):
    tokens=[m.surface() for m in tokenizer.tokenize(text) if m.surface().strip()]
    exempt=set(exempt)
    lexical=[t for t in tokens if re.search(r"[^\W_]",t,re.UNICODE)]
    unknown=[t for t in lexical if t not in known and t not in exempt]
    return {"status":"REVIEW" if unknown else "IN_VOCABULARY",
            "token_count":len(lexical),"unknown_count":len(unknown),
            "unknown_terms":unknown,"candidate_is_factually_correct":None,
            "candidate_is_semantically_relevant":None}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--vocab",default="results/real_persona_vocab_v013588297.json")
    p.add_argument("--text",required=True)
    p.add_argument("--allow",action="append",default=[],help="Known domain expression to exempt, e.g. スファレライト")
    a=p.parse_args()
    from sudachipy import dictionary
    vocab=json.loads(Path(a.vocab).read_text(encoding="utf-8-sig"))["counts"]
    result=audit(a.text,vocab,dictionary.Dictionary().create(),a.allow)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
