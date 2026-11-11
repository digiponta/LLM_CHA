"""LLM_CHA v0.11: optional in-process SKI evidence diagnostic.

The actual LLM_CHA chat.py invokes this before any training, RSE or generation
routing for explicitly typed '/ski' commands. Ordinary chat is unaffected.
This module does not modify persistent files, infer facts or train models.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

DEFAULT_PREFIX = "/ski"


def parse_ski_command(line):
    """Return a bounded request, or None if the line is not a SKI command."""
    if not isinstance(line, str):
        raise ValueError("INVALID_SKI_INPUT")
    if line != DEFAULT_PREFIX and not line.startswith(DEFAULT_PREFIX + " "):
        return None
    if not line or len(line) > 4000 or any(x in line for x in ("\r", "\n", "\x00")):
        raise ValueError("INVALID_SKI_INPUT")
    command, separator, question = line.partition("|")
    parts = command.split()
    if len(parts) != 3 or any(not x or len(x) > 256 for x in parts[1:]):
        raise ValueError("USAGE: /ski SOURCE_SD TARGET_SD | question")
    if separator and not question.strip():
        raise ValueError("EMPTY_SKI_QUESTION")
    return {
        "source_sd": parts[1],
        "target_sd": parts[2],
        "question": question.strip() if separator else "このSemantic関係のEvidenceを確認してください。",
    }


def _required_directory(name, value, expected_file):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + "_NOT_CONFIGURED")
    root = Path(value).expanduser().resolve()
    if not (root / expected_file).is_file():
        raise ValueError(name + "_MODULE_NOT_FOUND")
    return root


def execute_ski_query(request, *, bridge_dir, tmp_dir, native_path, predicate=""):
    """Use real, trusted local LLM_TMP APIs and SKI BRIDGE; diagnostic-only."""
    bridge_root = _required_directory(
        "LLM_CHA_SKI_BRIDGE_DIR", bridge_dir,
        "adapters/cha_truth_boundary_v07.py")
    tmp_root = _required_directory(
        "LLM_CHA_SKI_TMP_DIR", tmp_dir, "intent_sd_context_v03.py")
    native = Path(native_path).expanduser().resolve() if native_path else None
    if native is None or not native.is_file():
        raise ValueError("LLM_CHA_SKI_NATIVE_NOT_FOUND")
    # The sibling repository is trusted local code. No external network/exec.
    if str(bridge_root) not in sys.path:
        sys.path.insert(0, str(bridge_root))
    from adapters.llm_tmp_native_v09 import convert_file
    from adapters.llm_tmp_registry_v08 import build_relation_graph
    from adapters.llm_cha_client_v05 import CHAClient
    from adapters.llm_tmp_real import LLM_TMPAdapter
    from adapters.cha_truth_boundary_v07 import assess_exchange
    from verify_llm_tmp_integration_v03 import load_graph_class

    predicates = (predicate,) if predicate else ()
    converted, report = convert_file(
        native, tmp_root, supported_by_predicates=predicates)
    graph = build_relation_graph(load_graph_class(tmp_root), converted)
    exchange = CHAClient(LLM_TMPAdapter(graph)).exchange(
        request["question"], source_sd=request["source_sd"],
        target_sd=request["target_sd"])
    decision = assess_exchange(exchange)
    if (decision["action"] != "DIAGNOSTIC_ONLY"
            or decision["allow_model_context"] is not False
            or decision["allow_answer_from_evidence"] is not False
            or decision["allow_learning"] is not False
            or decision["allow_truth_promotion"] is not False):
        raise ValueError("UNSAFE_SKI_RESULT")
    return {
        "status": decision["evidence_status"],
        "message": decision["display_message"],
        "request_message_id": decision["request_message_id"],
        "response_to_message_id": decision["response_to_message_id"],
        "verified_fact": False,
        "human_approved": False,
        "llm_inference_invoked": False,
        "mapped_relations": report["relations_exported"],
    }


def handle_ski_input(line, *, environ=None, executor=None):
    """None means regular chat. Otherwise a complete fail-closed SKI outcome.

    Pass a fake executor in unit tests; production uses execute_ski_query.
    """
    try:
        parsed = parse_ski_command(line)
    except ValueError:
        return {"kind": "SKI_DIAGNOSTIC", "status": "ERROR",
                "message": "SKIコマンド形式が不正です。/ski SOURCE_SD TARGET_SD | question"}
    if parsed is None:
        return None
    env = os.environ if environ is None else environ
    if env.get("LLM_CHA_SKI_ENABLED") != "1":
        return {"kind": "SKI_DIAGNOSTIC", "status": "DISABLED",
                "message": "SKI連携は無効です。LLM_CHA_SKI_ENABLED=1で有効にしてください。"}
    try:
        fn = executor or execute_ski_query
        result = fn(
            parsed,
            bridge_dir=env.get("LLM_CHA_SKI_BRIDGE_DIR", ""),
            tmp_dir=env.get("LLM_CHA_SKI_TMP_DIR", ""),
            native_path=env.get("LLM_CHA_SKI_NATIVE", ""),
            predicate=env.get("LLM_CHA_SKI_PREDICATE", ""),
        )
        if (not isinstance(result, dict) or
                result.get("status") not in (
                    "FOUND", "NOT_FOUND", "UNKNOWN_NODE",
                    "LIMIT_REACHED", "DEPTH_LIMIT_REACHED")
                or result.get("verified_fact") is not False
                or result.get("human_approved") is not False
                or result.get("llm_inference_invoked") is not False
                or result.get("request_message_id") != result.get("response_to_message_id")):
            raise ValueError("INVALID_SKI_DIAGNOSTIC")
        return {"kind": "SKI_DIAGNOSTIC", **result}
    except (ValueError, RuntimeError, OSError, ImportError, KeyError, TypeError):
        return {"kind": "SKI_DIAGNOSTIC", "status": "ERROR",
                "message": "SKIの検証に失敗しました。通常の回答や学習には使用していません。"}


def print_ski_diagnostic(result, *, printer=print):
    """Emit a deliberately separate diagnostic; never an answer/assertion."""
    if result is None:
        return False
    printer("AI> 【SKI診断・事実未検証】" + result["message"])
    printer("[ski_status=" + result["status"] + ", route=SKI_DIAGNOSTIC_ONLY]")
    printer()
    return True
