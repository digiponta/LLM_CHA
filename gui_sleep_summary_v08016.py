"""Summarize /sleep output for the GUI without claiming training succeeded."""
import re

def summarize_sleep_output(raw):
    text=raw or ""
    match=re.search(r"\[unapproved wiki sleep: status=([^,\]]+), eligible=(\d+), trained=(True|False), checkpoint=([^,\]]+)",text)
    if "[unapproved wiki sleep FAILED:" in text:
        return {"state":"FAILED","label":"未承認Wikipedia学習: 失敗"}
    if match:
        state,count,trained,checkpoint=match.groups()
        return {"state":state,"label":"未承認Wikipedia学習: {} / 対象{}件 / 実行{}".format(
            state,count,"あり" if trained=="True" else "なし"),
            "checkpoint":checkpoint}
    if "experimental sleep FAILED:" in text:
        return {"state":"SKIPPED","label":"未承認Wikipedia学習: 既存処理失敗のため未実行"}
    return {"state":"UNKNOWN","label":"未承認Wikipedia学習: 結果未確認"}
