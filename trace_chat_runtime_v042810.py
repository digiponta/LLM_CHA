"""v0.4.28.10 opt-in stage trace entrypoint for isolated benchmark only.

Invokes real chat.main; wraps generate_reply without modifying any decision.
"""
import json, os
from pathlib import Path
import chat

def main():
    path=os.environ.get("LLM_CHA_STAGE_TRACE")
    if not path:raise SystemExit("LLM_CHA_STAGE_TRACE must be explicitly set")
    destination=Path(path)
    if destination.exists():raise SystemExit("trace output already exists")
    original=chat.generate_reply
    counter=0
    def traced(*args,**kwargs):
        nonlocal counter
        result=original(*args,**kwargs)
        counter+=1
        record={"event":"GENERATION_CANDIDATE","ordinal":counter,
                "seed":kwargs.get("seed"),"temperature":kwargs.get("temperature"),
                "text":result.text,"token_count":result.token_count,
                "mean_confidence":result.mean_confidence,
                "min_confidence":result.min_confidence,
                "mean_top2_margin":result.mean_top2_margin}
        with destination.open("a",encoding="utf-8") as file:
            file.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+"\n")
        return result
    chat.generate_reply=traced
    chat.main()
if __name__=="__main__":main()
