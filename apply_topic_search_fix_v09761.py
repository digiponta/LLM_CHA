"""Apply v0.9.7.61 search-topic and causal fallback fix to chat.py.

Run once in repository root: python apply_topic_search_fix_v09761.py
"""
from pathlib import Path

p = Path(__file__).with_name("chat.py")
s = p.read_text(encoding="utf-8-sig")

fixes = [
    (
        "        if google_term is not None:\n            google_result = launch(google_term)",
        "        if google_term is not None:\n"
        "            # Keep the searched subject available to elliptical follow-ups.\n"
        "            topic_context.active_topic = google_term\n"
        "            topic_context.topics.setdefault(google_term, {\"attribute\": None, \"status\": \"SOURCE_NEEDED\"})\n"
        "            google_result = launch(google_term)",
    ),
    (
        "            if causal_reply is not None:\n"
        "                print(\"AI> \" + causal_reply)\n"
        "                print(\"[route=CLIPBOARD_CAUSAL_EVIDENCE, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]\")\n"
        "                print()\n"
        "                continue",
        "            if causal_reply is not None:\n"
        "                print(\"AI> \" + causal_reply)\n"
        "                print(\"[route=CLIPBOARD_CAUSAL_EVIDENCE, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]\")\n"
        "                print()\n"
        "                continue\n"
        "            from clipboard_causal_evidence_v09760 import INTENTS\n"
        "            if topic_context.active_topic and any(p.search(user_text) for p, _ in INTENTS):\n"
        "                print(\"AI> 取得した資料から理由を裏付ける記述を確認できませんでした。（外部情報・未検証）\")\n"
        "                print(\"[route=CLIPBOARD_CAUSAL_SOURCE_NEEDED, train_ready=False, auto_promote=False]\")\n"
        "                print()\n"
        "                continue",
    ),
]

for old, new in fixes:
    if new in s:
        print("Already applied")
        continue
    if s.count(old) != 1:
        raise SystemExit("Unexpected chat.py version: anchor not unique. No file written.")
    s = s.replace(old, new)
compile(s, str(p), "exec")
p.write_text(s, encoding="utf-8")
print("Patched and syntax-checked chat.py")
