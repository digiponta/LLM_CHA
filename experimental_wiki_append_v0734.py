"""Append clearly attributed Wikipedia context only to unapproved Experimental answers.

External Wikipedia text is not verified, approved, or training-ready.
Never replace the model/candidate answer; fail closed on missing evidence.
"""
import re
from wiki_lead_v0736 import wiki_lead

def term_from_question(question):
    if not isinstance(question,str):return None
    term=question.strip()
    term=re.sub(r"^(?:教えて|説明して)[:：\s]*","",term)
    term=re.sub(r"(?:とは(?:何|なに)?(?:ですか)?|について(?:教えて|説明して)?(?:ください)?|って(?:何|なに)?|は(?:何|なに)?(?:ですか)?)\s*[？?。！!]*$","",term)
    term=term.strip(" \t\n　?？。")
    if not term or len(term)>60:return None
    return term

def append_wikipedia(answer,question,*,lookup):
    if not isinstance(answer,str) or not answer.strip():
        return {"answer":answer,"wiki_status":"SKIPPED"}
    term=term_from_question(question)
    if not term:return {"answer":answer,"wiki_status":"INVALID_TERM"}
    try:
        wiki=lookup(term)
    except (OSError,ValueError,TypeError,KeyError,TimeoutError) as exc:
        return {"answer":answer,"wiki_status":"LOOKUP_FAILED","error":type(exc).__name__}
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"answer":answer,"wiki_status":wiki.get("status","INVALID") if isinstance(wiki,dict) else "INVALID"}
    url=wiki.get("url","")
    title=wiki.get("title","")
    extract=wiki.get("extract","")
    if not (isinstance(url,str) and url.startswith("https://ja.wikipedia.org/wiki/")
            and isinstance(title,str) and title.strip() and isinstance(extract,str) and extract.strip()):
        return {"answer":answer,"wiki_status":"INVALID_EVIDENCE"}
    summary=wiki_lead(extract)
    if not summary:return {"answer":answer,"wiki_status":"EMPTY_EXTRACT"}
    appended=(answer+"\n【Wikipedia検索結果・外部情報・未検証】"
              +title+"："+summary+"\n出典："+url)
    return {"answer":appended,"wiki_status":"APPENDED","wiki_source":url,
            "truth_state":"EXTERNAL_UNVERIFIED","verified":False,
            "train_ready":False,"auto_promote":False}
