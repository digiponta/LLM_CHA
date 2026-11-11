"""v0.13: bounded, fail-closed multi-turn SKI context diagnostics.

Only session-local, explicitly named native SD topics are retained.
The LLM_TMP v0.3.3 Context Intent Resolver provides a second conservative
ambiguity veto for its known topics; it is not an Evidence query resolver.
No provenance authentication, model grounding or learning is performed.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import sys

FOLLOWUPS = frozenset((
    "その根拠は", "その根拠を確認して", "その根拠を確認してください",
    "その根拠を教えて", "その根拠を教えてください",
    "根拠は", "根拠は何ですか", "根拠を確認してください",
))
PUNCT = "。!?！？"
MAX_GAP = 2


def empty_context():
    return {"turn": 0, "source_sd": None, "source_turn": None}


def _text(text):
    return (isinstance(text, str) and 0 < len(text) <= 1000
            and not text.startswith("/") and
            not any(x in text for x in ("\r", "\n", "\x00")))


def _is_followup(text):
    return _text(text) and text.strip().rstrip(PUNCT).strip() in FOLLOWUPS


def _labels(native):
    names = native.get("display_names")
    nodes = native.get("nodes")
    if not isinstance(names, dict) or not isinstance(nodes, list):
        return {}
    allowed = {n["sd_id"] for n in nodes
               if n["node_type"] in ("TOPIC", "CONCEPT", "ENTITY")}
    return {sid: label for sid, label in names.items()
            if sid in allowed and isinstance(label, str)
            and label.strip() and label != sid}


def _mentions(text, labels):
    # Ignore substrings within ascii names; Japanese labels are literal.
    hits = set()
    for sid, label in labels.items():
        if label.isascii() and label.isalnum():
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(label) + r"(?![A-Za-z0-9_])"
            found = bool(re.search(pattern, text, re.I))
        else:
            found = label in text
        if found:
            hits.add(sid)
    return hits


def _target(source, converted):
    matching = {e["target"] for e in converted["relations"]
                if e["source"] == source and e["kind"] == "SUPPORTED_BY"
                and e["state"] == "APPROVED"}
    return next(iter(matching)) if len(matching) == 1 and source not in matching else None


def _tmp_veto(text, resolver):
    """Native TMP resolver cannot resolve general Evidence requests.

    Its known-topic ambiguity logic is used only as an additional veto.
    """
    if resolver is None:
        return False
    result = resolver(text)
    return (result.get("status") == "ABSTAIN"
            and result.get("reason") in ("MULTIPLE_TOPICS", "MULTIPLE_ATTRIBUTES"))


def next_context(text, state, native, converted, *, tmp_resolver=None):
    """Return (new session state, optional SKI request, reason).

    No mutable state or native object is changed. An unrecognized phrase
    passes through to normal LLM_CHA without fabricated topic context.
    """
    if not isinstance(state, dict) or set(state) != {"turn", "source_sd", "source_turn"}:
        raise ValueError("INVALID_SKI_CONTEXT")
    if type(state["turn"]) is not int or state["turn"] < 0:
        raise ValueError("INVALID_SKI_CONTEXT_TURN")
    if text == "/reset":
        return empty_context(), None, "RESET"
    if not _text(text):
        return dict(state), None, "NON_CHAT"
    turn = state["turn"] + 1
    fresh = {"turn": turn, "source_sd": state["source_sd"],
             "source_turn": state["source_turn"]}
    if _tmp_veto(text, tmp_resolver):
        fresh.update(source_sd=None, source_turn=None)
        return fresh, None, "TMP_AMBIGUITY_VETO"
    labels = _labels(native)
    hits = _mentions(text, labels)
    # For explicit v0.12 queries, "Xの根拠は?" often contains both
    # source label X and the Evidence target label "根拠".
    # Keep only the exactly specified subject; do not treat the target
    # label as a competing topic.
    from ski_auto_route_v012 import _strict_subject
    explicit_subject = _strict_subject(text)
    if explicit_subject is not None:
        hits = {sid for sid, label in labels.items()
                if label == explicit_subject}
    if _is_followup(text):
        # "根拠" can itself be a display name for the target Evidence
        # node. Never let that target label erase the previous source.
        source_ids = {e["source"] for e in converted["relations"]
                      if e["kind"] == "SUPPORTED_BY" and e["state"] == "APPROVED"}
        hits.intersection_update(source_ids)
    if len(hits) > 1:
        fresh.update(source_sd=None, source_turn=None)
        return fresh, None, "AMBIGUOUS_TOPIC"
    if len(hits) == 1:
        sid = next(iter(hits))
        # An explicit topic resets context. Only a source having a unique
        # mapped Evidence relation can establish eligible continuity.
        if _target(sid, converted):
            fresh.update(source_sd=sid, source_turn=turn)
            return fresh, None, "EXPLICIT_TOPIC"
        fresh.update(source_sd=None, source_turn=None)
        return fresh, None, "UNMAPPED_TOPIC"
    source = fresh["source_sd"]
    origin = fresh["source_turn"]
    if source is None or origin is None or turn - origin > MAX_GAP:
        fresh.update(source_sd=None, source_turn=None)
        return fresh, None, "NO_RECENT_CONTEXT"
    if not _is_followup(text):
        return fresh, None, "NON_REFERENCE_TURN"
    target = _target(source, converted)
    if target is None:
        fresh.update(source_sd=None, source_turn=None)
        return fresh, None, "NO_UNIQUE_EVIDENCE_TARGET"
    return fresh, {
        "source_sd": source, "target_sd": target, "question": text,
        "route": "V013_SINGLE_RECENT_TOPIC_CONTEXT",
        "source_turn": origin,
    }, "CONTEXT_RESOLVED"


def _load_tmp_resolver(tmp_dir):
    path = Path(tmp_dir).resolve() / "context_intent_resolver_v033.py"
    if not path.is_file():
        raise ValueError("TMP_CONTEXT_RESOLVER_NOT_FOUND")
    name = "llm_tmp_context_intent_resolver_v033_runtime"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ValueError("INVALID_TMP_CONTEXT_MODULE")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(name, None)
            raise
    # Independent, empty TMP context: use only multi-topic veto,
    # never inherit an unverified subject from the resolver.
    return lambda text: module.resolve(text, module.TopicContext(), 0)


def context_route(text, state, *, environ=None, executor=None):
    """Return (next state, diagnostic or None), caller owns the state."""
    env = os.environ if environ is None else environ
    if text == "/reset":
        return empty_context(), None
    if (env.get("LLM_CHA_SKI_ENABLED") != "1" or
            env.get("LLM_CHA_SKI_AUTO_ENABLED") != "1" or
            env.get("LLM_CHA_SKI_CONTEXT_ENABLED") != "1" or
            not _text(text)):
        return dict(state), None
    try:
        from ski_runtime_v011 import _required_directory, execute_ski_query
        from ski_auto_route_v012 import _strict_subject
        bridge = _required_directory(
            "LLM_CHA_SKI_BRIDGE_DIR", env.get("LLM_CHA_SKI_BRIDGE_DIR", ""),
            "adapters/llm_tmp_native_v09.py")
        tmp = _required_directory(
            "LLM_CHA_SKI_TMP_DIR", env.get("LLM_CHA_SKI_TMP_DIR", ""),
            "context_intent_resolver_v033.py")
        predicate = env.get("LLM_CHA_SKI_PREDICATE", "")
        if not predicate:
            return empty_context(), None
        if str(bridge) not in sys.path:
            sys.path.insert(0, str(bridge))
        from adapters.llm_tmp_native_v09 import read_native, convert_file
        native_path = env.get("LLM_CHA_SKI_NATIVE", "")
        data, fingerprint = read_native(native_path)
        converted, report = convert_file(
            native_path, tmp, supported_by_predicates=(predicate,))
        if fingerprint != report["native_file_sha256"]:
            raise ValueError("NATIVE_SNAPSHOT_CHANGED")
        resolver = _load_tmp_resolver(tmp)
        updated, request, reason = next_context(
            text, state, data, converted, tmp_resolver=resolver)
        if request is None:
            return updated, None
        if _strict_subject(text) is not None:
            return updated, None  # v0.12 explicit routing retains precedence.
        run = executor or execute_ski_query
        result = run(
            request, bridge_dir=str(bridge), tmp_dir=str(tmp),
            native_path=native_path, predicate=predicate)
        if (not isinstance(result, dict)
                or result.get("status") not in ("FOUND", "NOT_FOUND",
                                               "UNKNOWN_NODE", "LIMIT_REACHED")
                or result.get("verified_fact") is not False
                or result.get("human_approved") is not False
                or result.get("llm_inference_invoked") is not False
                or result.get("request_message_id") != result.get("response_to_message_id")):
            raise ValueError("INVALID_CONTEXT_SKI_DIAGNOSTIC")
        return updated, {
            "kind": "SKI_CONTEXT_DIAGNOSTIC",
            "status": result["status"],
            "message": result["message"],
            "verified_fact": False,
            "allow_model_context": False,
            "source_turn": request["source_turn"],
        }
    except (ValueError, OSError, ImportError, RuntimeError, KeyError, TypeError):
        # Do not use stale context when a configured integration fails.
        return empty_context(), {
            "kind": "SKI_CONTEXT_DIAGNOSTIC",
            "status": "ERROR",
            "message": "会話文脈を検証できませんでした。根拠を回答・学習に使用していません。",
            "verified_fact": False, "allow_model_context": False,
        }


def display_context_diagnostic(result, *, printer=print):
    if result is None:
        return False
    printer("AI> 【SKI文脈照会・事実未検証】" + result["message"])
    printer("[ski_context_status=" + result["status"] +
            ", route=SKI_CONTEXT_DIAGNOSTIC_ONLY]")
    printer()
    return True
