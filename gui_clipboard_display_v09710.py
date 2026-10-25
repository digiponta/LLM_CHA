"""Compact clipboard JSON in GUI, keeping chat.py's CLI output intact.

The parser forwards one AI summary for successful reads but hides the raw JSON.
Only content with the expected clipboard route is filtered. Incomplete or
unrecognized JSON is passed through to avoid silently hiding diagnostics.
"""
import json

class ClipboardDisplayFilter:
    def __init__(self, emit):
        self.emit=emit
        self.capturing=False
        self.lines=[]
    def feed(self,kind,message):
        if kind=="ai" and message=="クリップボードのテキストを読み取りました。":
            self.capturing=True
            self.lines=[]
            return
        if self.capturing:
            if kind=="ai_continuation":
                self.lines.append(message)
                raw="\n".join(self.lines)
                try:
                    data=json.loads(raw)
                except json.JSONDecodeError:
                    # Avoid indefinite capture on malformed payloads.
                    if len(raw)>100000:
                        self._flush()
                    return
                if isinstance(data,dict) and data.get("route")=="CLIPBOARD_CONTEXT_READ":
                    chars=data.get("characters","?")
                    extra="（一部省略）" if data.get("truncated") else ""
                    self.emit("ai",f"クリップボードを読み込みました（{chars}文字{extra}・一時文脈・未検証）。")
                    self.capturing=False
                    self.lines=[]
                    return
                self._flush()
                return
            self._flush()
        self.emit(kind,message)
    def _flush(self):
        self.emit("ai","クリップボードのテキストを読み取りました。")
        for line in self.lines:
            self.emit("ai_continuation",line)
        self.capturing=False
        self.lines=[]
