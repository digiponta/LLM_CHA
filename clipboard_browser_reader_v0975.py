"""User-initiated clipboard read-only context for LLM_CHA.

Copy content in your browser manually (Ctrl+A, Ctrl+C), then call this
reader. No browser automation, Google scraping, or automatic training.
"""
import hashlib
import json
import tkinter

MAX_CHARS=12000
def read_clipboard(getter=None):
    if getter is None:
        root=tkinter.Tk()
        root.withdraw()
        try:
            content=root.clipboard_get()
        finally:
            root.destroy()
    else:
        content=getter()
    if not isinstance(content,str) or not content.strip():
        raise ValueError("Clipboard has no text; select page and press Ctrl+A, Ctrl+C")
    text=content[:MAX_CHARS]
    return {"route":"CLIPBOARD_CONTEXT_READ",
            "text":text,"characters":len(text),
            "truncated":len(content)>MAX_CHARS,
            "content_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "source_url":None,"source_verified":False,
            "state":"EXTERNAL_UNVERIFIED","train_ready":False,
            "auto_promote":False,"persisted":False}

def main():
    result=read_clipboard()
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
