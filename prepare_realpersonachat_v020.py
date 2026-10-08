"""Convert RealPersonaChat dialogue JSON into LLM_CHA conversational SFT JSONL.

Source: https://github.com/nu-dialogue/real-persona-chat
License: CC BY-SA 4.0 (retain attribution; avoid impersonating participants).

All examples from the same dialogue belong to the same split.
Never add original interlocutor profiles to character metadata or Semantic Memory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def split_for(dialogue_id: str, seed: str = "LLM_CHA_RPC_v020") -> str:
    value = int(hashlib.sha256((seed + ":" + dialogue_id).encode("utf-8")).hexdigest()[:8], 16) / 0xffffffff
    return "test" if value < 0.05 else "val" if value < 0.10 else "train"


def dialogue_pairs(row: dict, context_turns: int = 3):
    utterances = row.get("utterances", [])
    if not isinstance(utterances, list):
        return
    for index in range(1, len(utterances)):
        previous, current = utterances[index - 1], utterances[index]
        if not isinstance(previous, dict) or not isinstance(current, dict):
            continue
        if previous.get("interlocutor_id") == current.get("interlocutor_id"):
            continue
        answer = current.get("text", "")
        if not isinstance(answer, str) or not answer.strip():
            continue
        # Only use dialogue turns. Do not train the model to claim original
        # participants' real biography, name, age, location or persona.
        window = utterances[max(0, index - context_turns):index]
        lines = []
        for item in window:
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                continue
            message = item["text"].strip()
            if message and len(message) <= 300 and "＊＊" not in message and "<" not in message:
                role = "相手" if item.get("interlocutor_id") == current.get("interlocutor_id") else "人"
                lines.append(role + ": " + message)
        answer = answer.strip()
        if not lines or len(answer) > 300 or "＊＊" in answer or "<" in answer:
            continue
        # Train a generic dialogue response, never a specific participant identity.
        yield {"user": "\n".join(lines), "assistant": answer}


def convert(source: Path, output: Path, max_dialogues: int = 0, context_turns: int = 3) -> dict:
    files = sorted(source.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No dialogue JSON files in {source}")
    output.mkdir(parents=True, exist_ok=True)
    counts = {"train": 0, "val": 0, "test": 0}
    dialogues = {"train": 0, "val": 0, "test": 0}
    seen = set()
    handles = {name: (output / f"rpc_{name}.jsonl").open("w", encoding="utf-8") for name in counts}
    try:
        for path in files[:max_dialogues or None]:
            row = json.loads(path.read_text(encoding="utf-8"))
            dialogue_id = str(row.get("dialogue_id", path.stem))
            split = split_for(dialogue_id)
            dialogues[split] += 1
            for pair in dialogue_pairs(row, context_turns=context_turns):
                fingerprint = hashlib.sha256((pair["user"] + "\0" + pair["assistant"]).encode("utf-8")).hexdigest()
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                handles[split].write(json.dumps(pair, ensure_ascii=False) + "\n")
                counts[split] += 1
    finally:
        for handle in handles.values():
            handle.close()
    report = {"dialogues": dialogues, "pairs": counts, "source": "RealPersonaChat", "license": "CC BY-SA 4.0"}
    (output / "rpc_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dialogues", type=Path, required=True, help="Path to real_persona_chat/dialogues")
    parser.add_argument("--output", type=Path, default=Path("data/realpersonachat"))
    parser.add_argument("--max-dialogues", type=int, default=0, help="0 = all")
    parser.add_argument("--context-turns", type=int, default=3)
    args = parser.parse_args()
    if args.context_turns < 1 or args.max_dialogues < 0:
        parser.error("context-turns >= 1 and max-dialogues >= 0 required")
    print(json.dumps(convert(args.dialogues, args.output, args.max_dialogues, args.context_turns), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
