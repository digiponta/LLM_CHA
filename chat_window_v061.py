"""LLM_CHA v0.6.1: mirror terminal chat into a read-only Tkinter window.

Run: python chat_window_v061.py
The command prompt remains the input interface; chat.py runs unchanged.
"""
import os
import queue
import re
import subprocess
import locale
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext

PROMPT = "You> "
AI_PREFIX = "AI> "
_STOP = object()


def clean_message(text):
    """Keep only user-facing conversation; never display diagnostics."""
    return text.rstrip("\r\n")


class ConversationParser:
    """Line/prompt parser, separated from Tk for deterministic tests."""
    def __init__(self, emit):
        self.emit = emit
        self.buffer = ""
        self.in_ai = False

    def feed(self, text):
        self.buffer += text
        while True:
            newline = self.buffer.find("\n")
            prompt = self.buffer.find(PROMPT)
            if prompt >= 0 and (newline < 0 or prompt < newline):
                prior = self.buffer[:prompt].rstrip("\r")
                if prior:
                    self._line(prior)
                self.buffer = self.buffer[prompt + len(PROMPT):]
                self.in_ai = False
                continue
            if newline < 0:
                break
            line, self.buffer = self.buffer[:newline].rstrip("\r"), self.buffer[newline + 1:]
            self._line(line)

    def _line(self, line):
        if line.startswith(AI_PREFIX):
            self.in_ai = True
            content = clean_message(line[len(AI_PREFIX):])
            if content:
                self.emit("ai", content)
        elif line.startswith("[") or not line.strip() or line.startswith("You>"):
            self.in_ai = False
        elif self.in_ai:
            # Continuations may contain multiline equations or explanations.
            self.emit("ai_continuation", line)


class ConsolePromptDeduper:
    """Collapse adjacent 'You> ' prompts while preserving the live CLI stream."""
    def __init__(self):
        self.candidate = ""
        self.after_prompt = False

    def feed(self, char):
        self.candidate += char
        output = ""
        prompt = PROMPT
        while self.candidate:
            if self.after_prompt:
                # A second prompt immediately after the previous one is redundant.
                prefix = self.candidate.lstrip(" \t")
                if prefix.startswith(prompt):
                    self.candidate = prefix[len(prompt):]
                    continue
                if prompt.startswith(prefix):
                    break
                self.after_prompt = False
            # Check for a new prompt from the beginning of the stream.
            if prompt.startswith(self.candidate):
                if self.candidate == prompt:
                    output += prompt
                    self.candidate = ""
                    self.after_prompt = True
                break
            output += self.candidate[0]
            self.candidate = self.candidate[1:]
        return output


def read_terminal_line():
    """Read Windows console as UTF-16, independent of codepage and pipe UTF-8."""
    if os.name == "nt":
        import ctypes
        import msvcrt
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = msvcrt.get_osfhandle(sys.stdin.fileno())
        mode = wintypes.DWORD()
        if kernel.GetConsoleMode(wintypes.HANDLE(handle), ctypes.byref(mode)):
            # ReadConsoleW provides normal console line editing and Unicode input.
            buffer = ctypes.create_unicode_buffer(4096)
            count = wintypes.DWORD()
            ok = kernel.ReadConsoleW(wintypes.HANDLE(handle), buffer, 4095,
                                     ctypes.byref(count), None)
            if not ok:
                raise OSError("ReadConsoleW failed: {}".format(ctypes.get_last_error()))
            return buffer.value[:count.value]
    return sys.stdin.readline()


def run():
    events = queue.Queue()
    parser = ConversationParser(lambda kind, value: events.put((kind, value)))
    root = tk.Tk()
    root.title("LLM_CHA — 会話履歴 (v0.6.1)")
    root.geometry("760x640")
    root.minsize(460, 280)

    header = tk.Label(root, text="LLM_CHA  会話履歴", anchor="w", font=("Yu Gothic UI", 14, "bold"), padx=14, pady=10)
    header.pack(fill="x")
    display = scrolledtext.ScrolledText(root, wrap="word", state="disabled",
                                        font=("Yu Gothic UI", 11), padx=14, pady=12)
    display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    display.tag_configure("user", foreground="#1266ac", spacing1=12, spacing3=6)
    display.tag_configure("ai", foreground="#174b34", spacing1=12, spacing3=6)
    display.tag_configure("ai_continuation", foreground="#174b34")

    def insert(kind, message):
        if kind == "user":
            output = "あなた: " + message + "\n"
        elif kind == "ai":
            output = "AI: " + message + "\n"
        else:
            output = message + "\n"
        display.configure(state="normal")
        display.insert("end", output, kind)
        display.configure(state="disabled")
        display.see("end")

    command = [sys.executable, "-u", os.path.join(os.path.dirname(__file__), "chat.py")]
    kwargs = dict(cwd=os.path.dirname(__file__), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                  errors="strict", bufsize=1,
                  env={**os.environ, "PYTHONIOENCODING":"utf-8"})
    try:
        child = subprocess.Popen(command, **kwargs)
    except OSError as exc:
        root.destroy()
        raise SystemExit("chat.py を起動できません: " + str(exc))

    def read_child():
        deduper = ConsolePromptDeduper()
        try:
            while True:
                char = child.stdout.read(1)
                if not char:
                    break
                visible = deduper.feed(char)
                if visible:
                    sys.stdout.write(visible)
                    sys.stdout.flush()
                parser.feed(char)
        finally:
            events.put(("exit", child.wait()))

    def forward_terminal():
        try:
            while child.poll() is None:
                line = read_terminal_line()
                if not line:
                    break
                message = line.strip()
                if message and not message.startswith("/"):
                    events.put(("user", message))
                child.stdin.write(line)
                child.stdin.flush()
        except (OSError, ValueError, BrokenPipeError, UnicodeError) as exc:
            print("[GUI input relay error: {}]".format(exc), file=sys.stderr, flush=True)

    threading.Thread(target=read_child, daemon=True).start()
    threading.Thread(target=forward_terminal, daemon=True).start()

    def poll():
        while True:
            try:
                kind, value = events.get_nowait()
            except queue.Empty:
                break
            if kind == "exit":
                root.title("LLM_CHA — 会話終了")
            else:
                insert(kind, value)
        root.after(60, poll)

    def close_window():
        # Closing the mirror must not end the CLI conversation.
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_window)
    root.after(60, poll)
    print("LLM_CHA GUI mirror: コマンドプロンプトに入力してください。", flush=True)
    root.mainloop()
    # If window closes, continue relaying chat in the CLI until /exit.
    if child.poll() is None:
        child.wait()


if __name__ == "__main__":
    run()
