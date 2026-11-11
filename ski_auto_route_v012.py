"""v0.12 opt-in, deterministic Japanese evidence-query router.

An exact native SD display-name mention plus a narrowly recognized
evidence-query form and exactly one approved, explicitly mapped edge are
required. Never infer a topic from conversational history or guess synonyms.
The result is diagnostic-only; no generated answer or learning.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

INTENT_ENDINGS = (
    "の根拠を確認して", "の根拠を確認してください",
    "の根拠を教えて", "の根拠を教えてください",
    "の根拠は何ですか", "の根拠は",
)
ENDING_PUNCT = "。.!！?？"


def _strict_subject(text):
    if not isinstance(text, str) or not 1 <= len(text) <= 1000:
        return None
    if text.startswith("/") or any(c in text for c in ("\n", "\r", "\x00")):
        return None
    trimmed = text.strip().rstrip(ENDING_PUNCT).strip()
    for suffix in INTENT_ENDINGS:
        if trimmed.endswith(suffix):
            subject = trimmed[:-len(suffix)].strip()
            if subject and len(subject) <= 256:
                return subject
    return None


def resolve_auto_query(text, native_snapshot, converted_snapshot):
    """Return explicit source/target SD IDs only when uniquely grounded."""
    subject = _strict_subject(text)
    if subject is None:
        return None
    if not isinstance(native_snapshot, dict) or not isinstance(converted_snapshot, dict):
        raise ValueError("INVALID_AUTO_SNAPSHOT")
    names = native_snapshot.get("display_names")
    if not isinstance(names, dict):
        # No trusted display labels means no language-to-SD mapping.
        return None
    nodes = native_snapshot.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("INVALID_AUTO_NODES")
    eligible = {n["sd_id"] for n in nodes if n["node_type"] in ("TOPIC", "CONCEPT", "ENTITY")}
    labels = []
    for sd_id in sorted(eligible):
        label = names.get(sd_id)
        # IDs alone are not Japanese-language evidence.
        if isinstance(label, str) and label.strip() and label == subject:
            labels.append(sd_id)
    if len(labels) != 1:
        return None
    source = labels[0]
    # Native APPROVED is NOT factual approval; these only select an
    # unauthenticated structural query target, never a model fact.
    targets = sorted({e["target"] for e in converted_snapshot["relations"]
                      if e["source"] == source and e["kind"] == "SUPPORTED_BY"
                      and e["state"] == "APPROVED"})
    if len(targets) != 1 or source == targets[0]:
        return None
    return {
        "source_sd": source, "target_sd": targets[0],
        "question": text, "route": "EXACT_LABEL_SINGLE_APPROVED_MAPPING",
    }


def auto_route(text, *, environ=None, executor=None):
    """None passes through to ordinary LLM_CHA handling."""
    env = os.environ if environ is None else environ
    if (env.get("LLM_CHA_SKI_ENABLED") != "1"
            or env.get("LLM_CHA_SKI_AUTO_ENABLED") != "1"
            or _strict_subject(text) is None):
        return None
    try:
        from ski_runtime_v011 import execute_ski_query
        from ski_runtime_v011 import _required_directory
        from importlib import import_module
        import sys
        bridge_dir = _required_directory("LLM_CHA_SKI_BRIDGE_DIR",
            env.get("LLM_CHA_SKI_BRIDGE_DIR", ""),
            "adapters/llm_tmp_native_v09.py")
        tmp_dir = _required_directory("LLM_CHA_SKI_TMP_DIR",
            env.get("LLM_CHA_SKI_TMP_DIR", ""), "intent_sd_context_v03.py")
        native_path = env.get("LLM_CHA_SKI_NATIVE", "")
        predicate = env.get("LLM_CHA_SKI_PREDICATE", "")
        if not predicate:
            # Auto-discovery cannot proceed without explicit semantic mapping.
            return None
        if str(bridge_dir) not in sys.path:
            sys.path.insert(0, str(bridge_dir))
        from adapters.llm_tmp_native_v09 import read_native, convert_file
        native_data, original_hash = read_native(native_path)
        converted, meta = convert_file(
            native_path, tmp_dir, supported_by_predicates=(predicate,))
        if original_hash != meta["native_file_sha256"]:
            raise ValueError("CHANGED_NATIVE_SOURCE")
        request = resolve_auto_query(text, native_data, converted)
        if request is None:
            return None
        run = executor or execute_ski_query
        result = run(
            request, bridge_dir=str(bridge_dir), tmp_dir=str(tmp_dir),
            native_path=native_path, predicate=predicate)
        if (not isinstance(result, dict)
                or result.get("status") not in ("FOUND", "NOT_FOUND",
                                               "UNKNOWN_NODE", "LIMIT_REACHED")
                or result.get("verified_fact") is not False
                or result.get("human_approved") is not False
                or result.get("llm_inference_invoked") is not False
                or result.get("request_message_id") != result.get("response_to_message_id")):
            raise ValueError("INVALID_AUTO_DIAGNOSTIC")
        return {
            "kind": "SKI_AUTO_DIAGNOSTIC",
            "status": result["status"],
            "message": result["message"],
            "verified_fact": False,
            "allow_model_context": False,
            "ski_diagnostic_profile": result.get("ski_diagnostic_profile"),
        }
    except (ValueError, RuntimeError, OSError, ImportError, KeyError, TypeError):
        # An explicit evidence-query candidate must not fall through when
        # a configured adapter fails. Treat it as an unverified error.
        return {
            "kind": "SKI_AUTO_DIAGNOSTIC",
            "status": "ERROR",
            "message": "Semantic照会を検証できませんでした。回答・学習に使用していません。",
            "verified_fact": False, "allow_model_context": False,
        }


def display_auto_diagnostic(result, *, printer=print):
    if result is None:
        return False
    printer("AI> 【SKI自動照会・事実未検証】" + result["message"])
    profile = result.get("ski_diagnostic_profile")
    profile_info = ", ski_profile=" + profile if profile else ""
    printer("[ski_auto_status=" + result["status"] +
            ", route=SKI_AUTO_DIAGNOSTIC_ONLY" + profile_info + "]")
    printer("")
    return True
