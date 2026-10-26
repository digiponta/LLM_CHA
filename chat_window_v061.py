"""LLM_CHA v0.6.8: model-selectable terminal chat mirror.

Run: python chat_window_v061.py
The command prompt remains the input interface; chat.py runs unchanged.
"""
import argparse
import os
import queue
import re
import subprocess
import locale
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
from gui_latex_v062 import insert_gui_message
from gui_status_v0732 import StatusParser

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
        elif line.startswith("[") or line.startswith("You>"):
            # Diagnostics and prompts terminate the current assistant message.
            self.in_ai = False
        elif self.in_ai:
            # A blank line inside an answer is a paragraph separator, not
            # its end. Keep collecting through the provenance/source lines.
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


EXPERIMENTAL_MODELS = (
    "model/model-llm-cha-aozora-replay-v067-r2.pt",
    "model/model-llm-cha-aozora-replay-v067.pt",
    "model/model-llm-cha-aozora-v065.pt",
)


def build_chat_command(argv=None, base_dir=None):
    """Build chat.py command; experimental checkpoints always require opt-in."""
    parser = argparse.ArgumentParser(description="LLM_CHA conversation mirror")
    parser.add_argument("--gui-only-input", action="store_true", help="Disable terminal input relay to avoid console interleaving")
    parser.add_argument("--model", default=None, help="Explicit checkpoint")
    parser.add_argument("--tokenizer", default=None, help="Explicit tokenizer")
    parser.add_argument("--latest-experimental", action="store_true",
                        help="Select newest locally available Aozora checkpoint")
    args, rest = parser.parse_known_args(argv)
    if args.model and args.latest_experimental:
        parser.error("choose --model OR --latest-experimental")
    root = os.path.abspath(base_dir or os.path.dirname(__file__))
    model = args.model
    if args.latest_experimental:
        model = next((name for name in EXPERIMENTAL_MODELS
                      if os.path.isfile(os.path.join(root, name))), None)
        if model is None:
            parser.error("no experimental checkpoint found")
    command = [sys.executable, "-u", os.path.join(root, "chat.py")]
    if model:
        resolved = model if os.path.isabs(model) else os.path.join(root, model)
        if not os.path.isfile(resolved):
            parser.error("model not found: " + resolved)
        command += ["--model", resolved]
    if args.tokenizer or args.latest_experimental:
        token_name = args.tokenizer or "model/tokenizer-v0.7-bpe.json"
        resolved = token_name if os.path.isabs(token_name) else os.path.join(root, token_name)
        if not os.path.isfile(resolved):
            parser.error("tokenizer not found: " + resolved)
        command += ["--tokenizer", resolved]
    command.extend(rest)
    return command, os.path.basename(model) if model else "chat.py default"


