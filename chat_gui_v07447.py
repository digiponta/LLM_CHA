"""LLM_CHA v0.7.44.7 standalone GUI chat frontend (Tkinter).

Uses existing chat.py in a subprocess: one runtime and one memory state.
GUI-only input, preserving Trusted/Wikipedia/experimental routing.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import queue
import subprocess
import sys
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

from chat_window_v061 import ConversationParser, build_chat_command
from gui_latex_v062 import insert_gui_message
from gui_status_v0732 import StatusParser
from gui_command_capture_v074411 import CommandOutputCapture
from gui_sleep_summary_v08016 import summarize_sleep_output


def create_process(command, quality_gate=True):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    env["LLM_CHA_RESPONSE_GATE"] = "1" if quality_gate else "0"
    env["LLM_CHA_DAILY_CHAT"] = "1"
    env["LLM_CHA_TOPIC_NORMALIZE"] = "1"
    env["LLM_CHA_CORPUS_FOLLOWUP"] = "1"
    env["LLM_CHA_FOLLOWUP_RELEVANCE"] = "1"
    env["LLM_CHA_ASPECT_EVIDENCE"] = "1"
    return subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace", bufsize=1, env=env,
        cwd=str(Path(__file__).resolve().parent),
    )


def run(argv=None):
    parser = argparse.ArgumentParser(description="LLM_CHA GUI-only chat")
    parser.add_argument("--no-quality-gate", action="store_true")
    args, chat_args = parser.parse_known_args(argv)
    command, model_label = build_chat_command(chat_args)
    events = queue.Queue()
    parser_stream = ConversationParser(lambda kind, value: events.put((kind, value)))
    status_parser = StatusParser(lambda value: events.put(("status", value)))
    root = tk.Tk()
    root.title("LLM_CHA v0.8.0.17 — GUI Chat")
    root.geometry("970x720")
    root.minsize(600, 400)

    heading = tk.Frame(root, padx=12, pady=8)
    heading.pack(fill="x")
    tk.Label(heading, text="LLM_CHA — Semantic Memory",
             font=("Yu Gothic UI", 14, "bold")).pack(anchor="w")
    quality_status = "ON" if not args.no_quality_gate else "OFF"
    status = tk.StringVar(value=f"Model: {model_label} | Quality Gate: {quality_status} | 起動中")
    tk.Label(heading, textvariable=status, anchor="w", font=("Yu Gothic UI", 9)).pack(fill="x")
    view = scrolledtext.ScrolledText(root, state="disabled", wrap="word",
                                    font=("Yu Gothic UI", 11), padx=12, pady=12)
    view.pack(fill="both", expand=True, padx=10, pady=8)
    view.tag_configure("user", foreground="#125b9a", spacing1=10, spacing3=4)
    view.tag_configure("ai", foreground="#176344", spacing1=10, spacing3=4)
    view.tag_configure("ai_continuation", foreground="#176344")
    view.tag_configure("source_wiki", foreground="#285b9f")
    view.tag_configure("source_raw", foreground="#99631c")
    images = []

    def display(kind, value):
        view.configure(state="normal")
        label = "あなた: " if kind == "user" else "AI: " if kind == "ai" else ""
        tag = kind
        if kind != "user" and "【Wikipedia検索結果・外部情報・未検証】" in value:
            tag = "source_wiki"
        elif kind != "user" and "【原文中の関連記述・未検証】" in value:
            tag = "source_raw"
        if kind == "user":
            view.insert("end", label + value + "\n", tag)
        else:
            insert_gui_message(view, label + value + "\n", tag, images)
        view.configure(state="disabled")
        view.see("end")

    entry_frame = tk.Frame(root, padx=10, pady=8)
    entry_frame.pack(fill="x")
    entry = tk.Entry(entry_frame, font=("Yu Gothic UI", 11))
    entry.pack(side="left", fill="x", expand=True)
    try:
        child = create_process(command, not args.no_quality_gate)
    except OSError as exc:
        root.destroy()
        raise SystemExit(f"chat.py 起動失敗: {exc}")
    mutex = threading.Lock()
    command_capture = CommandOutputCapture()
    capture_mutex = threading.Lock()

    def send(value, echo=True):
        if child.poll() is not None:
            return False
        try:
            with mutex:
                child.stdin.write(value + "\n")
                child.stdin.flush()
        except (OSError, ValueError, BrokenPipeError):
            return False
        if echo and not value.startswith("/"):
            events.put(("user", value))
        return True

    def submit(event=None):
        value = entry.get().strip()
        if value and send(value):
            entry.delete(0, "end")

    tk.Button(entry_frame, text="送信", command=submit).pack(side="left", padx=6)

    pending_status = {"command": None, "started": None}
    def request_status(command="/semstatus"):
        if child.poll() is not None:
            messagebox.showwarning("状態確認", "chat.pyが終了しています。")
            return
        if pending_status["command"] is not None:
            status.set("状態確認: 前のコマンドの完了待ち")
            return
        pending_status["command"] = command
        pending_status["started"] = time.monotonic()
        with capture_mutex:
            command_capture.start()
        if not send(command, False):
            with capture_mutex:
                command_capture.active = False
            pending_status["command"] = None
            pending_status["started"] = None
            messagebox.showerror("状態確認", "コマンドを送信できませんでした。")
        else:
            status.set("状態確認: {} の結果を取得中".format(command))
    tk.Button(entry_frame, text="Semantic状態",
              command=lambda:request_status("/semstatus")).pack(side="left", padx=(6,0))
    tk.Button(entry_frame, text="/sleep 実行",
              command=lambda:request_status("/sleep")).pack(side="left", padx=(6,0))
    def compare_unapproved():
        question=entry.get().strip()
        if not question:
            messagebox.showinfo("未承認LLM比較", "比較する質問を入力してください。")
            return
        request_status("/wiki-model-compare "+question)
    tk.Button(entry_frame, text="未承認LLM比較",command=compare_unapproved).pack(side="left",padx=(6,0))
    tk.Button(entry_frame, text="学習状態",
              command=lambda:request_status("/sleep status")).pack(side="left", padx=(6,0))
    entry.bind("<Return>", submit)
    entry.focus_set()

    def reader():
        try:
            while True:
                char = child.stdout.read(1)
                if not char:
                    break
                parser_stream.feed(char)
                status_parser.feed(char)
                with capture_mutex:
                    captured = command_capture.feed(char)
                if captured is not None:
                    events.put(("command_output", captured))
        finally:
            events.put(("exit", child.wait()))

    threading.Thread(target=reader, daemon=True).start()

    def poll():
        while True:
            try:
                kind, value = events.get_nowait()
            except queue.Empty:
                break
            if kind in ("user", "ai", "ai_continuation"):
                display(kind, value)
            elif kind == "command_output":
                dialog = tk.Toplevel(root)
                command = pending_status["command"] or "status"
                pending_status["command"] = None
                pending_status["started"] = None
                dialog.title("LLM_CHA " + command)
                dialog.geometry("780x520")
                output_view = scrolledtext.ScrolledText(dialog, wrap="word",
                    font=("Consolas", 10))
                output_view.pack(fill="both", expand=True, padx=8, pady=8)
                output_view.insert("1.0", value or "状態情報がありません。")
                output_view.configure(state="disabled")
                if command == "/sleep":
                    sleep_result = summarize_sleep_output(value)
                    status.set(sleep_result["label"])
                    dialog.title("LLM_CHA /sleep — "+sleep_result["state"])
                else:
                    status.set("状態確認: 完了")
            elif kind == "status":
                if "route" in value and value["route"]:
                    status.set(f"Model: {model_label} | Quality Gate: {quality_status} | {value['route']}")
            elif kind == "exit":
                if pending_status["command"] is not None:
                    command = pending_status["command"]
                    pending_status["command"] = None
                    pending_status["started"] = None
                    messagebox.showwarning("状態確認", "{} の実行中にchat.pyが終了しました。".format(command))
                status.set(f"chat.py 終了 (exit={value})")
                entry.configure(state="disabled")
        if (pending_status["command"] is not None and pending_status["started"] is not None
                and pending_status["command"] != "/sleep"
                and not pending_status["command"].startswith("/wiki-model-compare ")
                and time.monotonic() - pending_status["started"] > 20):
            command = pending_status["command"]
            pending_status["command"] = None
            pending_status["started"] = None
            with capture_mutex:
                command_capture.active = False
                command_capture.buffer = ""
            status.set("状態確認: {} がタイムアウトしました".format(command))
            messagebox.showwarning("状態確認", "応答待ちが20秒を超えました: " + command)
        root.after(70, poll)

    def close():
        if child.poll() is None:
            try:
                send("/exit", False)
                child.terminate()
            except OSError:
                pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.after(70, poll)
    root.mainloop()


if __name__ == "__main__":
    run()