def run():
    gui_only_input = "--gui-only-input" in sys.argv[1:]
    command, model_label = build_chat_command()
    events = queue.Queue()
    from gui_clipboard_display_v09710 import ClipboardDisplayFilter
    clipboard_display = ClipboardDisplayFilter(lambda kind, value: events.put((kind, value)))
    parser = ConversationParser(clipboard_display.feed)
    status_parser = StatusParser(lambda value: events.put(("status", value)))
    root = tk.Tk()
    root.title("LLM_CHA — GUI / Semantic Diagnostics (v0.9.7.50)")
    root.geometry("960x700")
    root.minsize(460, 280)

    header = tk.Label(root, text="LLM_CHA  会話履歴 — " + model_label, anchor="w", font=("Yu Gothic UI", 14, "bold"), padx=14, pady=10)
    header.pack(fill="x")
    status_vars = {name: tk.StringVar(value=label) for name, label in (
        ("trusted", "Trusted: initializing"),
        ("trusted_pending", "Trusted pending: unknown"),
        ("experimental", "Experimental: not active / waiting"),
        ("candidate", "Candidates: unknown"),
        ("route", "Last route: unknown"),
        ("approval", "Source approval: unknown"),
    )}
    bar = tk.Frame(root, padx=10, pady=5)
    bar.pack(fill="x")
    first_row = tk.Frame(bar)
    first_row.pack(fill="x")
    second_row = tk.Frame(bar)
    second_row.pack(fill="x")
    for name in ("trusted", "trusted_pending", "experimental", "candidate"):
        tk.Label(first_row, textvariable=status_vars[name], anchor="w",
                 font=("Yu Gothic UI", 9), padx=6).pack(side="left")
    tk.Label(second_row, textvariable=status_vars["route"], anchor="w",
             font=("Yu Gothic UI", 9), padx=6).pack(side="left")
    tk.Label(second_row, textvariable=status_vars["approval"], anchor="w",
             font=("Yu Gothic UI", 9), padx=6).pack(side="left")
    from gui_semantic_preview_v09745 import semantic_preview, format_preview
    semantic_enabled = tk.BooleanVar(value=True)
    semantic_bar = tk.Frame(root, padx=12, pady=2)
    semantic_bar.pack(fill="x")
    tk.Checkbutton(semantic_bar, text="Semantic診断と修正候補を表示（chat.py応答は変更しない）",
                   variable=semantic_enabled, anchor="w").pack(side="left")
    last_user_input = None
    display = scrolledtext.ScrolledText(root, wrap="word", state="disabled",
                                        font=("Yu Gothic UI", 11), padx=14, pady=12)
    display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    display.tag_configure("user", foreground="#1266ac", spacing1=12, spacing3=6)
    display.tag_configure("ai", foreground="#174b34", spacing1=12, spacing3=6)
    display.tag_configure("ai_continuation", foreground="#174b34")
    display.tag_configure("source_raw", foreground="#845422", spacing1=5)
    display.tag_configure("source_wiki", foreground="#245ea8", spacing1=7)
    display.tag_configure("source_link", foreground="#245ea8", underline=True)
    display.tag_configure("semantic_diagnostic", foreground="#855223", spacing1=4, spacing3=8)

    gui_images = []  # Keep Tk PhotoImage references alive.

    def insert(kind, message):
        nonlocal last_user_input
        if kind == "user":
            last_user_input = message if not message.startswith("/") else None
            output = "あなた: " + message + "\n"
        elif kind == "ai":
            output = "AI: " + message + "\n"
        else:
            output = message + "\n"
        display.configure(state="normal")
        selected = kind
        if kind != "user":
            if "【Wikipedia検索結果・外部情報・未検証】" in message:
                selected = "source_wiki"
            elif message.startswith("出典：https://"):
                selected = "source_link"
            elif "【原文中の関連記述・未検証】" in message:
                selected = "source_raw"
        insert_gui_message(display, output, selected, gui_images) if kind != "user" else display.insert("end", output, kind)
        display.configure(state="disabled")
        display.see("end")
        if kind == "ai" and semantic_enabled.get() and last_user_input:
            try:
                preview = semantic_preview(last_user_input, message)
                annotation = format_preview(preview)
            except (ValueError, TypeError, KeyError) as exc:
                annotation = "Semantic診断を適用できません: " + str(exc)
            if annotation:
                display.configure(state="normal")
                display.insert("end", annotation + "\n", "semantic_diagnostic")
                display.configure(state="disabled")
                display.see("end")

    input_frame = tk.Frame(root, padx=10, pady=6)
    input_frame.pack(fill="x", side="bottom")
    prompt_entry = tk.Entry(input_frame, font=("Yu Gothic UI", 11))
    prompt_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
    input_lock = threading.Lock()
    def send_to_chat(line, show_user=True):
        if not line.strip() or child.poll() is not None:
            return False
        with input_lock:
            try:
                child.stdin.write(line.rstrip("\r\n") + "\n")
                child.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                return False
        message = line.strip()
        if show_user and not message.startswith("/"):
            events.put(("user", message))
        return True
    def submit_entry(event=None):
        value = prompt_entry.get().strip()
        if value and send_to_chat(value):
            prompt_entry.delete(0, "end")
    tk.Button(input_frame, text="送信", command=submit_entry,
              font=("Yu Gothic UI", 10)).pack(side="left")
    def trigger_sleep():
        send_to_chat("/sleep", show_user=False)
    tk.Button(input_frame, text="/sleep", command=trigger_sleep,
              font=("Yu Gothic UI", 10)).pack(side="left", padx=(6, 0))
    def trigger_read_clipboard():
        # Send exactly the same command as typing /read-clipboard in chat.py.
        send_to_chat("/read-clipboard", show_user=False)
    tk.Button(input_frame, text="クリップボード読込",
              command=trigger_read_clipboard,
              font=("Yu Gothic UI", 10)).pack(side="left", padx=(6, 0))
    prompt_entry.bind("<Return>", submit_entry)

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
                status_parser.feed(char)
        finally:
            events.put(("exit", child.wait()))

    def forward_terminal():
        try:
            while child.poll() is None:
                line = read_terminal_line()
                if not line:
                    break
                send_to_chat(line)
        except (OSError, ValueError, BrokenPipeError, UnicodeError) as exc:
            print("[GUI input relay error: {}]".format(exc), file=sys.stderr, flush=True)

    threading.Thread(target=read_child, daemon=True).start()
    if not gui_only_input:
        threading.Thread(target=forward_terminal, daemon=True).start()

    closing_for_exit = False

    def poll():
        nonlocal closing_for_exit
        while True:
            try:
                kind, value = events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                for name, text in value.items():
                    if name in status_vars and text is not None:
                        status_vars[name].set(text)
                continue
            if kind == "exit":
                closing_for_exit = True
                root.destroy()
                return
            else:
                insert(kind, value)
        if not closing_for_exit:
            root.after(60, poll)

    def close_window():
        # Closing the mirror must not end the CLI conversation.
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_window)
    root.after(60, poll)
    print("LLM_CHA GUI: GUI入力またはコマンドプロンプトに入力してください。", flush=True)
    root.mainloop()
    # A manually closed mirror should not block CLI input or force the child to stop.
    # The process remains until the CLI receives /exit, like the original launcher.
    if child.poll() is None:
        child.wait()


if __name__ == "__main__":
    run()
