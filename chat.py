# chat.py
#
# Interactive chat interface for the current LLM_TRY conversational checkpoint.
# Defaults to the v9.4 Nagato SFT model used by the v10.x stable baseline.
#
# v1.5.12 additions:
#   - conservative chat-level Unknown rejection
#   - multiple probe generations
#   - token-confidence / response-agreement checks
#   - malformed / repetitive output detection
#   - fallback response: "未学習です"
#
# Note:
# The v1.4.32/v1.5.1 semantic risk predictors are contrast-routing specific.
# They cannot be applied directly to arbitrary chat prompts.  This file uses
# a chat-level conservative rejection gate inspired by the same selective
# prediction principle.

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
import json
import os
import hashlib
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from typing import List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat_conversation_bridge_v0506 import ConversationBridge
from context_aware_validation_v0507 import grounded as cha_topic_grounded, topic_for as cha_topic_for, resolve_context as cha_resolve_context
from user_context_recovery_v0508 import UserContext
from interactive_unknown_learning_v0510 import UnknownTeaching, concept_from
from truth_aware_teaching_retrieval_v0511 import review as cha_teaching_review
from definition_grounding_v05111 import definition_grounded as cha_definition_grounded
from knowledge_candidate_review_v0512 import inspect as cha_review_inspect, approve as cha_review_approve
from usage_confidence_v0513 import update as cha_usage_update, summary as cha_usage_summary, FeedbackSession, classify_feedback
from correction_learning_v0515 import CorrectionSession
from unknown_term_detection_v0516 import probe as cha_unknown_term_probe
from wikipedia_acquisition_v0517 import lookup as cha_wikipedia_lookup
from wiki_grounded_fallback_v05172 import grounded_reply as cha_wiki_grounded_reply
from persona_wiki_grounding_v0519 import respond as cha_persona_wiki_respond
from wiki_persona_multiturn_v0520 import WikiConversation
from wiki_evidence_expansion_v0521 import expand as cha_expand_wiki_evidence
from wiki_semantic_memory_bridge_v0525 import compare_store as cha_wiki_compare_store
from wiki_multi_article_discovery_v0526 import discover as cha_wiki_discover
from wiki_multihop_runtime_v0529 import probe as cha_wiki_multihop_probe
from wiki_causal_diagnostics_v0530 import diagnose as cha_wiki_causal_diagnose
from wiki_partial_means_v0533 import partial_why as cha_wiki_partial_why
from wiki_relation_tiers_v0534 import assess_why as cha_wiki_relation_assess
from wiki_relation_alignment_v0535 import align as cha_wiki_relation_align
from wiki_multi_evidence_alignment_v0536 import analyze as cha_wiki_multi_evidence_analyze
from wiki_extraction_coverage_v0538 import summarize as cha_wiki_coverage_summary
from wiki_retry_v0539 import retry as cha_wiki_retry
from wiki_answer_assessment_v0540 import assess as cha_wiki_answer_assess
from wiki_conversational_repair_v0541 import render as cha_wiki_conversational_render
from persona_priority_v0547 import apply as cha_persona_wiki_repair
from unified_persona_controller_v0548 import status as cha_persona_status, audit as cha_persona_audit
from persona_conversation_router_v0549 import respond as cha_persona_sharing_respond
from persona_context_v0550 import PersonaContext
from persona_auto_wiki_v0556 import enrich as cha_persona_auto_wiki_enrich
from unknown_wiki_fallback_v0557 import fallback as cha_unknown_wiki_fallback
from persona_wiki_topic_followup_v0558 import followup as cha_wiki_topic_followup
from wiki_more_details_v0560 import more as cha_wiki_more_details
from wiki_evidence_session_v0562 import EvidenceSession as ChaWikiEvidenceSession
from wiki_evidence_continuation_v0564 import EvidenceContinuation as ChaWikiEvidenceContinuation
from answer_quality_gate_v0542 import evaluate as cha_answer_quality_evaluate
from semantic_proposition_v1090 import (
    add_statement as add_semantic_proposition_statement,
    compose_subject as compose_semantic_proposition_subject,
    load_propositions as load_semantic_propositions,
)
from unified_semantic_bridge_v1090 import (
    sync_all_propositions,
    sync_subject_from_propositions,
)
from subject_keyed_proposition_v1090 import (
    compose_subject_from_index,
    load_subject_index,
    subject_index_dict,
    subject_mapping,
    sync_subject_index,
)
from typed_subject_proposition_v10100 import (
    load_typed_index,
    sync_typed_index,
    typed_index_dict,
    typed_query_lookup,
    typed_subject_mapping,
    typed_subject_rows,
)
from internalized_knowledge_v10100 import (
    internalized_record_for_focus,
    load_internalized_concepts,
    load_internalized_records,
)
from knowledge_state_resolver_v10100 import (
    resolve_knowledge_state,
)
from knowledge_state_dispatcher_v10101 import (
    dispatch_knowledge_state,
)
from truth_state_v10103 import (
    TRUTH_STATES,
    effective_truth_record,
    load_truth_records,
    upsert_truth_record,
)
from truth_aware_dispatch_v10103 import (
    apply_truth_policy,
)
from semantic_knowledge_architecture_v10110 import (
    SemanticKnowledgeArchitecture,
    SemanticKnowledgeConfig,
)
from semantic_knowledge_snapshot_v10111 import (
    snapshot_semantic_knowledge,
)
from knowledge_promotion_v10114 import (
    pending_knowledge_requests,
    promote_knowledge,
)
from candidate_repair_quality_v10123 import (
    RepairQualityProbe,
    append_repair_quality_audit,
)
from batch_repair_preservation_v10121 import (
    PreservationProbe,
    append_preservation_audit,
    protected_internalized_records,
)
from internalized_verification_v10119 import (
    active_verifications,
    batch_repair_plan,
    mark_batch_retrain,
    mark_retrain as mark_internalized_verification_retrain,
    mark_verified as mark_internalized_verification_verified,
    upsert_unstable as upsert_internalized_unstable,
    verification_summary,
)
from knowledge_queue_lifecycle_v10115 import (
    consolidate_legacy_resolved,
    lifecycle_summary,
    mark_concept_verified,
    revoke_concept_verification,
)
from retrieval_first_runtime_v1012161 import (
    resolve_subject as retrieval_first_resolve_subject,
    truth_allows_direct_retrieval,
)
from semantic_sleep_learning_v10131 import (
    DEFAULT_NAGATO_SEMANTIC_MEMORY,
    bootstrap_nagato_semantic_memory,
    prepare_semantic_sleep_pairs,
    semantic_sleep_status,
)
from modifier_condition_normalization_v10160 import (
    normalize_modifier_condition_text,
)
from conditional_semantic_v10161 import (
    DEFAULT_CONDITIONAL_CANDIDATE_QUEUE,
    add_conditional_statement,
    answer_conditional_query,
    approve_conditional_candidate,
    conditional_semantic_status,
    load_conditional_propositions,
    parse_conditional_query,
    parse_conditional_statement,
    pending_conditional_candidates,
    prepare_conditional_sleep_pairs,
    queue_conditional_candidate,
)


DEFAULT_TOKENIZER = "model/tokenizer-v0.7-bpe.json"
DEFAULT_MODEL = "model/model-llm-try-nagato-chat-v94.pt"
DEFAULT_PREVIOUS_ONLINE_MODEL = "model/model-gpu-v1.6.1-online.pt"
DEFAULT_CONCEPT_CALIBRATION = "model/concept-calibration-v1512.pt"
DEFAULT_LEARNING_LOG = "data/chat_history.jsonl"
DEFAULT_LEARNING_STATE = "data/chat_learning_state.json"
DEFAULT_TEACHING_QUEUE = "data/teaching_queue.jsonl"
DEFAULT_KNOWLEDGE_QUEUE = "data/knowledge_queue.jsonl"
DEFAULT_GATE_REVIEW_QUEUE = "data/gate_review_queue.jsonl"
DEFAULT_ONLINE_MODEL = "model/model-gpu-v1.6.2-online.pt"
DEFAULT_ONLINE_TRAINER = "online_train.py"
DEFAULT_RAW_KNOWLEDGE_CORPUS = "data/data-nagato.txt"
DEFAULT_SEMANTIC_KNOWLEDGE = "data/unified_semantic_memory_v1090.jsonl"
DEFAULT_PROPOSITION_STORE = "data/semantic_propositions_v1090.jsonl"
DEFAULT_CONDITIONAL_PROPOSITION_STORE = "data/conditional_propositions_v10161.jsonl"
DEFAULT_CONDITIONAL_CANDIDATES = DEFAULT_CONDITIONAL_CANDIDATE_QUEUE
DEFAULT_SUBJECT_INDEX = "data/subject_keyed_propositions_v1090.jsonl"
DEFAULT_TYPED_SUBJECT_INDEX = "data/typed_subject_propositions_v10100.jsonl"
DEFAULT_CORPUS_MEMORY = "data/subject_keyed_corpus_memory_v101216.jsonl"
DEFAULT_TRUTH_STORE = "data/truth_state_v10103.jsonl"
DEFAULT_INTERNALIZED_VERIFICATION = (
    "data/internalized_verification_v10119.jsonl"
)
DEFAULT_BATCH_PRESERVATION_AUDIT = (
    "data/batch_preservation_v10121.jsonl"
)
DEFAULT_CANDIDATE_REPAIR_QUALITY_AUDIT = (
    "data/candidate_repair_quality_v10123.jsonl"
)

USER_PREFIX = "人: "
AI_PREFIX = "AI: "
UNKNOWN_REPLY = "未学習です"

PROJECT_ROOT = Path(__file__).resolve().parent
SIBLING_LLM_GPU_ROOT = PROJECT_ROOT.parent / "LLM_GPU"


def resolve_runtime_path(value: str | Path) -> Path:
    """Resolve runtime assets robustly from LLM_TRY or sibling LLM_GPU.

    Resolution order for relative paths:
      1. current working directory (backward compatible)
      2. LLM_TRY repository root
      3. sibling ../LLM_GPU repository (for shared model assets)
    """
    raw = Path(value)
    if raw.is_absolute():
        return raw

    candidates = [raw, PROJECT_ROOT / raw]
    if raw.parts and raw.parts[0] == "model":
        candidates.append(SIBLING_LLM_GPU_ROOT / raw)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return (PROJECT_ROOT / raw).resolve()


@dataclass
class GenerationResult:
    text: str
    token_count: int
    mean_confidence: float
    min_confidence: float
    mean_top2_margin: float


@dataclass(frozen=True)
class CompositeFidelityResult:
    semantic_similarity: float
    lexical_coverage: float
    required_coverage: float
    contradiction: bool
    required_terms: tuple[str, ...] = ()
    matched_terms: tuple[str, ...] = ()

    @property
    def missing_terms(self) -> tuple[str, ...]:
        matched = set(self.matched_terms)
        return tuple(
            term for term in self.required_terms
            if term not in matched
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the current LLM_GPU conversational model."
    )
    parser.add_argument("--approved-qa-overlay", default=None,
        help="Opt-in approved exact-QA overlay (read-only JSONL); disabled by default.")
    parser.add_argument("--cha-memory-root", default="data/conversation_memory_local",
        help="Opt-in v0.5.6 conversation store; use /cha-start to record accepted turns.")
    parser.add_argument("--tokenizer", default=DEFAULT_TOKENIZER)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--concept-calibration",
        default=DEFAULT_CONCEPT_CALIBRATION,
        help=(
            "Optional v1.5.12 concept calibration checkpoint. "
            "Uses train-centroid calibrated space when available."
        ),
    )
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=0.45)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument("--learning-log", default=DEFAULT_LEARNING_LOG)
    parser.add_argument("--learning-state", default=DEFAULT_LEARNING_STATE)
    parser.add_argument("--teaching-queue", default=DEFAULT_TEACHING_QUEUE)
    parser.add_argument("--knowledge-queue", default=DEFAULT_KNOWLEDGE_QUEUE)
    parser.add_argument("--gate-review-queue", default=DEFAULT_GATE_REVIEW_QUEUE)
    parser.add_argument(
        "--propositions",
        default=DEFAULT_PROPOSITION_STORE,
        help="Persistent atomic semantic proposition store.",
    )
    parser.add_argument(
        "--conditional-propositions",
        default=DEFAULT_CONDITIONAL_PROPOSITION_STORE,
        help="Persistent v10.16.1 conditional semantic proposition store.",
    )
    parser.add_argument(
        "--conditional-candidates",
        default=DEFAULT_CONDITIONAL_CANDIDATES,
        help="Pending v10.16.3 conditional proposition candidate queue.",
    )
    parser.add_argument(
        "--subject-index",
        default=DEFAULT_SUBJECT_INDEX,
        help="Derived subject-keyed semantic proposition index.",
    )
    parser.add_argument(
        "--typed-subject-index",
        default=DEFAULT_TYPED_SUBJECT_INDEX,
        help="Derived Subject => Predicate Type => Statement index.",
    )
    parser.add_argument(
        "--corpus-memory",
        default=DEFAULT_CORPUS_MEMORY,
        help="v10.12.16 subject-keyed corpus memory used by retrieval-first runtime.",
    )
    parser.add_argument(
        "--truth-store",
        default=DEFAULT_TRUTH_STORE,
        help="Persistent concept truth-state overlay.",
    )
    parser.add_argument(
        "--internalized-verification",
        default=DEFAULT_INTERNALIZED_VERIFICATION,
        help="Persistent INTERNALIZED_UNSTABLE verification loop store.",
    )
    parser.add_argument(
        "--batch-preservation-audit",
        default=DEFAULT_BATCH_PRESERVATION_AUDIT,
        help="Persistent v10.12.1 batch preservation audit log.",
    )
    parser.add_argument(
        "--batch-preservation-force-fail",
        action="store_true",
        help=(
            "TEST ONLY: force candidate rollback after preservation "
            "evaluation to validate v10.12.2 rollback behavior."
        ),
    )
    parser.add_argument(
        "--candidate-repair-quality-audit",
        default=DEFAULT_CANDIDATE_REPAIR_QUALITY_AUDIT,
        help="Persistent v10.12.3 candidate repair-quality audit log.",
    )
    parser.add_argument(
        "--candidate-repair-force-fail",
        action="store_true",
        help=(
            "TEST ONLY: force Repair Quality Gate FAIL after evaluation "
            "to validate v10.12.3 rollback behavior."
        ),
    )
    parser.add_argument(
        "--learn",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Start with accepted-turn learning capture enabled.",
    )
    parser.add_argument("--online-trainer", default=DEFAULT_ONLINE_TRAINER)
    parser.add_argument("--online-output", default=DEFAULT_ONLINE_MODEL)
    parser.add_argument(
        "--history-turns",
        type=int,
        default=3,
        help="Number of previous turns included in the prompt.",
    )

    # Conservative selective-prediction gate.
    parser.add_argument(
        "--unknown-rejection",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable conservative chat-level Unknown rejection.",
    )
    parser.add_argument(
        "--probe-count",
        type=int,
        default=3,
        help="Number of generation probes used for agreement.",
    )
    parser.add_argument(
        "--probe-temperature",
        type=float,
        default=0.30,
        help="Sampling temperature for reliability probes.",
    )
    parser.add_argument(
        "--probe-top-k",
        type=int,
        default=10,
        help="Top-k used for reliability probes.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.18,
        help="Minimum mean selected-token probability.",
    )
    parser.add_argument(
        "--min-token-confidence",
        type=float,
        default=0.02,
        help="Minimum probability allowed for any generated token.",
    )
    parser.add_argument(
        "--min-mean-margin",
        type=float,
        default=0.01,
        help="Minimum mean top1-vs-top2 probability margin.",
    )
    parser.add_argument(
        "--min-agreement",
        type=float,
        default=0.35,
        help="Minimum mean textual agreement between probe responses.",
    )
    parser.add_argument(
        "--min-semantic-agreement",
        type=float,
        default=0.82,
        help="Minimum mean cosine similarity between probe response vectors.",
    )
    parser.add_argument(
        "--min-internalized-fidelity",
        type=float,
        default=0.90,
        help="Minimum teacher semantic similarity for INTERNALIZED output.",
    )
    parser.add_argument(
        "--min-internalized-lexical-coverage",
        type=float,
        default=0.45,
        help="Minimum teacher character-bigram coverage.",
    )
    parser.add_argument(
        "--min-internalized-required-coverage",
        type=float,
        default=0.50,
        help="Minimum required-content term coverage.",
    )
    parser.add_argument(
        "--semantic-consistency",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable question-answer semantic consistency checks.",
    )
    parser.add_argument(
        "--history-contamination-margin",
        type=float,
        default=0.05,
        help=(
            "Reject if the answer is closer to a previous user turn than "
            "the current turn by this cosine-similarity margin."
        ),
    )
    parser.add_argument(
        "--show-risk",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show confidence/agreement diagnostics.",
    )
    return parser.parse_args()




def normalize_pair_text(text: str) -> str:
    return " ".join(text.strip().split())


def pair_fingerprint(user: str, answer: str) -> str:
    payload = normalize_pair_text(user) + "\n" + normalize_pair_text(answer)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def trusted_fingerprints_from_log(path: Path) -> set[str]:
    fingerprints: set[str] = set()
    if not path.exists():
        return fingerprints

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        source = str(row.get("source", ""))
        if source not in ("chat-manual", "chat-approved"):
            continue
        user = str(row.get("user", "")).strip()
        answer = str(row.get("assistant", "")).strip()
        if user and answer:
            fingerprints.add(pair_fingerprint(user, answer))
    return fingerprints


def initialize_learning_state_if_missing(
    state_path: Path,
    learning_log: Path,
    assume_existing_trained: bool,
) -> int:
    if state_path.exists():
        return 0

    fingerprints = (
        trusted_fingerprints_from_log(learning_log)
        if assume_existing_trained
        else set()
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "v1.6.2",
        "trained_fingerprints": sorted(fingerprints),
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(fingerprints)


def mark_pair_for_retraining(
    state_path: Path,
    user_text: str,
    assistant_text: str,
) -> bool:
    if not state_path.exists():
        return False

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    fingerprints = {
        str(x) for x in data.get("trained_fingerprints", [])
    }
    fp = pair_fingerprint(user_text, assistant_text)
    if fp not in fingerprints:
        return False

    fingerprints.remove(fp)
    data["trained_fingerprints"] = sorted(fingerprints)
    data["version"] = data.get("version", "v1.6.2")
    state_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


def active_internalized_verification_record(
    verification_path: Path,
    learning_log: Path,
    learning_state: Path,
    focus: str,
):
    """Return CURRENT internalized record for an active repair task.

    This is used only for post-training verification. It lets a repaired
    INTERNALIZED concept be tested against model weights even when a higher-
    priority TYPED/UNIFIED retrieval source exists.
    """
    target = str(focus).strip().lower()
    if not target:
        return None

    rows = active_verifications(verification_path)
    active_fingerprints = {
        str(row.get("fingerprint", ""))
        for row in rows
        if str(row.get("concept", "")).strip().lower() == target
    }
    if not active_fingerprints:
        return None

    records = load_internalized_records(
        learning_log,
        learning_state,
    )
    for record in reversed(records):
        if (
            record.concept.strip().lower() == target
            and record.fingerprint in active_fingerprints
        ):
            return record
    return None


def choose_startup_model(
    requested_model: str,
    online_output: str = DEFAULT_ONLINE_MODEL,
    learning_state: str = DEFAULT_LEARNING_STATE,
) -> Path:
    """Choose the adaptive checkpoint only when training state proves it exists.

    Explicit --model always wins.  For the default v10.x startup, a local
    online checkpoint is resumed only when chat_learning_state.json records at
    least one consumed trusted fingerprint.  This avoids accidentally loading
    an unrelated legacy online checkpoint.
    """
    requested = resolve_runtime_path(requested_model)
    if requested_model != DEFAULT_MODEL:
        return requested

    state_path = resolve_runtime_path(learning_state)
    online_path = resolve_runtime_path(online_output)
    if not state_path.exists() or not online_path.exists():
        return requested

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return requested

    fingerprints = state.get("trained_fingerprints", [])
    if isinstance(fingerprints, list) and fingerprints:
        return online_path

    return requested

def append_learning_pair(
    path: Path,
    user_text: str,
    assistant_text: str,
    source: str = "chat-auto",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "user": user_text,
        "assistant": assistant_text,
        "source": source,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_route_record(
    path: Path,
    resolution: str,
    action: str,
    user_text: str,
    candidate_answer: str,
    reason: str,
) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)

    fingerprint = pair_fingerprint(
        resolution + "\n" + reason,
        user_text,
    )

    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                old = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if old.get("fingerprint") == fingerprint:
                return False

    row = {
        "fingerprint": fingerprint,
        "resolution": resolution,
        "action": action,
        "user": user_text,
        "candidate_answer": candidate_answer,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True


def route_resolution_action(
    args: argparse.Namespace,
    resolution: str,
    action: str,
    user_text: str,
    candidate_answer: str,
    reason: str,
) -> str:
    if resolution == "LEARNING_GAP":
        path = Path(args.teaching_queue)
        added = append_route_record(
            path, resolution, action, user_text, candidate_answer, reason
        )
        return (
            f"queued teaching candidate -> {path}"
            if added else
            f"teaching candidate already queued -> {path}"
        )

    if resolution == "UNKNOWN_KNOWLEDGE":
        path = Path(args.knowledge_queue)
        added = append_route_record(
            path, resolution, action, user_text, candidate_answer, reason
        )
        return (
            f"queued knowledge request -> {path}"
            if added else
            f"knowledge request already queued -> {path}"
        )

    if resolution == "GATE_REVIEW":
        path = Path(args.gate_review_queue)
        added = append_route_record(
            path, resolution, action, user_text, candidate_answer, reason
        )
        return (
            f"queued gate review -> {path}"
            if added else
            f"gate review already queued -> {path}"
        )

    if resolution == "INPUT_REJECT":
        return "request rephrase"

    return "normal response"


def validate_teaching_answer(
    question: str,
    corrected: str,
) -> tuple[bool, str]:
    intent, slots = classify_intent_and_slots(question)

    if intent == "definition" and slots:
        slot = slots[0]
        if definition_is_echo_only(slot, corrected):
            return (
                False,
                "definition teaching answer is only an echo; "
                "teach category/function/property, not only a synonym",
            )
        if definition_is_uninformative(slot, corrected):
            return (
                False,
                "definition teaching answer is uninformative; "
                "include category, function, or distinguishing property",
            )

    concept_ok, concept_reason = answer_concept_consistency(
        question,
        corrected,
    )
    if not concept_ok:
        return False, concept_reason

    return True, "teaching answer accepted"


def teaching_hint(question: str) -> str:
    focus = extract_definition_focus(question)
    if not focus:
        return "Provide a concrete, correct answer with the key concept and function."

    key = focus.lower()
    examples = {
        "ai": "AIは人間の知的な処理をコンピュータで実現する技術です。",
        "人工知能": "人工知能は人間の知的な処理をコンピュータで実現する技術です。",
        "cpu": "CPUは汎用的な命令実行と制御処理を担当する中央処理装置です。",
        "gpu": "GPUは多数の演算を並列に処理するプロセッサです。",
        "llm": "LLMは大量のテキストから学習し、言語を扱う大規模言語モデルです。",
        "大規模言語モデル": "大規模言語モデルは大量のテキストから学習し、言語を扱うモデルです。",
    }
    return examples.get(
        key,
        f"{focus}について、分類・機能・特徴のいずれかを含む説明を教えてください。",
    )


def learning_log_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def trusted_pairs_from_log(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if not path.exists():
        return pairs

    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if str(row.get("source", "")) not in (
            "chat-manual", "chat-approved", "chat-recovery"
        ):
            continue
        user = str(row.get("user", "")).strip()
        answer = str(row.get("assistant", "")).strip()
        if not user or not answer:
            continue
        fp = pair_fingerprint(user, answer)
        if fp in seen:
            continue
        seen.add(fp)
        pairs.append((user, answer))
    return pairs


def trained_known_concepts(
    learning_log: Path,
    learning_state: Path,
) -> set[str]:
    """Return definition focuses from trusted pairs already consumed by /train.

    A concept is promoted only when the exact trusted pair fingerprint appears
    in the training state. Merely teaching a pair is not enough.
    """
    if not learning_log.exists() or not learning_state.exists():
        return set()

    try:
        state = json.loads(learning_state.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()

    trained = {str(x) for x in state.get("trained_fingerprints", [])}
    if not trained:
        return set()

    concepts: set[str] = set()
    for raw in learning_log.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue

        source = str(row.get("source", ""))
        if source not in ("chat-manual", "chat-approved", "chat-recovery"):
            continue

        user = str(row.get("user", "")).strip()
        answer = str(row.get("assistant", "")).strip()
        if not user or not answer:
            continue

        if pair_fingerprint(user, answer) not in trained:
            continue

        focus = extract_concept_query_focus(user)
        if not focus:
            focus = extract_definition_focus(user) or ""
        if focus:
            concepts.add(focus.lower())

    return concepts


def recover_forgotten_pairs_from_queue(
    teaching_queue: Path,
    learning_log: Path,
    learning_state: Path,
    target_question: str | None = None,
) -> tuple[int, int, int, list[tuple[str, str, str]]]:
    if not teaching_queue.exists():
        return 0, 0, 0, []

    queued_questions: list[str] = []
    seen_questions: set[str] = set()

    for raw in teaching_queue.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if str(row.get("resolution", "")) != "LEARNING_GAP":
            continue
        if str(row.get("status", "pending")) == "resolved":
            continue

        question = str(row.get("user", "")).strip()
        if target_question is not None:
            if (
                normalize_pair_text(question).lower()
                != normalize_pair_text(target_question).lower()
            ):
                continue
        qn = normalize_pair_text(question).lower()
        if question and qn not in seen_questions:
            seen_questions.add(qn)
            queued_questions.append(question)

    if not queued_questions:
        return 0, 0, 0, []

    trusted_pairs = trusted_pairs_from_log(learning_log)
    reactivated = 0
    matched = 0
    rejected_old_teachers = 0
    selections: list[tuple[str, str, str]] = []

    for question in queued_questions:
        qn = normalize_pair_text(question).lower()
        queued_intent, queued_slots = classify_intent_and_slots(question)
        queued_focus = (
            _clean_slot(queued_slots[0]).lower()
            if queued_intent == "definition" and queued_slots
            else None
        )

        best: tuple[str, str] | None = None
        best_rank = -1.0

        for user, answer in trusted_pairs:
            trusted_intent, trusted_slots = classify_intent_and_slots(user)
            trusted_focus = (
                _clean_slot(trusted_slots[0]).lower()
                if trusted_intent == "definition" and trusted_slots
                else None
            )

            if queued_intent == "definition":
                if trusted_intent != "definition":
                    continue
                if queued_focus != trusted_focus:
                    continue

            un = normalize_pair_text(user).lower()
            similarity = response_similarity(qn, un)
            if qn == un:
                similarity = 1.0
            if similarity < 0.80:
                continue

            historical_ok, _ = validate_teaching_answer(user, answer)
            queued_ok, _ = validate_teaching_answer(question, answer)
            if not historical_ok or not queued_ok:
                rejected_old_teachers += 1
                continue

            informativeness = min(
                len(normalize_pair_text(answer)) / 200.0,
                0.20,
            )
            rank = similarity + informativeness
            if rank > best_rank:
                best_rank = rank
                best = (user, answer)

        if best is None:
            selections.append((question, "", "no valid trusted teacher"))
            continue

        matched += 1
        selections.append((question, best[1], f"trusted question={best[0]}"))
        if mark_pair_for_retraining(
            learning_state,
            best[0],
            best[1],
        ):
            append_learning_pair(
                learning_log,
                best[0],
                best[1],
                source="chat-recovery",
            )
            reactivated += 1

    return matched, reactivated, rejected_old_teachers, selections


def resolve_route_queue(
    queue_path: Path,
    question: str,
    resolution: str,
) -> int:
    """Mark matching routed work items resolved after trusted teaching."""
    if not queue_path.exists():
        return 0

    target = normalize_pair_text(question).lower()
    changed = 0
    rows: list[dict] = []

    for raw in queue_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue

        queued_question = normalize_pair_text(str(row.get("user", ""))).lower()
        if (
            str(row.get("resolution", "")) == resolution
            and queued_question == target
            and str(row.get("status", "pending")) != "resolved"
        ):
            row["status"] = "resolved"
            row["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            changed += 1

        rows.append(row)

    if changed:
        queue_path.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False) + "\n"
                for row in rows
            ),
            encoding="utf-8",
        )
    return changed


def resolve_teaching_queue(
    teaching_queue: Path,
    question: str,
) -> int:
    return resolve_route_queue(
        teaching_queue,
        question,
        "LEARNING_GAP",
    )


def run_online_training(
    args: argparse.Namespace,
    model_path: Path,
    *,
    output_path: Path | None = None,
    state_path: Path | None = None,
) -> Path | None:
    trainer = Path(args.online_trainer)
    learning_log = Path(args.learning_log)
    output = (
        Path(output_path)
        if output_path is not None
        else Path(args.online_output)
    )
    training_state = (
        Path(state_path)
        if state_path is not None
        else Path(args.learning_state)
    )

    if not trainer.exists():
        print(f"[online trainer not found: {trainer}]")
        return None
    if learning_log_count(learning_log) < 2:
        print("[need at least 2 learning pairs before /train]")
        return None

    cmd = [
        sys.executable,
        str(trainer),
        "--chat-data", str(learning_log),
        "--base-model", str(model_path),
        "--tokenizer", str(resolve_runtime_path(args.tokenizer)),
        "--output", str(output),
        "--state", str(training_state),
    ]
    print("[starting incremental training]")
    print(" ".join(cmd))
    completed = subprocess.run(cmd, check=False)
    if completed.returncode == 3:
        print("[no new trusted pairs; training skipped]")
        return None
    if completed.returncode != 0:
        print(f"[training failed: exit={completed.returncode}]")
        return None
    if not output.exists():
        print(f"[training finished but checkpoint not found: {output}]")
        return None
    return output

def batch_candidate_paths(
    output_path: Path,
    state_path: Path,
) -> tuple[Path, Path]:
    candidate_checkpoint = output_path.with_name(
        output_path.stem + ".candidate" + output_path.suffix
    )
    candidate_state = state_path.with_name(
        state_path.stem + ".candidate" + state_path.suffix
    )
    return candidate_checkpoint, candidate_state


def discard_batch_candidate(
    candidate_checkpoint: Path,
    candidate_state: Path,
) -> None:
    for path in (candidate_checkpoint, candidate_state):
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            print(f"[candidate cleanup warning: {path}: {exc}]")


def promote_batch_candidate(
    candidate_checkpoint: Path,
    candidate_state: Path,
    production_checkpoint: Path,
    production_state: Path,
) -> None:
    """Promote checkpoint/state together with rollback on partial failure."""
    production_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    production_state.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_backup = production_checkpoint.with_name(
        production_checkpoint.name + ".promotion-backup"
    )
    state_backup = production_state.with_name(
        production_state.name + ".promotion-backup"
    )
    for backup in (checkpoint_backup, state_backup):
        if backup.exists():
            backup.unlink()

    checkpoint_had_original = production_checkpoint.exists()
    state_had_original = production_state.exists()

    if checkpoint_had_original:
        shutil.copy2(production_checkpoint, checkpoint_backup)
    if state_had_original:
        shutil.copy2(production_state, state_backup)

    try:
        candidate_checkpoint.replace(production_checkpoint)
        candidate_state.replace(production_state)
    except Exception:
        # Restore both production files to the exact pre-promotion pair.
        if checkpoint_had_original and checkpoint_backup.exists():
            shutil.copy2(checkpoint_backup, production_checkpoint)
        elif not checkpoint_had_original and production_checkpoint.exists():
            production_checkpoint.unlink()

        if state_had_original and state_backup.exists():
            shutil.copy2(state_backup, production_state)
        elif not state_had_original and production_state.exists():
            production_state.unlink()
        raise
    finally:
        for backup in (checkpoint_backup, state_backup):
            try:
                if backup.exists():
                    backup.unlink()
            except OSError:
                pass


def _slot_overlap(a: list[str], b: list[str]) -> bool:
    aa = {x.lower() for x in a}
    bb = {x.lower() for x in b}
    return bool(aa & bb)


def select_relevant_history(
    history: List[Tuple[str, str]],
    user_text: str,
    history_turns: int,
) -> List[Tuple[str, str]]:
    """v1.5.5 minimal-context policy.

    definition  : no raw history
    comparison  : no raw history
    greeting    : at most one previous greeting
    general     : at most one highly similar previous user turn
    """
    if history_turns <= 0 or not history:
        return []

    current_intent, _ = classify_intent_and_slots(user_text)

    if current_intent in ("definition", "comparison"):
        return []

    if current_intent == "greeting":
        for old_user, old_ai in reversed(history):
            old_intent, _ = classify_intent_and_slots(old_user)
            if old_intent == "greeting":
                return [(old_user, old_ai)]
        return []

    # General question: keep only one closely related prior user turn.
    # Character bigram similarity is deliberately conservative and cheap.
    best: Tuple[str, str] | None = None
    best_score = 0.0
    for old_user, old_ai in history:
        score = response_similarity(user_text, old_user)
        if score > best_score:
            best_score = score
            best = (old_user, old_ai)

    if best is not None and best_score >= 0.55:
        return [best]

    return []


IDENTITY_QUERY_ALIASES = {
    "貴方は": "あなたは誰ですか",
    "あなたは": "あなたは誰ですか",
    "長門": "あなたは誰ですか",
    "長門有希": "あなたは誰ですか",
    "長門とは": "あなたは誰ですか",
    "長門有希とは": "あなたは誰ですか",
}


def normalize_identity_query(question: str) -> str:
    """Map short identity variants to the stable canonical identity prompt."""
    return IDENTITY_QUERY_ALIASES.get(question.strip(), question)


def build_prompt(
    history: List[Tuple[str, str]],
    user_text: str,
    history_turns: int,
) -> tuple[str, List[Tuple[str, str]]]:
    chunks: List[str] = []
    selected = select_relevant_history(
        history=history,
        user_text=user_text,
        history_turns=history_turns,
    )

    for old_user, old_ai in selected:
        chunks.append(
            f"{USER_PREFIX}{old_user}\n"
            f"{AI_PREFIX}{old_ai}\n"
        )

    chunks.append(f"{USER_PREFIX}{user_text}\n{AI_PREFIX}")
    return "".join(chunks), selected


def _clean_reply(reply: str) -> str:
    for marker in ("\n人:", "\nAI:", "\n"):
        if marker in reply:
            reply = reply.split(marker, 1)[0]
    return reply.strip()


@torch.no_grad()
def generate_reply(
    model: LanguageModel,
    tokenizer: Tokenizer,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    repetition_penalty: float,
    seed: int | None = None,
) -> GenerationResult:
    if seed is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    prompt_ids = tokenizer.encode(prompt, add_bos=True)
    generated = list(prompt_ids)
    response_ids: List[int] = []

    confidences: List[float] = []
    margins: List[float] = []

    model.eval()
    device = next(model.parameters()).device

    for _ in range(max_new_tokens):
        context = generated[-model.context_length:]
        x = torch.tensor(
            [context],
            dtype=torch.long,
            device=device,
        )

        raw_logits = model(x)[0, -1, :].clone()

        if repetition_penalty != 1.0:
            for token_id in set(response_ids):
                if 0 <= token_id < raw_logits.numel():
                    if raw_logits[token_id] >= 0:
                        raw_logits[token_id] /= repetition_penalty
                    else:
                        raw_logits[token_id] *= repetition_penalty

        # Confidence is always measured on the untempered model distribution.
        raw_probs = F.softmax(raw_logits, dim=-1)
        top2_values, _ = torch.topk(raw_probs, k=2)

        if temperature <= 0:
            next_id = int(torch.argmax(raw_logits).item())
        else:
            logits = raw_logits / temperature
            if 0 < top_k < logits.numel():
                values, indices = torch.topk(logits, top_k)
                probs = F.softmax(values, dim=-1)
                selected = torch.multinomial(probs, 1)
                next_id = int(indices[selected].item())
            else:
                probs = F.softmax(logits, dim=-1)
                next_id = int(torch.multinomial(probs, 1).item())

        if next_id == tokenizer.eos_id:
            break

        confidences.append(float(raw_probs[next_id].item()))
        margins.append(float((top2_values[0] - top2_values[1]).item()))

        generated.append(next_id)
        response_ids.append(next_id)

        decoded = tokenizer.decode(
            response_ids,
            skip_special_tokens=True,
        )
        if "\n" in decoded:
            break

    reply = tokenizer.decode(
        response_ids,
        skip_special_tokens=True,
    )
    reply = _clean_reply(reply)

    mean_conf = (
        sum(confidences) / len(confidences)
        if confidences else 0.0
    )
    min_conf = min(confidences) if confidences else 0.0
    mean_margin = (
        sum(margins) / len(margins)
        if margins else 0.0
    )

    return GenerationResult(
        text=reply,
        token_count=len(response_ids),
        mean_confidence=mean_conf,
        min_confidence=min_conf,
        mean_top2_margin=mean_margin,
    )


def _normalize_for_similarity(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[。、,.!?！？:：;；「」『』（）()\[\]{}]", "", text)
    return text


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    text = _normalize_for_similarity(text)
    if not text:
        return set()
    if len(text) < n:
        return {text}
    return {text[i:i+n] for i in range(len(text)-n+1)}


def response_similarity(a: str, b: str) -> float:
    aa = _char_ngrams(a)
    bb = _char_ngrams(b)
    if not aa and not bb:
        return 1.0
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def mean_pairwise_agreement(results: List[GenerationResult]) -> float:
    if len(results) < 2:
        return 1.0
    values: List[float] = []
    for i in range(len(results)):
        for j in range(i+1, len(results)):
            values.append(
                response_similarity(results[i].text, results[j].text)
            )
    return sum(values) / len(values) if values else 1.0


def malformed_or_unstable(text: str) -> bool:
    if not text:
        return True

    # Unicode replacement character is a strong malformed-output signal.
    if "�" in text:
        return True

    # Reject pathological character/token repetition.
    compact = _normalize_for_similarity(text)
    if len(compact) >= 8:
        for n in (1, 2, 3, 4):
            chunks = [
                compact[i:i+n]
                for i in range(0, len(compact)-n+1)
            ]
            if chunks:
                most = max(chunks.count(x) for x in set(chunks))
                if most / len(chunks) > 0.45:
                    return True

    return False


@torch.no_grad()
def semantic_vector(
    model: LanguageModel,
    tokenizer: Tokenizer,
    text: str,
    block_index: int = 4,
) -> torch.Tensor:
    """Mean pooled hidden representation at block5 (index 4)."""
    ids = tokenizer.encode(text, add_bos=True)
    if not ids:
        return torch.zeros(model.d_model, device=next(model.parameters()).device)

    ids = ids[-model.context_length:]
    device = next(model.parameters()).device
    x_ids = torch.tensor([ids], dtype=torch.long, device=device)

    x = model.embedding(x_ids)
    if model.position_embedding is not None:
        positions = torch.arange(x_ids.shape[1], device=device)
        x = x + model.position_embedding(positions).unsqueeze(0)

    last = min(block_index, len(model.blocks)-1)
    for i in range(last + 1):
        x = model.blocks[i](x)

    # Exclude BOS when possible.
    token_states = x[0, 1:, :] if x.shape[1] > 1 else x[0]
    v = token_states.mean(dim=0)
    return F.normalize(v, dim=0)


@torch.no_grad()
def mean_pairwise_semantic_agreement(
    model: LanguageModel,
    tokenizer: Tokenizer,
    results: List[GenerationResult],
) -> float:
    if len(results) < 2:
        return 1.0

    vectors = [
        semantic_vector(model, tokenizer, result.text)
        for result in results
    ]
    values: List[float] = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            values.append(float(torch.dot(vectors[i], vectors[j]).item()))
    return sum(values) / len(values) if values else 1.0


@torch.no_grad()
def internalized_teacher_fidelity(
    model: LanguageModel,
    tokenizer: Tokenizer,
    generated_answer: str,
    teacher_answer: str,
) -> float:
    if not generated_answer.strip() or not teacher_answer.strip():
        return 0.0
    generated_vector = semantic_vector(
        model,
        tokenizer,
        generated_answer,
    )
    teacher_vector = semantic_vector(
        model,
        tokenizer,
        teacher_answer,
    )
    return float(torch.dot(generated_vector, teacher_vector).item())


def _teacher_lexical_coverage(
    generated_answer: str,
    teacher_answer: str,
) -> float:
    teacher = _char_ngrams(teacher_answer, n=2)
    generated = _char_ngrams(generated_answer, n=2)
    if not teacher:
        return 0.0
    return len(teacher & generated) / len(teacher)


def _required_teacher_terms(
    teacher_answer: str,
    concept: str = "",
) -> tuple[str, ...]:
    text = _normalize_for_similarity(teacher_answer)
    concept_norm = _normalize_for_similarity(concept)
    if concept_norm and text.startswith(concept_norm):
        text = text[len(concept_norm):]
    text = re.sub(r"^(?:は|とは)", "", text)
    text = re.sub(r"(?:である|です|だ)$", "", text)

    parts = re.split(
        r"(?:を|に|で|が|は|と|して|する|行う|利用|ため|の)",
        text,
    )
    stop = {
        "もの", "こと", "ため", "これ", "それ",
        "ある", "いる", "なる", "できる",
    }
    terms: list[str] = []
    for part in parts:
        term = part.strip()
        if len(term) < 2 or term in stop:
            continue
        if term not in terms:
            terms.append(term)

    # Preserve the terminal category noun when it is informative.
    category_match = re.search(
        r"([一-龯々ァ-ヶーA-Za-z0-9]{2,12})(?:である|です|だ)$",
        teacher_answer.strip(),
    )
    if category_match:
        category = category_match.group(1)
        if (
            category != concept
            and category not in terms
            and len(category) >= 2
        ):
            terms.append(category)

    return tuple(terms[:8])


def _required_content_coverage(
    generated_answer: str,
    teacher_answer: str,
    concept: str = "",
) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
    required = _required_teacher_terms(
        teacher_answer,
        concept=concept,
    )
    if not required:
        return 1.0, (), ()
    generated_norm = _normalize_for_similarity(generated_answer)
    matched = tuple(
        term for term in required
        if _normalize_for_similarity(term) in generated_norm
    )
    return len(matched) / len(required), required, matched


def _polarity_contradiction(
    generated_answer: str,
    teacher_answer: str,
) -> bool:
    negative_patterns = (
        r"ではない", r"でない", r"しない", r"できない",
        r"行わない", r"利用しない", r"不可能", r"存在しない",
    )
    teacher_negative = any(
        re.search(pattern, teacher_answer)
        for pattern in negative_patterns
    )
    generated_negative = any(
        re.search(pattern, generated_answer)
        for pattern in negative_patterns
    )
    return teacher_negative != generated_negative


@torch.no_grad()
def composite_internalized_teacher_fidelity(
    model: LanguageModel,
    tokenizer: Tokenizer,
    generated_answer: str,
    teacher_answer: str,
    concept: str = "",
) -> CompositeFidelityResult:
    semantic = internalized_teacher_fidelity(
        model=model,
        tokenizer=tokenizer,
        generated_answer=generated_answer,
        teacher_answer=teacher_answer,
    )
    lexical = _teacher_lexical_coverage(
        generated_answer,
        teacher_answer,
    )
    required_coverage, required, matched = (
        _required_content_coverage(
            generated_answer,
            teacher_answer,
            concept=concept,
        )
    )
    contradiction = _polarity_contradiction(
        generated_answer,
        teacher_answer,
    )
    return CompositeFidelityResult(
        semantic_similarity=semantic,
        lexical_coverage=lexical,
        required_coverage=required_coverage,
        contradiction=contradiction,
        required_terms=required,
        matched_terms=matched,
    )


def apply_internalized_fidelity_policy(
    accepted: bool,
    fidelity: float,
    threshold: float,
) -> tuple[bool, str]:
    """Backward-compatible v10.11.7 single-score fidelity policy."""
    if not accepted:
        return False, ""
    if fidelity < threshold:
        return (
            False,
            (
                "internalized teacher fidelity "
                f"{fidelity:.3f} < {threshold:.3f}"
            ),
        )
    return True, "internalized teacher fidelity passed"


def apply_composite_internalized_fidelity_policy(
    accepted: bool,
    result: CompositeFidelityResult,
    *,
    semantic_threshold: float,
    lexical_threshold: float,
    required_threshold: float,
) -> tuple[bool, str]:
    failures: list[str] = []
    if result.semantic_similarity < semantic_threshold:
        failures.append(
            "semantic "
            f"{result.semantic_similarity:.3f} < {semantic_threshold:.3f}"
        )
    if result.lexical_coverage < lexical_threshold:
        failures.append(
            "lexical "
            f"{result.lexical_coverage:.3f} < {lexical_threshold:.3f}"
        )
    if result.required_coverage < required_threshold:
        failures.append(
            "required "
            f"{result.required_coverage:.3f} < {required_threshold:.3f}"
        )
    if result.contradiction:
        failures.append("contradiction detected")

    if failures:
        return False, "composite teacher fidelity: " + "; ".join(failures)
    if not accepted:
        return False, ""
    return True, "composite teacher fidelity passed"


SLOT_ALIASES = {
    "ai": ("ai", "人工知能", "artificial intelligence"),
    "人工知能": ("人工知能", "ai", "artificial intelligence"),
    "llm": ("llm", "大規模言語モデル", "large language model", "言語モデル"),
    "大規模言語モデル": ("大規模言語モデル", "llm", "large language model", "言語モデル"),
    "cpu": ("cpu", "中央処理装置", "central processing unit"),
    "gpu": ("gpu", "画像処理装置", "graphics processing unit"),
    "cuda": ("cuda",),
}


STRICT_SYNONYMS = {
    "ai": ("ai", "人工知能", "artificial intelligence"),
    "人工知能": ("人工知能", "ai", "artificial intelligence"),
    "llm": ("llm", "大規模言語モデル", "large language model"),
    "大規模言語モデル": ("大規模言語モデル", "llm", "large language model"),
    "cpu": ("cpu", "中央処理装置", "central processing unit"),
    "gpu": ("gpu", "graphics processing unit"),
    "cuda": ("cuda",),
}

DEFINITION_CATEGORIES = {
    "量子力学": ("理論", "微視的", "状態", "重ね合わせ", "測定"),
    "量子コンピュータ": ("量子", "計算", "量子ビット", "重ね合わせ"),
    "コンピュータ": ("計算機", "装置", "計算", "情報処理"),
    "semantic": ("意味", "意味論", "セマンティック"),
    "セマンティック": ("意味", "意味論", "セマンティック"),
    "llm": ("言語モデル",),
    "大規模言語モデル": ("言語モデル",),
    "gpu": ("画像処理装置", "プロセッサ", "処理装置"),
    "cpu": ("中央処理装置", "プロセッサ", "処理装置"),
    "ai": ("技術", "システム", "人工知能"),
    "人工知能": ("技術", "システム"),
}


def strict_synonyms(slot: str) -> tuple[str, ...]:
    key = slot.lower()
    return STRICT_SYNONYMS.get(
        key,
        STRICT_SYNONYMS.get(slot, (slot,)),
    )


def definition_categories(slot: str) -> tuple[str, ...]:
    key = slot.lower()
    return DEFINITION_CATEGORIES.get(
        key,
        DEFINITION_CATEGORIES.get(slot, ()),
    )


KNOWN_ENTITY_TOKENS = {
    "AI", "LLM", "CPU", "GPU", "CUDA",
}

CALIBRATION_PROJECTION = None
CALIBRATION_CENTROIDS = None
CALIBRATION_CONCEPTS: list[str] = []
CALIBRATION_INFO: dict = {}


class ChatConceptProjection(nn.Module):
    """Inference-only projection compatible with v1.5.12 checkpoints."""

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.net(x), dim=-1)


def load_concept_calibration(path: Path, device: torch.device) -> bool:
    global CALIBRATION_PROJECTION
    global CALIBRATION_CENTROIDS
    global CALIBRATION_CONCEPTS
    global CALIBRATION_INFO

    if not path.exists():
        CALIBRATION_PROJECTION = None
        CALIBRATION_CENTROIDS = None
        CALIBRATION_CONCEPTS = []
        CALIBRATION_INFO = {"loaded": False, "path": str(path)}
        return False

    ckpt = torch.load(str(path), map_location=device)

    if ckpt.get("centroid_source") != "train":
        raise ValueError(
            "Concept calibration rejected: centroid_source must be 'train'."
        )
    if ckpt.get("holdout_used_for_centroid", True):
        raise ValueError(
            "Concept calibration rejected: holdout must not be used for centroid fit."
        )

    projection = ChatConceptProjection(
        int(ckpt["input_dim"]),
        int(ckpt["hidden_dim"]),
        int(ckpt["output_dim"]),
    ).to(device)
    projection.load_state_dict(ckpt["projection_state"])
    projection.eval()

    CALIBRATION_PROJECTION = projection
    CALIBRATION_CENTROIDS = F.normalize(
        ckpt["centroids"].to(device), dim=-1
    )
    CALIBRATION_CONCEPTS = list(ckpt["concepts"])
    CALIBRATION_INFO = {
        "loaded": True,
        "path": str(path),
        "version": ckpt.get("version"),
        "evaluation_protocol": ckpt.get("evaluation_protocol"),
        "centroid_source": ckpt.get("centroid_source"),
        "holdout_used_for_centroid": ckpt.get("holdout_used_for_centroid"),
    }
    return True


CONCEPT_ANCHORS = {
    "AI": (
        "AIは人工知能です",
        "人工知能は人間の知的処理を機械で実現する技術です",
    ),
    "LLM": (
        "LLMは大規模言語モデルです",
        "大規模言語モデルは文章を理解し生成するモデルです",
    ),
    "CPU": (
        "CPUは中央処理装置です",
        "CPUは汎用的な命令実行と制御処理を担当します",
    ),
    "GPU": (
        "GPUは画像処理装置です",
        "GPUは大量の並列計算を得意とする演算装置です",
    ),
    "CUDA": (
        "CUDAはNVIDIAのGPU向け汎用計算技術です",
        "CUDAはGPUで計算を実行するための技術です",
    ),
}


@torch.no_grad()
def concept_prototype(
    model: LanguageModel,
    tokenizer: Tokenizer,
    concept: str,
) -> torch.Tensor | None:
    key = _clean_slot(concept).upper()
    anchors = CONCEPT_ANCHORS.get(key)
    if not anchors:
        return None
    vectors = [semantic_vector(model, tokenizer, text) for text in anchors]
    return F.normalize(torch.stack(vectors, dim=0).mean(dim=0), dim=0)


def answer_semantic_spans(answer: str) -> list[str]:
    spans = [
        s.strip()
        for s in re.split(r"[。！？!?、,]|(?:一方)|(?:対して)", answer)
        if s.strip()
    ]
    if answer.strip() and answer.strip() not in spans:
        spans.append(answer.strip())
    return spans


@torch.no_grad()
def concept_slot_match(
    model: LanguageModel,
    tokenizer: Tokenizer,
    slot: str,
    answer: str,
    min_similarity: float = 0.82,
    min_margin: float = 0.005,
) -> tuple[bool, float, float]:
    """Concept-aware fallback.

    v1.5.12 prefers the calibrated train-centroid space. If no compatible
    checkpoint is loaded, it falls back to the raw prototype method.
    """
    target = _clean_slot(slot).upper()

    if (
        CALIBRATION_PROJECTION is not None
        and CALIBRATION_CENTROIDS is not None
        and target in CALIBRATION_CONCEPTS
    ):
        target_idx = CALIBRATION_CONCEPTS.index(target)
        best_score = -1.0
        best_margin = -1.0

        for span in answer_semantic_spans(answer):
            raw = semantic_vector(model, tokenizer, span)
            z = CALIBRATION_PROJECTION(raw.unsqueeze(0))[0]
            sims = z @ CALIBRATION_CENTROIDS.T

            target_score = float(sims[target_idx].item())
            mask = torch.ones(
                len(CALIBRATION_CONCEPTS),
                dtype=torch.bool,
                device=sims.device,
            )
            mask[target_idx] = False
            other_best = float(sims[mask].max().item())
            margin = target_score - other_best

            if margin > best_margin:
                best_score = target_score
                best_margin = margin

        ok = best_margin >= 0.0
        return ok, best_score, best_margin

    target_proto = concept_prototype(model, tokenizer, target)
    if target_proto is None:
        return False, -1.0, -1.0

    other_protos = []
    for concept in CONCEPT_ANCHORS:
        if concept == target:
            continue
        p = concept_prototype(model, tokenizer, concept)
        if p is not None:
            other_protos.append(p)

    best_sim = -1.0
    best_margin = -1.0
    for span in answer_semantic_spans(answer):
        sv = semantic_vector(model, tokenizer, span)
        target_sim = float(torch.dot(target_proto, sv).item())
        other_best = max(
            (float(torch.dot(p, sv).item()) for p in other_protos),
            default=-1.0,
        )
        margin = target_sim - other_best
        if target_sim > best_sim or (
            abs(target_sim - best_sim) < 1e-9 and margin > best_margin
        ):
            best_sim = target_sim
            best_margin = margin

    ok = best_sim >= min_similarity and best_margin >= min_margin
    return ok, best_sim, best_margin


def _clean_slot(slot: str) -> str:
    slot = slot.strip()
    slot = re.sub(r"(?:を|は|が|の)$", "", slot)
    return slot.strip()


def slot_aliases(slot: str) -> tuple[str, ...]:
    key = _clean_slot(slot).lower()
    return SLOT_ALIASES.get(key, (key,))


def slot_present(slot: str, answer: str) -> bool:
    answer_lower = answer.lower()
    return any(alias.lower() in answer_lower for alias in slot_aliases(slot))


def extract_suspicious_entities(text: str) -> list[str]:
    """Extract novel-looking identifiers whose identity should survive generation."""
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9_+.#-]{1,39}", text)
    entities: list[str] = []
    for token in candidates:
        upper = token.upper()
        if upper in KNOWN_ENTITY_TOKENS:
            continue

        # Conservative: require digits/hyphen, or mixed-case identifier shape.
        suspicious = (
            any(ch.isdigit() for ch in token)
            or "-" in token
            or (
                any(ch.islower() for ch in token)
                and any(ch.isupper() for ch in token[1:])
                and len(token) >= 5
            )
        )
        if suspicious and token not in entities:
            entities.append(token)
    return entities


def extract_definition_focus(text: str) -> str | None:
    """Extract focus from Japanese definition prompts such as 'GPUとは'."""
    compact = text.strip()
    patterns = [
        r"^\s*([A-Za-z0-9_+.#\-]{2,40})\s*(?:とは|って|とは何|って何)\s*[、,。．！？!?？?]*\s*$",
        r"^\s*([^\s、。！？?]{1,40})\s*(?:とは|って)\s*[、,。．！？!?？?]*\s*$",
    ]
    for p in patterns:
        m = re.search(p, compact, flags=re.IGNORECASE)
        if m:
            return _clean_slot(m.group(1))
    return None



RUNTIME_TRAILING_PUNCTUATION = "、，,。．.!！?？:：;；"


def normalize_runtime_input(text: str) -> str:
    """Normalize runtime input before semantic routing.

    v10.16.1 first recognizes conditional *questions* so they cannot be
    misparsed as declarative modifier statements. Declarative inputs then use
    the v10.16 Modifier-to-Condition normalizer.
    """
    normalized = unicodedata.normalize("NFKC", text).strip()

    # Commands are control-plane input, not natural-language semantic input.
    # Preserve the command name and payload verbatim (apart from NFKC/trim)
    # so /condteach, /teachq, /promote, etc. cannot be rewritten as facts.
    if normalized.startswith("/"):
        return normalized

    normalized = normalized.rstrip(RUNTIME_TRAILING_PUNCTUATION).strip()

    conditional_query = parse_conditional_query(normalized)
    if conditional_query.matched:
        return conditional_query.normalized

    return normalize_modifier_condition_text(normalized)


def input_quality_check(text: str) -> tuple[bool, str]:
    q = text.strip()
    if not q:
        return False, "empty input"

    compact = _normalize_for_similarity(q)

    # Bare interrogative/function words have no subject or target concept.
    # Do not let the language model guess a topic from prior training bias.
    bare_interrogatives = {
        "とは", "って", "なに", "何", "何ですか", "教えて",
        "説明して", "について", "は", "を", "の",
    }
    if q.rstrip("、。！？?! ").strip() in bare_interrogatives:
        return False, "missing query subject"

    # Repeated interrogative fragments such as "とはとは".
    if re.search(r"(とは){2,}|(って){2,}", q):
        return False, "malformed repeated intent"

    # Obvious typo pattern observed in regression: a known technical acronym
    # followed by an unrelated single kanji instead of an interrogative form.
    if re.fullmatch(r"(AI|CPU|GPU|LLM|CUDA)[一-龯]", q, flags=re.IGNORECASE):
        return False, "malformed technical-term suffix"

    # Multiple bare known entities plus a broken definition marker are
    # ambiguous rather than a well-formed comparison/definition request.
    known_hits = re.findall(r"\b(?:AI|CPU|GPU|LLM|CUDA)\b", q, flags=re.IGNORECASE)
    if len(set(x.upper() for x in known_hits)) >= 2 and "とは" in q:
        if not re.search(r"(違い|比較|差)", q):
            return False, "incoherent multi-concept input"

    # Very short garbage around a known acronym should not be auto-corrected.
    if len(compact) <= 6 and re.search(r"(AI|CPU|GPU|LLM|CUDA)", q, flags=re.IGNORECASE):
        if not (
            extract_definition_focus(q)
            or re.search(r"(について|説明|教えて|違い|比較)", q)
        ):
            # Bare acronym is still allowed as a general query.
            if compact.upper() not in {"AI", "CPU", "GPU", "LLM", "CUDA"}:
                return False, "malformed short technical query"

    return True, "input accepted"


def classify_intent_and_slots(question: str) -> tuple[str, list[str]]:
    q = question.strip()
    q_lower = q.lower()

    greeting_patterns = (
        "こんにちは", "こんばんは", "おはよう", "お疲れ", "はじめまして",
        "やあ", "hello", "hi",
    )
    if any(x in q_lower for x in greeting_patterns):
        return "greeting", []

    # Comparison: "AとBの違い", "AとBを比較", "AとBの差"
    m = re.search(
        r"^\s*([^\s、。！？?と]{1,30})\s*と\s*([^\s、。！？?]{1,30}?)"
        r"\s*(?:を|の)?(?:違い|差|比較|違う点)",
        q,
        flags=re.IGNORECASE,
    )
    if m:
        return "comparison", [
            _clean_slot(m.group(1)),
            _clean_slot(m.group(2)),
        ]

    focus = extract_definition_focus(q)
    if focus:
        return "definition", [focus]

    return "general", []


def greeting_consistent(answer: str) -> bool:
    a = answer.lower()
    greeting_terms = (
        "こんにちは", "こんばんは", "おはよう", "お疲れ", "はじめまして",
        "よろしく", "話しましょう", "何について", "hello", "hi",
    )
    return any(x in a for x in greeting_terms)



def _normalize_definition_surface(text: str) -> str:
    norm = _normalize_for_similarity(text)
    # Strip sentence-final punctuation and light copula/polite endings so that
    # "人工知能", "人工知能です", and "人工知能です。" are treated alike.
    norm = re.sub(r"[。．.!！?？、,]+$", "", norm)
    for ending in ("です", "だ", "である", "です。", "だ。", "である。"):
        e = _normalize_for_similarity(ending)
        if norm.endswith(e):
            norm = norm[:-len(e)]
            break
    return norm


def definition_is_echo_only(slot: str, answer: str) -> bool:
    answer_norm = _normalize_definition_surface(answer)
    aliases = {
        _normalize_definition_surface(alias)
        for alias in strict_synonyms(slot)
    }
    if answer_norm in aliases:
        return True

    # Also reject simple copular synonym statements such as
    # "人工知能はAIです" when asked for a definition.
    compact = _normalize_for_similarity(answer)
    for left in strict_synonyms(slot):
        left_n = _normalize_for_similarity(left)
        for right in strict_synonyms(slot):
            right_n = _normalize_definition_surface(right)
            if left_n == right_n:
                continue
            candidates = (
                f"{left_n}は{right_n}です",
                f"{left_n}は{right_n}",
            )
            if _normalize_definition_surface(compact) in {
                _normalize_definition_surface(x) for x in candidates
            }:
                return True
    return False


def definition_is_uninformative(slot: str, answer: str) -> bool:
    if definition_is_echo_only(slot, answer):
        return True

    a = _normalize_for_similarity(answer)
    # Reject vacuous templates that mention the focus but provide no category,
    # function, property, relation, or differentiating content.
    vacuous_patterns = (
        "同じ種類のもの",
        "同じもの",
        "ものです",
        "ものだ",
        "ものです。",
        "ものだ。",
        "一種です",
        "一種だ",
        "何かです",
        "何かだ",
    )
    if any(_normalize_for_similarity(p) in a for p in vacuous_patterns):
        # "Xは言語モデルです" should pass because it supplies a concrete category.
        informative_terms = (
            "モデル", "装置", "技術", "方式", "手法", "プロセッサ",
            "処理装置", "ソフトウェア", "ハードウェア", "システム",
            "人工知能", "言語モデル", "大規模言語モデル",
        )
        if not any(_normalize_for_similarity(t) in a for t in informative_terms):
            return True

    # Require at least some content beyond the focus/alias and light particles.
    # A concrete category relation is informative even when the answer is short:
    # "LLMは言語モデルです", "GPUは画像処理装置です".
    if any(
        _normalize_for_similarity(category) in a
        for category in definition_categories(slot)
    ):
        return False

    stripped = a
    for alias in sorted(strict_synonyms(slot), key=len, reverse=True):
        stripped = stripped.replace(_normalize_for_similarity(alias), "")
    stripped = re.sub(r"(とは|は|って|を|が|に|で|の|です|だ|である|。|、|,|\.)", "", stripped)
    return len(stripped) < 2


def slot_coverage_check(
    intent: str,
    slots: list[str],
    answer: str,
) -> tuple[bool, float, str]:
    if intent == "greeting":
        if greeting_consistent(answer):
            return True, 1.0, "greeting matched"
        return False, 0.0, "greeting intent mismatch"

    if not slots:
        return True, 1.0, "no required slots"

    hits = [slot for slot in slots if slot_present(slot, answer)]
    coverage = len(hits) / len(slots)

    if intent == "definition":
        if coverage < 1.0:
            return False, coverage, f"definition focus missing: {slots[0]}"

        if definition_is_echo_only(slots[0], answer):
            return False, coverage, "definition answer is only an echo"
        if definition_is_uninformative(slots[0], answer):
            return False, coverage, "definition answer is uninformative"

        return True, coverage, "definition slot covered"

    if intent == "comparison":
        if coverage < 1.0:
            missing = [s for s in slots if not slot_present(s, answer)]
            return (
                False,
                coverage,
                "comparison slot missing: " + ", ".join(missing),
            )

        comparison_cues = (
            "一方", "対して", "違", "比べ", "比較", "対照", "より",
            "得意", "汎用", "並列", "制御",
        )
        if not any(cue in answer for cue in comparison_cues):
            return False, coverage, "comparison relation missing"

        return True, coverage, "comparison slots covered"

    return True, coverage, "slots covered"


def focus_consistent(question: str, answer: str) -> tuple[bool, str]:
    focus = extract_definition_focus(question)
    if not focus:
        return True, "no explicit focus"

    if focus.lower() in answer.lower():
        return True, "focus preserved"

    # Strong mismatch for acronym/technical-term definition questions.
    if re.fullmatch(r"[A-Za-z0-9_+.#\-]{2,20}", focus):
        return False, f"definition focus missing: {focus}"

    return True, "focus not mandatory"



ANSWER_CONCEPT_RULES = {
    "ai": {
        "required_any": ("人工知能", "知的", "技術", "システム", "llm"),
        "forbidden": (),
    },
    "人工知能": {
        "required_any": ("人工知能", "知的", "技術", "システム", "ai"),
        "forbidden": (),
    },
    "cpu": {
        "required_any": ("中央処理装置", "プロセッサ", "命令", "制御", "演算"),
        "forbidden": ("人工知能", "llm", "言語モデル"),
    },
    "gpu": {
        "required_any": ("gpu", "並列", "演算", "プロセッサ", "画像処理装置"),
        "forbidden": ("人工知能", "llm", "言語モデル"),
    },
    "llm": {
        "required_any": ("llm", "言語モデル", "大規模言語モデル", "言語"),
        "forbidden": ("画像処理装置", "中央処理装置"),
    },
}


def answer_concept_consistency(
    question: str,
    answer: str,
) -> tuple[bool, str]:
    q = question.lower()
    matched_key = None
    for key in ("gpu", "cpu", "llm", "人工知能", "ai"):
        if key in q:
            matched_key = key
            break

    if matched_key is None:
        return True, "no answer concept rule"

    rule = ANSWER_CONCEPT_RULES[matched_key]
    a = answer.lower()

    required = rule["required_any"]
    if required and not any(term.lower() in a for term in required):
        return False, f"answer concept missing for {matched_key.upper()}"

    bad = [term for term in rule["forbidden"] if term.lower() in a]
    if bad:
        return False, (
            f"answer concept conflict for {matched_key.upper()}: "
            + ", ".join(bad)
        )

    return True, "answer concept consistent"

CANONICAL_DEFINITIONS = {
    "cpu": "CPUは、命令を解釈して演算や制御を実行する中央処理装置である。",
    "gpu": "GPUは、多数の演算を並列に実行することを得意とする処理装置である。",
    "cuda": "CUDAは、NVIDIAのGPUを汎用計算に利用するための並列計算基盤である。",
}


def canonical_definition_lookup(question: str) -> tuple[str, str] | None:
    """Return a stable canonical definition for explicitly validated concepts."""
    focus = extract_concept_query_focus(question)
    if not focus:
        focus = extract_bare_concept_focus(question)
    if not focus:
        return None

    answer = CANONICAL_DEFINITIONS.get(focus.lower())
    if not answer:
        return None
    return focus, answer


KNOWN_QUERY_CONCEPTS = {
    "ai", "人工知能",
    "llm", "大規模言語モデル",
    "cpu", "gpu", "cuda",
    "コンピュータ",
    "量子力学", "量子コンピュータ",
    "semantic", "セマンティック", "セマンティックデータ",
    # Persona/identity concepts that are explicitly trained in the Nagato SFT.
    "長門", "長門有希",
}


def extract_bare_concept_focus(question: str) -> str:
    """Extract a conservative bare concept token such as 'CUDA' or '宇宙'.

    This intentionally excludes conversational/persona phrases and malformed
    punctuation. It is used only as a pre-generation safety gate.
    """
    q = question.strip()
    if not q:
        return ""

    # Exclude whitespace, sentence punctuation, particles and command-like text.
    if re.search(r"[\s。、！？!?？,:：;；]", q):
        return ""
    if len(q) > 24:
        return ""

    # Technical identifiers or short Japanese noun-like tokens.
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_+.#\-]{1,23}", q):
        return q
    if re.fullmatch(r"[一-龯々ァ-ヶー]{2,24}", q):
        return q

    return ""


BARE_DEFINITION_CONCEPTS = {
    "ai", "人工知能",
    "llm", "大規模言語モデル",
    "cpu", "gpu", "cuda",
    "コンピュータ",
    "量子力学", "量子コンピュータ",
    "semantic", "セマンティック", "セマンティックデータ",
}


def canonicalize_bare_known_query(question: str) -> str:
    """Turn a validated bare knowledge concept into an explicit definition query.

    Example: "CPU" -> "CPUとは".

    Persona nouns such as "長門" are intentionally excluded; this helper is
    only for concepts whose bare form semantically means "tell me what X is".
    """
    focus = extract_bare_concept_focus(question)
    if not focus:
        return question
    if focus.lower() not in BARE_DEFINITION_CONCEPTS:
        return question
    return f"{focus}とは"


def extract_concept_query_focus(question: str) -> str:
    """Extract a concept from the explicit query forms used by the pre-gate."""
    q = question.strip()
    patterns = (
        r"^(.+?)(?:とは)$",
        r"^(.+?)(?:って何)$",
        r"^(.+?)(?:について教えて)$",
        r"^(.+?)(?:を説明して)$",
        r"^(.+?)(?:を簡単に説明して)$",
        r"^([^\s。、！？?]{1,24})は$",
    )
    for pattern in patterns:
        m = re.fullmatch(pattern, q)
        if m:
            return m.group(1).strip()
    return ""


def raw_corpus_knows_focus(
    focus: str,
    corpus_path: str | Path = DEFAULT_RAW_KNOWLEDGE_CORPUS,
    min_occurrences: int = 2,
) -> bool:
    """Return True when a concept is materially present in the local raw corpus.

    This only relaxes the *pre-generation* lexical gate.  The generated answer
    must still pass the normal confidence/semantic gate.
    """
    path = resolve_runtime_path(corpus_path)
    if not path.exists() or not focus:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return text.count(focus) >= max(1, min_occurrences)


def semantic_proposition_lookup(
    question: str,
    proposition_path: str | Path = DEFAULT_PROPOSITION_STORE,
) -> tuple[str, str] | None:
    """Return a composed answer from atomic propositions for concept queries."""
    focus = extract_concept_query_focus(question)
    if not focus:
        focus = extract_bare_concept_focus(question)
    if not focus:
        return None

    path = resolve_runtime_path(proposition_path)
    if not path.exists():
        return None

    answer = compose_semantic_proposition_subject(path, focus)
    if not answer:
        return None
    return focus, answer


def semantic_knowledge_lookup(
    question: str,
    knowledge_path: str | Path = DEFAULT_SEMANTIC_KNOWLEDGE,
) -> tuple[str, str] | None:
    """Look up a merged semantic answer for an explicit concept query.

    Returns (concept, answer) when the concept is present in the semantic
    proposition knowledge file.  This is retrieval, not generation.
    """
    focus = extract_concept_query_focus(question)
    if not focus:
        focus = extract_bare_concept_focus(question)
    if not focus:
        return None

    path = resolve_runtime_path(knowledge_path)
    if not path.exists():
        return None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for raw in lines:
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue

        concept = str(row.get("concept", "")).strip()
        answer = str(row.get("assistant", "")).strip()
        if concept == focus and answer:
            return concept, answer

    return None


def pre_generation_unknown_concept(
    question: str,
    promoted_concepts: set[str] | None = None,
) -> tuple[bool, str]:
    """
    Question-side lexical concept gate for definition/explanation prompts.

    Returns (is_unknown, focus). This is intentionally conservative and only
    triggers on explicit concept-query forms so ordinary persona/chat prompts
    such as '本は好きですか' are unaffected.
    """
    explicit_focus = extract_concept_query_focus(question)
    bare_focus = ""
    focus = explicit_focus
    if not focus:
        bare_focus = extract_bare_concept_focus(question)
        focus = bare_focus
    if not focus:
        return False, ""

    norm = focus.lower()

    # Pronouns / conversational identity prompts are not knowledge concepts.
    # They must reach the normal persona/chat path instead of being rejected
    # by the lexical concept pre-gate.
    NON_CONCEPT_FOCI = {
        "あなた", "貴方", "きみ", "君", "おまえ", "お前",
        "わたし", "私", "ぼく", "僕",
    }
    if focus in NON_CONCEPT_FOCI:
        return False, focus

    if norm in KNOWN_QUERY_CONCEPTS:
        return False, focus
    if promoted_concepts and norm in promoted_concepts:
        return False, focus

    # v10.9.0 semantic integration: a bare noun such as "時間" must not
    # become KNOWN merely because the raw corpus contains the token.  Bare
    # concept queries require validated/promoted knowledge or a retrieval hit
    # handled before this gate.  This prevents corpus-frequency hallucination.
    if bare_focus:
        return True, focus

    # Preserve the legacy raw-corpus relaxation only for explicit concept
    # queries such as "Xとは".  Generated answers still pass downstream gates.
    if raw_corpus_knows_focus(focus):
        return False, focus
    return True, focus


def classify_resolution(
    accepted: bool,
    reason: str,
    question: str = "",
) -> tuple[str, str]:
    if accepted:
        return "ACCEPT", "none"

    q = question.strip()

    input_markers = (
        "malformed repeated intent",
        "malformed technical-term suffix",
        "incoherent multi-concept input",
        "malformed short technical query",
        "empty input",
        "missing query subject",
    )
    if any(marker in reason for marker in input_markers):
        return "INPUT_REJECT", "ask/rephrase"

    # Unknown named entities are not automatically a local training failure.
    # They should be routed to external knowledge or explicit teaching.
    if "unknown entity missing" in reason:
        return "UNKNOWN_KNOWLEDGE", "retrieve/teach"

    # Known concepts with incomplete or contradictory answers indicate that
    # the current model should be taught rather than the gate relaxed.
    learning_markers = (
        "definition answer is only an echo",
        "definition answer is uninformative",
        "concept slot missing",
        "answer concept missing",
        "answer concept conflict",
    )
    if any(marker in reason for marker in learning_markers):
        return "LEARNING_GAP", "teach/train"

    # A definition-like request for an unknown focus term is also knowledge
    # absence even when the generation failed before entity matching.
    focus = extract_definition_focus(q)
    known_focuses = {"ai", "人工知能", "cpu", "gpu", "llm", "大規模言語モデル", "cuda"}
    if focus and focus.lower() not in known_focuses:
        return "UNKNOWN_KNOWLEDGE", "retrieve/teach"

    # Confidence/agreement/quality failures are routed for gate review.
    return "GATE_REVIEW", "review/gate"


def semantic_consistency_check(
    model: LanguageModel,
    tokenizer: Tokenizer,
    current_question: str,
    answer: str,
    history: List[Tuple[str, str]],
    contamination_margin: float,
) -> tuple[bool, float, float, str, str, list[str], float]:
    intent, slots = classify_intent_and_slots(current_question)

    suspicious_entities = extract_suspicious_entities(current_question)
    missing_entities = [
        entity
        for entity in suspicious_entities
        if entity.lower() not in answer.lower()
    ]
    if missing_entities:
        return (
            False, 0.0, 0.0,
            "unknown entity missing: " + ", ".join(missing_entities),
            intent, slots, 0.0,
        )

    # Compute semantic similarity before lexical slot rejection so that
    # canonical concepts can use a conservative semantic fallback.
    qv = semantic_vector(model, tokenizer, current_question)
    av = semantic_vector(model, tokenizer, answer)
    current_sim = float(torch.dot(qv, av).item())

    slots_ok, slot_coverage, slot_reason = slot_coverage_check(
        intent, slots, answer
    )

    # v1.6.4 hard constraint: a definition that is only the focus term or
    # one of its aliases is incomplete. Do not let concept fallback override it.
    if intent == "definition" and slots:
        if definition_is_echo_only(slots[0], answer):
            return (
                False,
                current_sim,
                0.0,
                "definition answer is only an echo",
                intent,
                slots,
                slot_coverage,
            )
        if definition_is_uninformative(slots[0], answer):
            return (
                False,
                current_sim,
                0.0,
                "definition answer is uninformative",
                intent,
                slots,
                slot_coverage,
            )

    if not slots_ok and intent in ("definition", "comparison") and slots:
        covered = 0
        evidence: list[str] = []
        for slot in slots:
            if slot_present(slot, answer):
                covered += 1
                evidence.append(f"{slot}:lexical")
                continue

            categories = definition_categories(slot)
            answer_norm = _normalize_for_similarity(answer)
            matched_category = next(
                (
                    category
                    for category in categories
                    if _normalize_for_similarity(category) in answer_norm
                ),
                None,
            )
            if intent == "definition" and matched_category is not None:
                covered += 1
                evidence.append(
                    f"{slot}:category({matched_category})"
                )
                continue

            concept_ok, concept_sim, concept_margin = concept_slot_match(
                model=model,
                tokenizer=tokenizer,
                slot=slot,
                answer=answer,
            )
            if concept_ok:
                covered += 1
                evidence.append(
                    f"{slot}:concept({concept_sim:.3f}/{concept_margin:.3f})"
                )
            else:
                evidence.append(
                    f"{slot}:miss({concept_sim:.3f}/{concept_margin:.3f})"
                )

        slot_coverage = covered / len(slots)
        if slot_coverage >= 1.0:
            slots_ok = True
            slot_reason = "concept-aware slots: " + ", ".join(evidence)
        else:
            return (
                False,
                current_sim,
                0.0,
                "concept slot missing: " + ", ".join(evidence),
                intent,
                slots,
                slot_coverage,
            )

    # Greeting turns are intentionally short and semantically broad.
    # Slot/intent matching is more reliable than history similarity here.
    # A non-greeting answer must not pass merely because generation confidence
    # or probe agreement is high.
    if intent == "greeting":
        return (
            slots_ok, current_sim, -1.0, slot_reason,
            intent, slots, slot_coverage,
        )

    previous_sims: List[float] = []
    contamination_candidates: List[float] = []
    for old_user, _ in history[-3:]:
        pv = semantic_vector(model, tokenizer, old_user)
        old_answer_sim = float(torch.dot(pv, av).item())
        old_current_sim = float(torch.dot(pv, qv).item())
        previous_sims.append(old_answer_sim)

        # v1.6.3: history is suspicious only when the previous question is
        # materially different from the current question. Closely related
        # paraphrases/synonyms must not be rejected merely because the answer
        # also matches the previous turn.
        if old_current_sim < 0.82:
            contamination_candidates.append(old_answer_sim)

    previous_best = max(previous_sims) if previous_sims else -1.0
    contamination_best = (
        max(contamination_candidates)
        if contamination_candidates
        else -1.0
    )

    if (
        contamination_candidates
        and contamination_best > current_sim + contamination_margin
    ):
        return (
            False,
            current_sim,
            previous_best,
            "history contamination",
            intent,
            slots,
            slot_coverage,
        )

    return (
        True,
        current_sim,
        previous_best,
        slot_reason,
        intent,
        slots,
        slot_coverage,
    )


def calibrated_agreement_threshold(
    intent: str,
    semantic_ok: bool,
    slot_coverage: float,
    base_threshold: float,
) -> float:
    """Relax agreement only when semantic structure is already verified."""
    if (
        semantic_ok
        and slot_coverage >= 1.0
        and intent in ("definition", "comparison")
    ):
        return min(base_threshold, 0.30)
    return base_threshold


def evaluate_unknown_gate(
    model: LanguageModel,
    tokenizer: Tokenizer,
    results: List[GenerationResult],
    min_confidence: float,
    min_token_confidence: float,
    min_mean_margin: float,
    min_agreement: float,
    min_semantic_agreement: float,
    allow_semantic_rescue: bool,
) -> Tuple[bool, float, float, float, str]:
    if not results:
        return False, 0.0, 0.0, 0.0, "no generation"

    primary = results[0]

    if malformed_or_unstable(primary.text):
        return (
            False,
            primary.mean_confidence,
            0.0,
            0.0,
            "malformed/repetitive output",
        )

    # v1.6.8 Output Quality Gate: semantic agreement cannot rescue a response
    # containing a locally very unlikely token sequence.
    if primary.min_confidence < min_token_confidence:
        return (
            False,
            primary.mean_confidence,
            0.0,
            0.0,
            "low local token confidence",
        )

    if primary.mean_top2_margin < min_mean_margin:
        return (
            False,
            primary.mean_confidence,
            0.0,
            0.0,
            "low generation margin",
        )

    lexical_agreement = mean_pairwise_agreement(results)
    semantic_agreement = mean_pairwise_semantic_agreement(
        model,
        tokenizer,
        results,
    )

    if primary.mean_confidence < min_confidence:
        return (
            False,
            primary.mean_confidence,
            lexical_agreement,
            semantic_agreement,
            "low token confidence",
        )

    if lexical_agreement >= min_agreement:
        return (
            True,
            primary.mean_confidence,
            lexical_agreement,
            semantic_agreement,
            "accepted",
        )

    # v1.6.7 semantic rescue is deliberately conservative: it is enabled only
    # after the primary answer has passed semantic/slot validation.
    if allow_semantic_rescue and semantic_agreement >= min_semantic_agreement:
        return (
            True,
            primary.mean_confidence,
            lexical_agreement,
            semantic_agreement,
            "semantic probe agreement",
        )

    return (
        False,
        primary.mean_confidence,
        lexical_agreement,
        semantic_agreement,
        "low response agreement",
    )


def print_info(
    model: LanguageModel,
    tokenizer: Tokenizer,
    checkpoint: dict,
    device: torch.device,
    model_path: Path,
    tokenizer_path: Path,
    args: argparse.Namespace,
) -> None:
    print()
    print("==============================================")
    print(" LLM_TRY Chat - v10.16.5 Conditional Semantic Runtime Stable")
    print("==============================================")
    print("Device          :", device)
    if device.type == "cuda":
        print("GPU             :", torch.cuda.get_device_name(0))
    print("Model           :", model_path)
    print("Tokenizer       :", tokenizer_path)
    print("Vocabulary size :", tokenizer.vocab_size)
    print("Parameters      :", f"{model.parameter_count:,}")
    print("Context length  :", model.context_length)
    print("d_model         :", model.d_model)
    print("Layers          :", model.num_layers)
    print("Attention heads :", model.num_heads)
    print("Checkpoint epoch:", checkpoint.get("epoch"))
    print("Checkpoint loss :", checkpoint.get("loss"))
    print("Unknown reject  :", args.unknown_rejection)
    if args.unknown_rejection:
        print("Probe count     :", args.probe_count)
        print("Min confidence  :", args.min_confidence)
        print("Min token conf  :", args.min_token_confidence)
        print("Min mean margin :", args.min_mean_margin)
        print("Min agreement   :", args.min_agreement)
        print("Min sem agree   :", args.min_semantic_agreement)
        print("Min int semantic:", args.min_internalized_fidelity)
        print(
            "Min int lexical :",
            args.min_internalized_lexical_coverage,
        )
        print(
            "Min int required:",
            args.min_internalized_required_coverage,
        )
        print("Fallback        :", UNKNOWN_REPLY)
        print("Context policy  : minimal")
        print("Teaching queue  :", args.teaching_queue)
        print("Knowledge queue :", args.knowledge_queue)
        print("Gate review q   :", args.gate_review_queue)
        print("Proposition db  :", args.propositions)
        print("Subject index   :", args.subject_index)
        print("Typed index     :", args.typed_subject_index)
        print("Corpus memory   :", args.corpus_memory)
        print("Conditional db  :", args.conditional_propositions)
        print("Cond candidates :", args.conditional_candidates)
        print(
            "Concept calib   :",
            CALIBRATION_INFO.get("version", "raw fallback")
            if CALIBRATION_INFO.get("loaded")
            else "raw fallback",
        )
        if CALIBRATION_INFO.get("loaded"):
            print("Centroid source : TRAIN ONLY")
            print("Holdout in fit  :", CALIBRATION_INFO.get("holdout_used_for_centroid"))
    metadata = checkpoint.get("metadata", {})
    if isinstance(metadata, dict):
        bound = metadata.get("trained_fingerprints", [])
        binding_version = metadata.get("knowledge_binding_version", "")
        print(
            "Checkpoint bind :",
            f"{len(bound) if isinstance(bound, list) else 0} fingerprint(s)",
        )
        if binding_version:
            print("Binding version :", binding_version)
    print()


def run_candidate_repair_quality_gate(
    *,
    model: LanguageModel,
    tokenizer: Tokenizer,
    plan,
    args: argparse.Namespace,
) -> tuple[bool, int, int]:
    probes: list[RepairQualityProbe] = []

    for row in plan.tasks:
        concept = str(row.get("concept", "")).strip()
        question = str(row.get("question", "")).strip()
        teacher = str(row.get("teacher_answer", "")).strip()
        fingerprint = str(row.get("fingerprint", "")).strip()

        prompt, _ = build_prompt(
            history=[],
            user_text=question,
            history_turns=0,
        )
        generated = generate_reply(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=0.0,
            top_k=args.top_k,
            repetition_penalty=args.repetition_penalty,
            seed=0,
        )
        malformed = malformed_or_unstable(generated.text)
        composite = composite_internalized_teacher_fidelity(
            model=model,
            tokenizer=tokenizer,
            generated_answer=generated.text,
            teacher_answer=teacher,
            concept=concept,
        )
        fidelity_ok, fidelity_reason = (
            apply_composite_internalized_fidelity_policy(
                accepted=not malformed,
                result=composite,
                semantic_threshold=args.min_internalized_fidelity,
                lexical_threshold=args.min_internalized_lexical_coverage,
                required_threshold=args.min_internalized_required_coverage,
            )
        )
        reason = (
            fidelity_reason
            if fidelity_reason
            else (
                "malformed/repetitive output"
                if malformed
                else "repair quality gate rejected"
            )
        )
        probes.append(
            RepairQualityProbe(
                concept=concept,
                question=question,
                teacher_answer=teacher,
                fingerprint=fingerprint,
                generated_answer=generated.text,
                semantic=composite.semantic_similarity,
                lexical=composite.lexical_coverage,
                required=composite.required_coverage,
                contradiction=composite.contradiction,
                passed=fidelity_ok,
                reason=reason,
            )
        )
        print(
            f"[repair quality {'PASS' if fidelity_ok else 'FAIL'}: "
            f"concept={concept!r}, "
            f"sem={composite.semantic_similarity:.3f}, "
            f"lex={composite.lexical_coverage:.3f}, "
            f"req={composite.required_coverage:.3f}, "
            f"contra={composite.contradiction}]"
        )
        if not fidelity_ok:
            print(f"  candidate={generated.text}")
            print(f"  reason={reason}")

    summary = append_repair_quality_audit(
        Path(args.candidate_repair_quality_audit),
        probes=probes,
    )
    print(
        f"[candidate repair quality gate: "
        f"targets={summary.targets}, "
        f"passed={summary.passed}, "
        f"failed={summary.failed}, "
        f"status={'PASS' if summary.ok else 'FAIL'}]"
    )
    return summary.ok, summary.passed, summary.failed


def run_batch_preservation_gate(
    *,
    model: LanguageModel,
    tokenizer: Tokenizer,
    protected_records,
    args: argparse.Namespace,
    batch_fingerprints: tuple[str, ...],
) -> tuple[bool, int, int]:
    probes: list[PreservationProbe] = []

    for record in protected_records:
        prompt, _ = build_prompt(
            history=[],
            user_text=record.question,
            history_turns=0,
        )
        generated = generate_reply(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=0.0,
            top_k=args.top_k,
            repetition_penalty=args.repetition_penalty,
            seed=0,
        )
        composite = composite_internalized_teacher_fidelity(
            model=model,
            tokenizer=tokenizer,
            generated_answer=generated.text,
            teacher_answer=record.teacher_answer,
            concept=record.concept,
        )
        fidelity_ok, fidelity_reason = (
            apply_composite_internalized_fidelity_policy(
                accepted=not malformed_or_unstable(generated.text),
                result=composite,
                semantic_threshold=args.min_internalized_fidelity,
                lexical_threshold=args.min_internalized_lexical_coverage,
                required_threshold=args.min_internalized_required_coverage,
            )
        )
        reason = (
            fidelity_reason
            if fidelity_reason
            else (
                "malformed/repetitive output"
                if malformed_or_unstable(generated.text)
                else "preservation gate rejected"
            )
        )
        probes.append(
            PreservationProbe(
                concept=record.concept,
                question=record.question,
                teacher_answer=record.teacher_answer,
                fingerprint=record.fingerprint,
                generated_answer=generated.text,
                semantic=composite.semantic_similarity,
                lexical=composite.lexical_coverage,
                required=composite.required_coverage,
                contradiction=composite.contradiction,
                passed=fidelity_ok,
                reason=reason,
            )
        )
        print(
            f"[preservation {'PASS' if fidelity_ok else 'FAIL'}: "
            f"concept={record.concept!r}, "
            f"sem={composite.semantic_similarity:.3f}, "
            f"lex={composite.lexical_coverage:.3f}, "
            f"req={composite.required_coverage:.3f}, "
            f"contra={composite.contradiction}]"
        )
        if not fidelity_ok:
            print(f"  candidate={generated.text}")
            print(f"  reason={reason}")

    summary = append_preservation_audit(
        Path(args.batch_preservation_audit),
        batch_fingerprints=batch_fingerprints,
        probes=probes,
    )
    print(
        f"[batch preservation gate: "
        f"protected={summary.protected}, "
        f"passed={summary.passed}, "
        f"failed={summary.failed}, "
        f"status={'PASS' if summary.ok else 'FAIL'}]"
    )
    return summary.ok, summary.passed, summary.failed


def checkpoint_trained_fingerprints(
    checkpoint: dict,
) -> frozenset[str]:
    metadata = checkpoint.get("metadata", {})
    if not isinstance(metadata, dict):
        return frozenset()
    values = metadata.get("trained_fingerprints", [])
    if not isinstance(values, (list, tuple, set)):
        return frozenset()
    return frozenset(str(value) for value in values)


def main() -> None:
    args = parse_args()

    tokenizer_path = resolve_runtime_path(args.tokenizer)
    model_path = choose_startup_model(
        args.model,
        online_output=args.online_output,
        learning_state=args.learning_state,
    )

    if not tokenizer_path.exists():
        raise FileNotFoundError(
            f"Tokenizer not found: {tokenizer_path}\n"
            "Place tokenizer-v0.7-bpe.json under LLM_TRY/model/ or "
            "keep the sibling LLM_GPU/model/ directory available. "
            "You can also pass --tokenizer <path>."
        )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Chat model not found: {model_path}\n"
            "Expected the LLM_TRY v9.4 Nagato SFT checkpoint.\n"
            "Place it under LLM_TRY/model/ or pass --model <path>."
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    tokenizer = Tokenizer.load(str(tokenizer_path))
    model, checkpoint = LanguageModel.load_checkpoint(
        str(model_path),
        device=device,
    )

    calibration_path = resolve_runtime_path(args.concept_calibration)
    load_concept_calibration(calibration_path, device)

    if model.vocab_size != tokenizer.vocab_size:
        raise ValueError(
            "Tokenizer/model vocabulary mismatch: "
            f"{tokenizer.vocab_size} != {model.vocab_size}"
        )

    print_info(
        model=model,
        tokenizer=tokenizer,
        checkpoint=checkpoint,
        device=device,
        model_path=model_path,
        tokenizer_path=tokenizer_path,
        args=args,
    )

    print("Commands:")
    print("  /cha-start    begin opt-in conversation memory capture (accepted replies only)")
    print("  /cha-load ID  load completed conversation for read-only recall")
    print("  /cha-recall Q recall recorded USER utterances with turn IDs")
    print("  /cha-unknown X show unverified user-taught candidate entries")
    print("  /cha-review X inspect candidate differences and review state")
    print("  /cha-ack ID  acknowledge review (does not verify, promote or train)")
    print("  /cha-usage ID       show usage/feedback state")
    print("  /cha-terms TEXT     inspect Wikipedia lookup candidates (diagnostic only)")
    print("  /cha-wiki TERM      retrieve Wikipedia summary with source and confidence state")
    print("  /cha-feedback ID +  explicit positive feedback")
    print("  /cha-feedback ID -  explicit negative feedback")
    print("  /cancel      cancel pending UNKNOWN teaching")
    print("  /cha-status   show conversation memory status")
    print("  /cha-close    close current conversation record")
    print("  /cha-sleep    update incremental checkpoint (no model training)")
    print("  /cha-migrate  preserve compact evidence and migration receipt")
    print("  /reset        clear conversation history")
    print("  /info         show model/checkpoint information")
    print("  /learn on     capture accepted turns for later training")
    print("  /learn off    stop capture")
    print("  /learn status show capture state and saved-pair count")
    print("  /teach TEXT   save a corrected answer for the previous user turn")
    print("  /teachq Q => A teach an explicit question/answer pair")
    print("  /good         approve and save the previous AI answer for learning")
    print("  /train        run incremental training and reload checkpoint")
    print("  /sleep        train PENDING candidates in Experimental Adapter; trusted Semantic Sleep remains separate")
    print("  /sleep status show Semantic Memory / internalized / pending counts")
    print("  /trainbatch   batch-train all active verification repair tasks")
    print("  /batchstatus  show verification-aware batch repair plan")
    print("  /maintain     recover the previous question from trusted teaching data")
    print("  /maintain all recover all pending trusted teaching candidates")
    print("  /condteach S  persist conditional semantic proposition statement")
    print("  /conds        list conditional semantic propositions")
    print("  /condcandidates list pending auto-detected conditional candidates")
    print("  /condapprove N approve one pending candidate (or 'all')")
    print("  /propteach S  decompose and persist semantic proposition statement")
    print("  /prop X       compose stored propositions for subject X")
    print("  /props        list atomic semantic propositions")
    print("  /propsync     sync all atomic propositions to unified semantic memory")
    print("  /subject X    show X => X+predicate mappings")
    print("  /subjects     list subject-keyed proposition index")
    print("  /typedsubject X show X => predicate type => statement")
    print("  /typedsubjects list typed subject proposition index")
    print("  /internalized list concepts proven consumed by /train")
    print("  /kstate Q     inspect resolved knowledge state for query Q")
    print("  /dispatch Q   inspect dispatcher action for query Q")
    print("  /provenance Q inspect source/origin evidence for query Q")
    print("  /truth X      inspect effective truth state for concept X")
    print("  /truths       list explicit truth-state records")
    print("  /truthset X STATE [=> CORRECTION]")
    print("  /semstatus    show Semantic Knowledge Architecture status")
    print("  /semantic X   inspect all semantic knowledge layers for X")
    print("  /promotions   list pending UNKNOWN_KNOWLEDGE requests")
    print("  /promotionstatus show pending/promoted/verified lifecycle counts")
    print("  /verifystatus show internalized verification loop counts")
    print("  /verifications list active internalized verification tasks")
    print("  /promote X => STATEMENT  promote pending concept to semantic knowledge")
    print("  /exit         quit")
    print()

    history: List[Tuple[str, str]] = []
    learning_log = Path(args.learning_log)
    learning_state = Path(args.learning_state)
    proposition_path = resolve_runtime_path(args.propositions)
    conditional_proposition_path = resolve_runtime_path(
        args.conditional_propositions
    )
    conditional_candidate_path = resolve_runtime_path(
        args.conditional_candidates
    )
    unified_semantic_path = resolve_runtime_path(DEFAULT_SEMANTIC_KNOWLEDGE)
    subject_index_path = resolve_runtime_path(args.subject_index)
    typed_subject_index_path = resolve_runtime_path(
        args.typed_subject_index
    )
    truth_store_path = resolve_runtime_path(args.truth_store)

    semantic_config = SemanticKnowledgeConfig(
        proposition_path=proposition_path,
        subject_index_path=subject_index_path,
        typed_index_path=typed_subject_index_path,
        unified_path=unified_semantic_path,
        learning_log=learning_log,
        learning_state=learning_state,
        raw_corpus_path=resolve_runtime_path(
            DEFAULT_RAW_KNOWLEDGE_CORPUS
        ),
        truth_store_path=truth_store_path,
        canonical_definitions=CANONICAL_DEFINITIONS,
        checkpoint_fingerprints=checkpoint_trained_fingerprints(
            checkpoint
        ),
    )
    semantic_knowledge = SemanticKnowledgeArchitecture(
        semantic_config
    )

    nagato_semantic_memory_path = resolve_runtime_path(
        DEFAULT_NAGATO_SEMANTIC_MEMORY
    )
    semantic_sleep_sync = bootstrap_nagato_semantic_memory(
        resolve_runtime_path(DEFAULT_RAW_KNOWLEDGE_CORPUS),
        resolve_runtime_path(args.corpus_memory),
        nagato_semantic_memory_path,
        unified_semantic_path,
    )
    semantic_sleep_initial = semantic_sleep_status(
        nagato_semantic_memory_path,
        learning_state,
        checkpoint_trained_fingerprints(checkpoint),
    )
    print(
        f"[Nagato Semantic Memory: "
        f"corpus_records={semantic_sleep_sync.corpus_records}, "
        f"subjects={semantic_sleep_sync.memory_subjects}, "
        f"unified_added={semantic_sleep_sync.unified_added}, "
        f"unified_preserved={semantic_sleep_sync.unified_preserved}, "
        f"internalized={semantic_sleep_initial.internalized}, "
        f"pending={semantic_sleep_initial.pending}]"
    )
    print("[use /sleep to internalize pending Semantic Memory into model weights]")
    print()

    migrated_legacy_queue = consolidate_legacy_resolved(
        Path(args.knowledge_queue)
    )
    if migrated_legacy_queue:
        print(
            f"[knowledge queue lifecycle: migrated "
            f"{migrated_legacy_queue} legacy resolved row(s)]"
        )
        print()

    baseline_count = initialize_learning_state_if_missing(
        learning_state,
        learning_log,
        assume_existing_trained=(
            model_path != Path(DEFAULT_MODEL)
        ),
    )
    if baseline_count:
        print(
            f"[v1.6.2 baseline initialized: "
            f"{baseline_count} existing trusted pair(s) marked as trained]"
        )
        print()
    learning_enabled = bool(args.learn)
    # v0.2.33.82.4: opt-in transient context; no persistent knowledge writes.
    import os
    from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
    topic_adapter = (
        ConversationTopicAdapter()
        if os.environ.get("LLM_CHA_MULTITOPIC", "0") == "1"
        else None
    )
    if topic_adapter is not None:
        from grounded_expansion_v0233826 import PropositionCursor
        proposition_cursor = PropositionCursor()
        from proposition_truth_v0233827 import TruthOverlay
        proposition_truth = TruthOverlay(os.environ.get("LLM_CHA_PROPOSITION_TRUTH"))
        print("[multi-topic context enabled; Truth Gate unchanged]")
    # v0.2.34.3: explicit, opt-in context recovery only.
    context_recovery_path = (
        os.environ.get("LLM_CHA_CONTEXT_PATH")
        if topic_adapter is not None and os.environ.get("LLM_CHA_CONTEXT_RECOVERY", "0") == "1"
        else None
    )
    if context_recovery_path:
        print("[context recovery available: /context-save, /context-load]")
    cha_bridge = ConversationBridge(resolve_runtime_path(args.cha_memory_root))
    cha_user_context = UserContext()
    cha_wiki_conversation = WikiConversation()
    cha_wiki_evidence_session = ChaWikiEvidenceSession()
    from wiki_equation_evidence_v074430 import EquationCursor
    cha_wiki_equation_cursor = EquationCursor()
    pending_equation_explanation = None
    pending_wiki_topic_offer = None
    cha_wiki_evidence_continuation = ChaWikiEvidenceContinuation()
    cha_persona_context = PersonaContext(cha_wiki_conversation.persona)
    cha_persona_wiki_cache = {}
    cha_unknown_teacher = UnknownTeaching(resolve_runtime_path("data/cha_unknown_candidates_v0510.json"))
    cha_feedback_session = FeedbackSession()
    cha_correction_session = CorrectionSession()
    cha_recent_topic: str | None = None
    last_user_text: str | None = None
    last_ai_reply: str | None = None
    cha_wiki_retry_utterance: str | None = None
    cha_wiki_retry_status: str = "NEVER_RUN"
    cha_wiki_last_generated: str | None = None

    from identity_context_v0617 import IdentityContext
    identity_context = IdentityContext()
    aozora_dialogue = None
    if os.environ.get("LLM_CHA_AOZORA_ROUTER", "0") == "1":
        from aozora_literature_router_v069 import load_catalog
        from aozora_dialogue_v0610 import AozoraDialogue
        try:
            aozora_dialogue = AozoraDialogue(load_catalog(
                PROJECT_ROOT / "data" / "aozora_v064" / "aozora_semantic_corpus.jsonl"))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print("[aozora initialization unavailable: {}]".format(exc))

    from semantic_relation_context_v0620 import RelationContext, grounded_attribute_answer, clarification
    relation_context = RelationContext()
    from synonym_lexicon_v0626 import SynonymLexicon, learn_command, best_raw_mentions
    synonym_lexicon = SynonymLexicon(PROJECT_ROOT / "data" / "synonym_pairs_v0626.jsonl")
    from synonym_semantic_retrieval_v0628 import trace_match
    from synonym_candidate_review_v0627 import SynonymReview
    synonym_review = SynonymReview(PROJECT_ROOT / "data" / "synonym_candidates_v0627.jsonl", synonym_lexicon)
    from evaluate_memory_first_v0635 import load_overlay
    from approved_synonym_qa_v0637 import approved_qa_lookup
    approved_qa_overlay = load_overlay(args.approved_qa_overlay) if args.approved_qa_overlay else {}
    menu_topic_context = None
    from topic_scope_guard_v0638 import safe_greeting, scoped_followup
    active_evidence_topic = None
    active_evidence_extract = ""
    active_evidence_source = ""
    corpus_followup_context = None
    corpus_evidence_cursor = None
    last_explicit_knowledge_topic = None
    from followup_exhaustion_v074424 import FollowupExhaustion
    followup_exhaustion = FollowupExhaustion()
    from multi_topic_evidence_v0639 import TopicEvidenceContext
    topic_evidence = TopicEvidenceContext(max_topics=4)
    from persistent_topic_context_v0640 import save_context, load_context
    topic_context_file = PROJECT_ROOT / "data" / "topic_context_v0640.json"
    # v0.7.11: experimental adapter is opt-in and invoked only on the
    # structured UNKNOWN_KNOWLEDGE path (not TRUTH_BLOCK/INTERNALIZED_STALE).
    from experimental_quality_gate_v0711 import fallback_on_structured_unknown
    experimental_backend = None
    if os.environ.get("LLM_CHA_EXPERIMENTAL_FALLBACK", "0") == "1":
        from experimental_backend_v0711 import ExperimentalBackend
        experimental_backend = ExperimentalBackend(
            PROJECT_ROOT / "model" / "model-gpu-v1.6.2-online.pt",
            PROJECT_ROOT / "model" / "tokenizer-v0.7-bpe.json",
            PROJECT_ROOT / "results" / "adapter_sweep_v077_full" /
                "r16_e30_lr1e-03" / "experimental-adapter.pt",
        )
    # v0.7.21 Memory-First is separately opt-in; default chat.py unchanged.
    memory_first_enabled = os.environ.get("LLM_CHA_MEMORY_FIRST", "0") == "1"
    memory_first_mode = os.environ.get("LLM_CHA_MEMORY_FIRST_MODE", "evidence")
    if memory_first_enabled and memory_first_mode not in ("evidence", "constrained"):
        raise ValueError("LLM_CHA_MEMORY_FIRST_MODE must be evidence or constrained")
    from dual_runtime_bridge_v0721 import resolve as cha_memory_first_resolve
    memory_first_generator = None
    if memory_first_enabled and memory_first_mode == "constrained":
        if experimental_backend is None:
            from experimental_backend_v0711 import ExperimentalBackend
            memory_first_generator = ExperimentalBackend(
                PROJECT_ROOT / "model" / "model-gpu-v1.6.2-online.pt",
                PROJECT_ROOT / "model" / "tokenizer-v0.7-bpe.json",
                PROJECT_ROOT / "results" / "multi_fact_v0715" / "experimental-adapter.pt",
            )
        else:
            memory_first_generator = experimental_backend
    if memory_first_enabled and memory_first_mode == "constrained":
        from experimental_restore_v0724 import restore_latest
        restored_backend, restore_info = restore_latest(
            PROJECT_ROOT / "results" / "experimental_sleep_v0722",
            PROJECT_ROOT / "data" / "approved_v071.jsonl",
            PROJECT_ROOT / "data" / "candidates_v071.jsonl",
            PROJECT_ROOT / "model" / "model-gpu-v1.6.2-online.pt",
            PROJECT_ROOT / "model" / "tokenizer-v0.7-bpe.json")
        if restored_backend is not None:
            memory_first_generator = restored_backend
        print("[experimental startup restore: status={}, checked={}, candidate_count={}, checkpoint={}]".format(
            restore_info["status"],restore_info["checked"],
            restore_info.get("candidate_count",0),
            restore_info.get("checkpoint","-")))
    while True:
        try:
            user_text = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_text:
            continue
        # v0.7.44.42: interpret consent to the most recent approved topic offer.
        if pending_wiki_topic_offer is not None:
            normalized_topic_reply = user_text.strip().rstrip("。！？!? ")
            if normalized_topic_reply in ("はい", "うん", "ええ", "お願いします", "聞きたい", "そうして", "続けて"):
                from wiki_topic_memory_v074441 import begin_topic
                result = begin_topic(pending_wiki_topic_offer)
                pending_wiki_topic_offer = None
                print("AI> " + result.get("answer", "承認済みの話題を開始できなかった。もう一度、話題を提供して、と入力して。"))
                print("[route=WIKI_TOPIC_ACCEPTED, status={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]".format(result["status"]))
                print()
                continue
            if normalized_topic_reply in ("いいえ", "いや", "結構です", "やめる", "別の話題"):
                pending_wiki_topic_offer = None
                print("AI> 了解。別の話題にしよう。")
                print("[route=WIKI_TOPIC_DECLINED, train_ready=False]")
                print()
                continue
            pending_wiki_topic_offer = None
        # v0.8.0.2: explicit natural-language opt-in for unapproved knowledge.
        # This is not a global fallback: trusted and normal chat remain unchanged.
        from unapproved_conversation_v0802 import parse_unapproved_request, conversational_answer
        unapproved_question = parse_unapproved_request(user_text)
        if unapproved_question is not None:
            result=conversational_answer(unapproved_question)
            print("AI> " + result["answer"])
            print("[route=UNAPPROVED_CONVERSATIONAL_EVIDENCE, status={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, model_generated=False]".format(result["status"]))
            print()
            continue
        # v0.8.0.1: read-only structured Semantic candidate lookup.
        if user_text.startswith("/semantic-search "):
            from unapproved_semantic_search_v0801 import search_semantic
            query=user_text[len("/semantic-search "):].strip()
            result=search_semantic(query)
            print("AI> " + json.dumps(result,ensure_ascii=False))
            print("[route=UNAPPROVED_SEMANTIC_SEARCH, model_generated=False, train_ready=False, weights_changed=False]")
            print()
            continue
        # v0.7.44.47: explicit, read-only unapproved evidence comparison.
        if user_text.startswith("/wiki-compare "):
            from unapproved_llm_compare_v074447 import compare_answers
            query=user_text[len("/wiki-compare "):].strip()
            result=compare_answers(query)
            print("AI> " + json.dumps(result,ensure_ascii=False))
            print("[route=WIKI_UNAPPROVED_COMPARE, model_generated=False, train_ready=False, weights_changed=False]")
            print()
            continue
        # v0.7.44.46: isolated, unapproved knowledge intake. No weight updates.
        if user_text in ("/wiki-unapproved", "/wiki-intake"):
            from unapproved_llm_intake_v074446 import ingest_wikipedia
            result = ingest_wikipedia(cha_wiki_conversation.current)
            print("AI> 未承認Semantic候補: " + str(result))
            print("[route=WIKI_UNAPPROVED_INTAKE, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]")
            print()
            continue
        if user_text == "/wiki-unapproved-status":
            from unapproved_llm_intake_v074446 import inspect_candidates
            result = inspect_candidates()
            print("AI> " + json.dumps(result,ensure_ascii=False))
            print("[route=WIKI_UNAPPROVED_INSPECT, train_ready=False]")
            print()
            continue
        # v0.7.44.41: explicit Wikipedia topic memory workflow.
        # This stores externally sourced candidate text; never updates weights.
        if user_text in ("/wiki-learn", "Wikiを覚えて", "Wikipediaを覚えて"):
            from wiki_topic_memory_v074441 import learn_candidate
            result = learn_candidate(cha_wiki_conversation.current)
            print("AI> Wikipediaの話題候補: " + str(result))
            print("[route=WIKI_TOPIC_CANDIDATE, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]")
            print()
            continue
        if user_text.startswith("/wiki-approve "):
            from wiki_topic_memory_v074441 import approve_topic
            result = approve_topic(user_text.split(" ", 1)[1].strip())
            print("AI> " + str(result))
            print("[route=WIKI_TOPIC_APPROVAL, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]")
            print()
            continue
        from wiki_topic_intent_v074444 import is_topic_request
        if is_topic_request(user_text):
            from wiki_topic_memory_v074441 import suggest_topic
            result = suggest_topic()
            pending_wiki_topic_offer = result.get("id") if result["status"] == "FOUND" else None
            print("AI> " + result.get("answer", "承認済みのWikipedia話題候補はまだない。記事について会話した後、/wiki-learn を実行して。"))
            print("[route=WIKI_TOPIC_SUGGESTION, status={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]".format(result["status"]))
            print()
            continue
        if user_text in ("/context-save", "/context-load", "/context-clear"):
            try:
                if user_text == "/context-save":
                    save_context(topic_evidence, topic_context_file)
                    print("[route=CONTEXT_SAVE, file={}, topics={}]".format(topic_context_file,len(topic_evidence.items)))
                elif user_text == "/context-load":
                    restored_context = load_context(topic_context_file, max_topics=4)
                    topic_evidence = restored_context
                    current = topic_evidence.current()
                    active_evidence_topic = current["topic"] if current else None
                    active_evidence_extract = current["extract"] if current else ""
                    active_evidence_source = current["source"] if current else ""
                    print("[route=CONTEXT_LOAD, file={}, topics={}, active={}]".format(
                        topic_context_file,len(topic_evidence.items),topic_evidence.active))
                else:
                    topic_evidence.reset()
                    active_evidence_topic = None
                    active_evidence_extract = ""
                    active_evidence_source = ""
                    print("[route=CONTEXT_CLEAR, scope=session, saved_file_unchanged=True]")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                print("[context_error={}]".format(exc))
            print()
            continue
        # v0.6.39: explicit restoration of a previously evidenced topic.
        if not user_text.startswith("/"):
            restored = topic_evidence.restore(user_text)
            if restored is not None:
                if restored["status"] == "RESTORED":
                    active_evidence_topic = restored["topic"]
                    active_evidence_extract = restored["extract"]
                    active_evidence_source = restored["source"]
                    print("AI> {}の話題に戻りました。".format(active_evidence_topic))
                    print("[route=TOPIC_RESTORE, topic={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                        active_evidence_topic, active_evidence_source or "-"))
                else:
                    print("AI> その話題の記録はありません。")
                    print("[route=TOPIC_RESTORE_MISS, requested={}]".format(restored["requested"]))
                print()
                continue
        # v0.6.38: scoped followups cannot become unrelated generic Wikipedia lookups.
        if not user_text.startswith("/"):
            scoped = scoped_followup(user_text, active_evidence_topic, active_evidence_extract)
            if scoped is not None:
                print("AI> " + scoped["answer"])
                print("[route=CONTEXT_SCOPED_EVIDENCE, topic={}, attribute={}, grounded={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                    scoped["topic"], scoped["attribute"], scoped["grounded"], active_evidence_source or "-"))
                print()
                continue
            greeting = safe_greeting(user_text)
            if greeting is not None:
                print("AI> " + greeting)
                print("[route=SAFE_GREETING, model_generation=SKIPPED, train_ready=False]")
                print()
                continue
        # Approved exact-QA lookup is explicit opt-in, read-only, and never intercepts commands.
        if not user_text.startswith("/") and approved_qa_overlay:
            memory_hit = approved_qa_lookup(user_text, approved_qa_overlay, synonym_lexicon)
            if memory_hit is not None:
                print("AI> " + memory_hit["answer"])
                print("[route={}, source_id={}, matched_question={}, model_weights_unchanged=True]".format(
                    memory_hit["route"], memory_hit["source_id"], memory_hit["matched_question"]))
                print()
                continue
        # Explicit Japanese synonym declarations are learning actions,
        # and must not be sent to unguided model generation.
        from synonym_lexicon_v0626 import learn_natural_statement
        try:
            natural_synonym = learn_natural_statement(user_text, synonym_lexicon)
        except (ValueError, OSError) as exc:
            print("[synonym_error={}]".format(exc))
            natural_synonym = None
        if natural_synonym is not None:
            print("AI> 同義語を登録しました: " + " = ".join(natural_synonym["terms"]))
            print("[route=SYNONYM_NATURAL_LEARN, updated={}, model_weights_unchanged=True]".format(
                natural_synonym["added"]))
            print()
            continue
        if user_text.startswith("/synonym-propose "):
            source_text = user_text[len("/synonym-propose "):].strip()
            proposed = synonym_review.propose(source_text)
            print("AI> " + (", ".join("#{} {} = {}".format(r["id"],r["a"],r["b"]) for r in proposed)
                              if proposed else "新しい同義語候補はありません。"))
            print("[route=SYNONYM_CANDIDATE, pending={}, auto_promote=False]".format(len(synonym_review.pending())))
            print()
            continue
        if user_text=="/synonym-pending":
            pending = synonym_review.pending()
            print("AI> " + (", ".join("#{} {} = {}".format(r["id"],r["a"],r["b"]) for r in pending)
                              if pending else "承認待ちの候補はありません。"))
            print()
            continue
        if user_text.startswith("/synonym-approve ") or user_text.startswith("/synonym-reject "):
            approved = user_text.startswith("/synonym-approve ")
            try:
                record_id=int(user_text.split()[-1])
                decision=synonym_review.decide(record_id,approved)
                print("AI> " + ("候補 #{} を {}しました。".format(record_id,"承認" if approved else "拒否")
                                 if decision else "承認待ちの候補IDが見つかりません。"))
            except (ValueError,OSError,KeyError) as exc:
                print("[synonym_review_error={}]".format(exc))
            print()
            continue
        if user_text.startswith("/synonym-add "):
            try:
                learned = learn_command(user_text, synonym_lexicon)
                if learned is None:
                    print("AI> 書式: /synonym-add 語A = 語B")
                else:
                    print("AI> 同義語を登録しました: " + " = ".join(learned["terms"]))
                    print("[route=SYNONYM_LEARN, updated={}, model_weights_unchanged=True]".format(learned["added"]))
            except (OSError, ValueError, KeyError) as exc:
                print("[synonym_error={}]".format(exc))
            print()
            continue
        if user_text.startswith("/synonym-list "):
            try:
                term = user_text[len("/synonym-list "):].strip()
                print("AI> " + " = ".join(synonym_lexicon.expand(term)))
            except ValueError as exc:
                print("[synonym_error={}]".format(exc))
            print()
            continue
        if user_text=="/wiki status":
            print("[wiki_retry_status={}, last_user={}]".format(
                cha_wiki_retry_status,cha_wiki_retry_utterance or "-"))
            print()
            continue
        if user_text=="/persona-status":
            print("[persona_status="+json.dumps(cha_persona_status(cha_wiki_conversation.persona),ensure_ascii=False)+"]")
            print()
            continue
        if user_text=="/wiki" or user_text.startswith("/wiki "):
            explicit=user_text[6:].strip() if user_text.startswith("/wiki ") else None
            previous=cha_wiki_retry_utterance
            result=cha_wiki_retry(previous,explicit=explicit)
            if result["status"]=="EVIDENCE_FOUND":
                result=cha_persona_wiki_repair(previous,result,explicit=bool(explicit),persona=cha_wiki_conversation.persona)
            cha_wiki_retry_status=result["status"]
            print("[wiki_retry={}, topic={}, previous_user={}, verified=False, train_ready=False]".format(
                result["status"],result.get("topic","-"),previous or "-"))
            if result["status"]=="EVIDENCE_FOUND":
                comparison=cha_wiki_answer_assess(
                    cha_wiki_last_generated,result["evidence_span"],result["topic"],result.get("source"))
                print("[wiki_answer_assessment={}, reason={}, correction_approved=False]".format(
                    comparison["status"],comparison["reason"]))
            print("AI> "+result["answer"])
            if result.get("source"):
                print("[route={}, source={}, truth_state=EXTERNAL_UNVERIFIED, promoted=False]".format(result["route"],result["source"]))
            print()
            continue
        # v0.6.10: stateful, opt-in literature dialogue; preserve teaching guards.
        if aozora_dialogue is not None and not user_text.startswith("/") and cha_unknown_teacher.pending is None and cha_correction_session.pending is None:
            # Treat an explicitly learned cat alias as the canonical cat topic.
            # Keep the raw user utterance for logs and other routes.
            literature_query = user_text
            if (user_text in synonym_lexicon.expand("猫")
                    and user_text != "猫"):
                literature_query = "猫"
                print("[synonym_topic_route, input={}, canonical=猫]".format(user_text))
            literature_result = aozora_dialogue.respond(literature_query)
            if literature_result is not None:
                literature_answer, literature_meta = literature_result
                print("AI> " + literature_answer)
                print("[aozora="+json.dumps(literature_meta,ensure_ascii=False)+"]")
                print()
                continue
        if not user_text.startswith("/"):
            cha_wiki_retry_utterance=user_text
            cha_wiki_last_generated=None

        if cha_correction_session.pending is not None:
            try:
                response = cha_correction_session.respond(cha_unknown_teacher.path,user_text)
                print(f"AI> {response}")
            except (OSError,ValueError,KeyError) as exc:
                print(f"[correction error: {exc}]")
            print()
            continue
        if cha_unknown_teacher.pending is not None:
            try:
                response = cha_unknown_teacher.handle(user_text)
                print(f"AI> {response}")
            except (OSError, ValueError, KeyError) as exc:
                print(f"[unknown teaching error: {exc}]")
            print()
            continue
        if user_text.lower() == "/cancel":
            print("[no pending UNKNOWN teaching]")
            print()
            continue
        if cha_feedback_session.candidate_id is not None:
            try:
                feedback_result = cha_feedback_session.respond(
                    user_text, cha_unknown_teacher.path
                )
                if feedback_result is not None:
                    print(json.dumps(feedback_result, ensure_ascii=False, indent=2))
                    print("[feedback=EXPLICIT_USER, duplicate_prevented=True]")
                    if feedback_result["operational_status"]=="CONTESTED" and classify_feedback(user_text)=="negative":
                        print("AI> "+cha_correction_session.start(
                            cha_unknown_teacher.path,feedback_result["id"]))
                    print()
                    continue
            except (OSError, ValueError, KeyError) as exc:
                cha_feedback_session.clear()
                print(f"[natural feedback error: {exc}]")
            # Feedback applies only to the immediately following user turn.
            cha_feedback_session.clear()
        if user_text.startswith("/cha-wiki "):
            term=user_text.split(None,1)[1].strip()
            print(json.dumps(cha_wikipedia_lookup(term),ensure_ascii=False,indent=2))
            print()
            continue
        if user_text.startswith("/cha-terms "):
            phrase=user_text.split(None,1)[1]
            print(json.dumps(cha_unknown_term_probe(phrase),ensure_ascii=False,indent=2))
            print()
            continue
        if user_text.startswith("/cha-usage "):
            try:
                number = int(user_text.split(None,1)[1].strip())
                print(json.dumps(cha_usage_summary(cha_unknown_teacher.path,number),ensure_ascii=False,indent=2))
            except (OSError,ValueError,KeyError) as exc:
                print(f"[usage status error: {exc}]")
            print()
            continue
        if user_text.startswith("/cha-feedback "):
            try:
                parts=user_text.split()
                if len(parts)!=3 or parts[2] not in ("+","-"):
                    raise ValueError("syntax: /cha-feedback ID + or -")
                number=int(parts[1])
                outcome="positive" if parts[2]=="+" else "negative"
                print(json.dumps(cha_usage_update(cha_unknown_teacher.path,number,outcome),
                                 ensure_ascii=False,indent=2))
            except (OSError,ValueError,KeyError) as exc:
                print(f"[feedback error: {exc}]")
            print()
            continue
        if user_text.startswith("/cha-review "):
            concept = user_text.split(None, 1)[1].strip()
            try:
                print(json.dumps(cha_review_inspect(cha_unknown_teacher.path, concept),
                                 ensure_ascii=False, indent=2))
            except (OSError, ValueError, KeyError) as exc:
                print(f"[candidate review error: {exc}]")
            print()
            continue
        if user_text.startswith("/cha-ack "):
            try:
                candidate_id = int(user_text.split(None, 1)[1].strip())
                print(json.dumps(cha_review_approve(cha_unknown_teacher.path, candidate_id),
                                 ensure_ascii=False, indent=2))
            except (OSError, ValueError, KeyError) as exc:
                print(f"[candidate acknowledgement error: {exc}]")
            print()
            continue
        if user_text.startswith("/cha-unknown "):
            concept = user_text.split(None, 1)[1].strip()
            try:
                print(json.dumps(cha_unknown_teacher.lookup(concept), ensure_ascii=False, indent=2))
            except (OSError, ValueError, KeyError) as exc:
                print(f"[unknown lookup error: {exc}]")
            print()
            continue

        taught_reply = cha_teaching_review(cha_unknown_teacher, user_text)
        if taught_reply is not None:
            print(f"AI> {taught_reply['answer']}")
            cha_feedback_session.offered([
                evidence["record_number"] for evidence in taught_reply["records"]
            ])
            for evidence in taught_reply["records"]:
                try:
                    cha_usage_update(cha_unknown_teacher.path, evidence["record_number"], "used")
                except (OSError,ValueError,KeyError) as exc:
                    print(f"[usage recording error: {exc}]")
            print("[route=TEACHING_RETRIEVAL, truth_state=USER_REPORTED_UNVERIFIED, trusted=False, train_ready=False]")
            if cha_feedback_session.candidate_id is not None:
                print("[feedback_prompt=この説明は正しいですか？ はい／いいえ]")
            print()
            continue

        raw_user_text = user_text
        # v0.7.44.39: a follow-up after on-demand equation display continues
        # the equation explanation before unrelated Wikipedia prose.
        followup_text = raw_user_text.strip().rstrip("。！？!? ")
        if pending_equation_explanation is not None:
            wiki_now = cha_wiki_conversation.current
            if (followup_text in ("もっと詳しく", "もう少し詳しく", "詳しく", "詳しく教えて")
                    and isinstance(wiki_now, dict)
                    and (wiki_now.get("title"), wiki_now.get("url")) == pending_equation_explanation):
                meaning = cha_wiki_equation_cursor.explain_once(wiki_now)
                pending_equation_explanation = None
                if meaning is not None:
                    print("AI> " + meaning["answer"])
                    print("[route=EQUATION_SEMANTIC_FOLLOWUP, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(meaning["source"]))
                    last_ai_reply = None
                    print()
                    continue
            else:
                pending_equation_explanation = None
        # v0.7.44.38: explicit equation request must not fall into free generation.
        if (os.environ.get("LLM_CHA_ASPECT_EVIDENCE", "0") == "1"
                and raw_user_text.strip().rstrip("。！？!? ") in ("数式の意味", "数式を説明", "数式について教えて")
                and isinstance(cha_wiki_conversation.current, dict)):
            wiki = cha_wiki_conversation.current
            explanation = cha_wiki_equation_cursor.explain_once(wiki)
            if explanation is None:
                equations = cha_wiki_equation_cursor.next(wiki)
                if equations is not None:
                    explanation = {"answer": equations["answer"], "source": equations["source"],
                                   "route": "EQUATION_EVIDENCE_ON_DEMAND"}
            if explanation is None:
                answer = "現在のWikipedia記事から、説明可能な数式の根拠を取得できない。"
                source = wiki.get("url", "-")
                route = "EQUATION_EVIDENCE_INSUFFICIENT"
            else:
                answer = explanation["answer"]
                source = explanation["source"]
                route = explanation.get("route", "EQUATION_SEMANTIC_EVIDENCE")
            pending_equation_explanation = (wiki.get("title"), wiki.get("url")) if route == "EQUATION_EVIDENCE_ON_DEMAND" else None
            print("AI> " + answer)
            print("[route={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(route, source))
            last_ai_reply = None
            print()
            continue
        # v0.7.44.25: resolve explicitly selected aspect from current source.
        # No sentence is generated when the article lacks aspect evidence.
        if (os.environ.get("LLM_CHA_ASPECT_EVIDENCE","0") == "1"
                and last_explicit_knowledge_topic):
            from aspect_evidence_v074425 import choose_aspect, extract_aspect
            aspect = choose_aspect(raw_user_text)
            if aspect is not None:
                allowed = truth_allows_direct_retrieval(
                    effective_truth_record(truth_store_path, last_explicit_knowledge_topic).state)
                wiki_for_aspect = cha_wiki_conversation.current
                if allowed:
                    # Corpus/raw-Wikipedia parallel results may not populate
                    # the active Wiki Conversation. Resolve the actual topic.
                    if (not isinstance(wiki_for_aspect, dict)
                            or wiki_for_aspect.get("title") != last_explicit_knowledge_topic):
                        try:
                            wiki_for_aspect = cha_wikipedia_lookup(
                                last_explicit_knowledge_topic,
                                context=last_explicit_knowledge_topic + "とは")
                        except (OSError, ValueError, KeyError, TimeoutError, TypeError):
                            wiki_for_aspect = None
                    from wiki_expanded_aspect_v074426 import expanded_aspect
                    selected = expanded_aspect(wiki_for_aspect, aspect)
                else:
                    selected = None
                if selected is not None:
                    print("AI> " + selected["answer"])
                    print("[route=ASPECT_EVIDENCE, topic={}, aspect={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                        last_explicit_knowledge_topic, aspect, selected["source"]))
                else:
                    print("AI> 「{}」の「{}」について、現在の資料には明確な根拠がない。".format(
                        last_explicit_knowledge_topic, aspect))
                    print("[route=ASPECT_EVIDENCE_INSUFFICIENT, train_ready=False, auto_promote=False]")
                print()
                last_ai_reply = None
                continue
        # v0.7.44.23: remember explicit knowledge topic, not any model reply.
        # This guards the fallback route when a follow-up has no evidence.
        if raw_user_text.endswith(("とは", "とは？", "とは?")):
            last_explicit_knowledge_topic = raw_user_text.split("とは", 1)[0].strip()
            followup_exhaustion.reset()
        elif raw_user_text.strip().rstrip("。！？? ") not in (
                "もっと詳しく", "もう少し詳しく", "詳しく", "詳しく教えて",
                "もっと詳しく教えて", "もう少し詳しく教えて"):
            last_explicit_knowledge_topic = None
            followup_exhaustion.reset()
        # v0.7.44.15: corpus follow-ups are intentionally scoped to the
        # immediately preceding corpus reply. No further evidence is invented.
        from corpus_followup_v074415 import corpus_followup, FOLLOWUPS
        if os.environ.get("LLM_CHA_CORPUS_FOLLOWUP", "0") == "1":
            guarded_followup = corpus_followup(raw_user_text, corpus_followup_context)
            if guarded_followup is not None:
                # The cursor never returns an already presented proposition.
                if (corpus_evidence_cursor is not None
                        and corpus_evidence_cursor.subject == corpus_followup_context["subject"]):
                    from evidence_cursor_v074416 import render_unverified
                    next_record = corpus_evidence_cursor.next_evidence(corpus_followup_context["subject"])
                    if next_record is not None:
                        print("AI> " + render_unverified(next_record))
                        print("[route=CORPUS_EVIDENCE_CURSOR, proposition_id={}, truth_state=UNVERIFIED, train_ready=False, auto_promote=False]".format(next_record.proposition_id))
                        print()
                        last_ai_reply = None
                        continue
                print("AI> " + guarded_followup["answer"])
                print("[route={}, topic={}, truth_state=UNVERIFIED, train_ready=False, auto_promote=False]".format(
                    guarded_followup["route"], corpus_followup_context["subject"]))
                print()
                corpus_followup_context = None
                last_ai_reply = None
                continue
        # Invalidate on any non-follow-up user turn to avoid topic leakage.
        if raw_user_text.strip().rstrip("。!?？") not in FOLLOWUPS:
            corpus_followup_context = None
            corpus_evidence_cursor = None
        # v0.7.44.10 opt-in narrow Japanese daily-chat intent guard.
        # Never promote a conversational acknowledgement to trusted evidence.
        if os.environ.get("LLM_CHA_DAILY_CHAT", "0") == "1":
            from daily_chat_intent_v074410 import chat_reply
            daily_reply = chat_reply(raw_user_text, synonym_lexicon)
            if daily_reply is not None:
                print("AI> " + daily_reply["answer"])
                print("[route=DAILY_CHAT_INTENT, intent={}, persona=ngt_presentation, truth_state=NONFACTUAL, train_ready=False, auto_promote=False]".format(
                    daily_reply["intent"]))
                print()
                last_ai_reply = None
                cha_wiki_last_generated = None
                continue
        # v0.7.44.14: opt-in, narrowly scoped alias normalization.
        # Preserve the literal utterance for provenance and diagnostics;
        # only the downstream lookup query is rewritten.
        if os.environ.get("LLM_CHA_TOPIC_NORMALIZE", "0") == "1":
            from topic_recovery_v074413 import resolve as cha_topic_resolve
            cha_topic_plan = cha_topic_resolve(raw_user_text)
            if cha_topic_plan.status == "NORMALIZED":
                # Existing downstream handlers also read raw_user_text, so
                # reassigning user_text alone would NOT reliably reroute it.
                # Resolve the normalized query via the established wiki path.
                target = cha_topic_plan.topic
                if (truth_allows_direct_retrieval(
                        effective_truth_record(truth_store_path, raw_user_text).state)
                        and truth_allows_direct_retrieval(
                            effective_truth_record(truth_store_path, target).state)):
                    normalized_wiki = cha_unknown_wiki_fallback(
                        target, cha_topic_plan.query,
                        cha_wiki_conversation.persona, cha_wikipedia_lookup,
                        cha_persona_wiki_respond,
                        grounded=cha_wiki_grounded_reply,
                        cache=cha_persona_wiki_cache)
                    if (normalized_wiki.get("status") == "FOUND"
                            and normalized_wiki.get("answer")
                            and normalized_wiki.get("source")
                            and normalized_wiki.get("wiki_context")):
                        # v0.7.44.20: a successful alias lookup must become
                        # the active evidence context for subsequent follow-ups.
                        # Otherwise older topics (e.g. 量子ビット) leak through.
                        cha_wiki_conversation.offer(normalized_wiki["wiki_context"])
                        print("AI> " + normalized_wiki["answer"])
                        print("[route=TOPIC_ALIAS_WIKIPEDIA, input={}, topic={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                            raw_user_text, target, normalized_wiki["source"]))
                        print()
                        last_ai_reply = None
                        cha_wiki_last_generated = None
                        continue
        relation = relation_context.observe(raw_user_text)
        if relation is not None and relation["subject"] != "スターバックス":
            # No answer is invented from a Wikipedia article that lacks attribute evidence.
            try:
                from wikipedia_relation_evidence_v0621 import article_evidence
                relation_article = article_evidence(relation["subject"], relation["attribute"])
                print("[relation_evidence_status={}, reason={}, subject={}, attribute={}, extract_chars={}]".format(
                    relation_article.get("status"), relation_article.get("reason","-"),
                    relation["subject"], relation["attribute"], relation_article.get("extract_chars","-")))
                relation_grounded = ({"answer":relation_article["answer"],"source":relation_article["source"]}
                                     if relation_article["status"] == "FOUND" else None)
            except (OSError, ValueError, KeyError, TimeoutError):
                relation_grounded = None
            if relation_grounded:
                print("AI> " + relation_grounded["answer"])
                print("[route=SEMANTIC_RELATION_WIKIPEDIA, subject={}, attribute={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                    relation["subject"], relation["attribute"], relation_grounded["source"]))
            else:
                print("AI> " + clarification(relation))
                print("[route=SEMANTIC_RELATION_CLARIFY, subject={}, attribute={}, train_ready=False]".format(
                    relation["subject"], relation["attribute"]))
            print()
            continue
        # v0.6.19: intent resolution precedes unrestricted model generation.
        from menu_intent_v0619 import menu_request, menu_answer
        if raw_user_text in ("スターバックス", "スターバックスの話題"):
            menu_topic_context = "スターバックス"
        menu_intent = menu_request(raw_user_text, menu_topic_context)
        if menu_intent is not None:
            menu_reply = menu_answer(menu_intent)
            print("AI> " + menu_reply)
            print("[route=MENU_INTENT_CLARIFY, topic={}, aspect={}, truth_state=NO_UNSUPPORTED_MENU_FACTS, train_ready=False]".format(
                menu_intent.get("topic","UNRESOLVED"), menu_intent["aspect"]))
            if menu_intent["status"] == "FOUND":
                menu_topic_context = menu_intent["topic"]
            print()
            last_ai_reply = menu_reply
            continue
        if raw_user_text not in ("スターバックス", "スターバックスの話題"):
            menu_topic_context = None
        cha_sharing=cha_persona_context.handle(raw_user_text)
        if cha_sharing is not None:
            wiki_auto=cha_persona_auto_wiki_enrich(
                raw_user_text,cha_wiki_conversation.persona,
                cha_wikipedia_lookup,cha_persona_wiki_respond,
                cache=cha_persona_wiki_cache)
            if wiki_auto["status"]=="FOUND":
                cha_wiki_conversation.offer(wiki_auto["wiki_context"])
                print("AI> "+wiki_auto["answer"])
                print("[route=PERSONA_AUTO_WIKIPEDIA, term={}, source={}, truth_state=EXTERNAL_UNVERIFIED, verified=False, train_ready=False, auto_promote=False]".format(
                    wiki_auto["term"],wiki_auto["source"]))
                last_ai_reply=None
                cha_wiki_last_generated=None
                print()
                continue
            print("AI> "+cha_sharing["answer"])
            print("[route={}, persona={}, intent={}, knowledge_asserted=False, train_ready=False]".format(
                cha_sharing["route"],cha_sharing["persona"],cha_sharing["intent"]))
            last_ai_reply=None
            cha_wiki_last_generated=None
            print()
            continue
        topic_followup=cha_wiki_topic_followup(
            raw_user_text,cha_wiki_conversation.current,
            cha_wiki_conversation.persona,cha_wikipedia_lookup,
            cha_persona_wiki_respond,grounded=cha_wiki_grounded_reply,
            cache=cha_persona_wiki_cache)
        if topic_followup["status"]=="FOUND":
            cha_wiki_conversation.offer(topic_followup["wiki_context"])
            print("AI> "+topic_followup["answer"])
            print("[route=PERSONA_WIKIPEDIA_TOPIC_FOLLOWUP, term={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                topic_followup["term"],topic_followup["source"]))
            last_ai_reply=None
            cha_wiki_last_generated=None
            print()
            continue
        wiki_followup=cha_wiki_conversation.respond(raw_user_text)
        if (wiki_followup is not None
                and wiki_followup.get("route")=="PERSONA_WIKIPEDIA_CONTEXT_FOLLOWUP"):
            from wiki_topic_memory_v074441 import observe_followup
            learned=observe_followup(cha_wiki_conversation.current)
            from wiki_topic_memory_v074441 import record_used_evidence
            evidence_saved=record_used_evidence(cha_wiki_conversation.current, wiki_followup.get("answer",""))
            print("[wiki_evidence_memory={}, added={}, total={}, train_ready=False]".format(
                evidence_saved.get("status"),evidence_saved.get("added",0),evidence_saved.get("total",0)))
            print("[wiki_interest_learning={}, count={}, state={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]".format(
                learned.get("status"),learned.get("count",0),learned.get("state","-")))
        if wiki_followup is not None:
            if wiki_followup["route"]=="WIKIPEDIA_EVIDENCE_INSUFFICIENT" and cha_wiki_conversation.current is not None:
                more_detail=cha_wiki_evidence_session.next(
                    cha_wiki_conversation.current,raw_user_text,
                    persona=cha_wiki_conversation.persona)
                print("[wiki_evidence_session={}, reason={}, segments={}, candidates={}, eligible={}, seen_eligible={}, extended_chars={}, remainder_chars={}]".format(
                    more_detail.get("status", "UNKNOWN"),
                    more_detail.get("reason", more_detail.get("error", "-")),
                    more_detail.get("segments", "-"),
                    more_detail.get("candidates", "-"),
                    more_detail.get("eligible", "-"),
                    more_detail.get("seen_eligible", "-"),
                    more_detail.get("extended_chars", "-"),
                    more_detail.get("remainder_chars", "-")))
                if more_detail.get("status")=="EVIDENCE_EXHAUSTED":
                    for rejected in more_detail.get("rejected_samples", []):
                        print("[wiki_evidence_reject={} ]".format(
                            json.dumps(rejected, ensure_ascii=False)))
                if more_detail["status"]=="FOUND":
                    print("AI> "+more_detail["answer"])
                    print("[route={}, source={}, truth_state=EXTERNAL_UNVERIFIED, verified=False, train_ready=False, quality_gate={}]".format(
                        more_detail["route"],more_detail["source"],more_detail["quality_gate"]))
                    last_ai_reply=None
                    cha_wiki_last_generated=None
                    print()
                    continue
                if more_detail["status"]=="EVIDENCE_EXHAUSTED":
                    meaning = cha_wiki_equation_cursor.explain_once(cha_wiki_conversation.current)
                    if meaning is not None:
                        print("AI> " + meaning["answer"])
                        print("[route=EQUATION_SEMANTIC_EVIDENCE, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(meaning["source"]))
                        last_ai_reply=None
                        cha_wiki_last_generated=None
                        print()
                        continue
                    equation = cha_wiki_equation_cursor.next(cha_wiki_conversation.current)
                    if equation is not None:
                        print("AI> " + equation["answer"])
                        print("[route=WIKIPEDIA_EQUATION_EVIDENCE, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False, quality_gate=SOURCE_WIKITEXT_MATH_EXACT]".format(equation["source"]))
                        last_ai_reply=None
                        cha_wiki_last_generated=None
                        print()
                        continue
                    continuation=cha_wiki_evidence_continuation.next(
                        cha_wiki_conversation.current,raw_user_text,
                        persona=cha_wiki_conversation.persona)
                    print("[wiki_evidence_continuation={}, visited={}]".format(
                        continuation.get("status"),len(continuation.get("visited",[]))))
                    if continuation["status"]=="FOUND":
                        print("[wiki_evidence_scope={}, origin_title={}, article_title={}, source={}, truth_state=EXTERNAL_UNVERIFIED]".format(
                            continuation.get("evidence_scope","UNKNOWN"), continuation.get("origin_title","-"),
                            continuation.get("title","-"), continuation.get("source","-")))
                        print("AI> "+continuation["answer"])
                        print("[route={}, source={}, truth_state=EXTERNAL_UNVERIFIED, verified=False, train_ready=False, auto_promote=False, quality_gate={}]".format(
                            continuation["route"],continuation["source"],continuation["quality_gate"]))
                        last_ai_reply=None
                        cha_wiki_last_generated=None
                        print()
                        continue
                expanded=cha_expand_wiki_evidence(cha_wiki_conversation.current,raw_user_text)
                print("[wiki_evidence_expansion={}, intent={}]".format(expanded["status"],expanded["intent"]))
                if expanded["status"] not in ("FOUND","LOOKUP_FAILED"):
                    related=cha_wiki_discover(cha_wiki_conversation.current,raw_user_text)
                    print("[wiki_related_discovery={}, intent={}, visited={}]".format(
                        related["status"],related["intent"],len(related.get("visited",[]))))
                    if related["status"]=="FOUND":
                        expanded=related
                if expanded["status"]!="FOUND" and raw_user_text.find("なぜ")>=0:
                    diagnostic=cha_wiki_multihop_probe(cha_wiki_conversation.current,raw_user_text)
                    print("[wiki_multihop_diagnostic={}, visited={}, edges={}, answer_used=False]".format(
                        diagnostic["status"],len(diagnostic.get("visited",[])),diagnostic.get("edge_candidates",0)))
                    if diagnostic.get("edge_candidates",0)==0 and diagnostic["status"]=="NO_SUPPORTED_CHAIN":
                        extraction_report=cha_wiki_causal_diagnose(cha_wiki_conversation.current)
                        counts=extraction_report.get("totals",{})
                        print("[wiki_causal_diagnostics={}, sentences={}, no_marker={}, ambiguous={}, edges={}]".format(
                            extraction_report["status"],counts.get("sentences",0),
                            counts.get("NO_CAUSAL_MARKER",0),counts.get("INVALID_OR_AMBIGUOUS_EDGE",0),
                            counts.get("EDGE_EXTRACTED",0)))
                        print("[wiki_propositions=atomic_typed, count={}, verified=False, promoted=False]".format(
                            counts.get("typed_propositions",0)))
                        for example in extraction_report.get("samples",[]):
                            print("[wiki_causal_reject={}, article={}, excerpt={}]".format(
                                example["reason"],example["article"],example["excerpt"]))
                    if diagnostic["status"]=="CHAIN_FOUND":
                        for hop_index,hop in enumerate(diagnostic["hops"],1):
                            print("[wiki_multihop_edge={}, cause={}, effect={}, source={}]".format(
                                hop_index,hop["cause"],hop["effect"],hop["source"]))
                if expanded["status"]!="FOUND" and cha_wiki_conversation.current is not None:
                    wiki_current=cha_wiki_conversation.current
                    wiki_excerpt=wiki_current.get("extract","")
                    wiki_sentence=wiki_excerpt.split("。")[0].strip()+"。" if wiki_excerpt else ""
                    relation_review=cha_wiki_relation_assess(raw_user_text,wiki_sentence,wiki_current.get("url"))
                    print("[wiki_relation_tiers={}, means={}, explicit_direction={}, causal_answer_approved=False]".format(
                        relation_review["status"],relation_review.get("means_count",0),
                        relation_review.get("explicit_direction_count",0)))
                    alignment=cha_wiki_relation_align(raw_user_text,wiki_sentence,wiki_current.get("url"))
                    print("[wiki_relation_alignment={}, aligned={}, causal_answer_approved=False]".format(
                        alignment["status"],alignment.get("aligned_count",0)))
                    multi_evidence=cha_wiki_multi_evidence_analyze(wiki_current,raw_user_text)
                    print("[wiki_multi_evidence={}, articles={}, propositions={}, aligned={}, causal_answer_approved=False]".format(
                        multi_evidence["status"],len(multi_evidence.get("articles",[])),
                        len(multi_evidence.get("propositions",[])),
                        len(multi_evidence.get("aligned_candidates",[]))))
                    coverage_summary=cha_wiki_coverage_summary(multi_evidence)
                    if coverage_summary["status"]=="COMPARISON_DIAGNOSTIC":
                        comparison_counts=coverage_summary["comparison_counts"]
                        print("[wiki_extraction_coverage=DIAGNOSTIC, comparison_match={}, conflict={}, complement={}, insufficient={}]".format(
                            comparison_counts["MATCH"],comparison_counts["CONFLICT"],
                            comparison_counts["COMPLEMENT"],comparison_counts["INSUFFICIENT"]))
                        for article_report in multi_evidence.get("articles",[]):
                            c=article_report["coverage"]["counts"]
                            print("[wiki_article_coverage={}, sentences={}, extracted={}, propositions={}, unsupported={}]".format(
                                article_report["title"],c.get("sentences",0),c.get("EXTRACTED",0),
                                c.get("propositions",0),c.get("unextracted_sentences",0)))
                    partial=cha_wiki_partial_why(raw_user_text,wiki_sentence,wiki_current.get("url"))
                    print("[wiki_partial_means={}, causal_explanation=False]".format(partial["status"]))
                    if partial["status"]=="PARTIAL_MEANS_EVIDENCE":
                        wiki_followup={
                            "answer":partial["answer"],
                            "route":"PERSONA_WIKIPEDIA_PARTIAL_MEANS",
                            "source":partial["source"],
                            "quality_gate":partial["quality_gate"]}
                if expanded["status"]=="FOUND":
                    try:
                        comparison=cha_wiki_compare_store(expanded,resolve_runtime_path(args.propositions))
                        print("[wiki_semantic_comparison={}, matches={}, conflicts={}, promoted=False]".format(
                            comparison["status"],len(comparison["matches"]),len(comparison["conflicts"])))
                    except (OSError,ValueError,KeyError) as exc:
                        print("[wiki_semantic_comparison=UNAVAILABLE, reason={}]".format(type(exc).__name__))
                    sentence=expanded["sentence"].rstrip("。")
                    wiki_followup={
                        "answer":"Wikipediaには、"+sentence+"とある。",
                        "route":"PERSONA_WIKIPEDIA_EXPANDED_EVIDENCE",
                        "source":expanded["source"],
                        "quality_gate":expanded["quality_gate"]}
            print("AI> " + wiki_followup["answer"])
            print("[route={}, source={}, verified=False, train_ready=False, raw_generation=SKIPPED, quality_gate={}]".format(wiki_followup["route"],wiki_followup["source"],wiki_followup["quality_gate"]))
            print()
            last_ai_reply=None
            continue
        term_probe=cha_unknown_term_probe(raw_user_text)
        if term_probe["terms"]:
            term=term_probe["terms"][0]
            wiki_context=cha_wikipedia_lookup(term,context=raw_user_text)
            if wiki_context.get("status")=="FOUND":
                print("[wiki_context={}, status=EXTERNAL_UNVERIFIED, url={}]".format(
                    wiki_context["title"],wiki_context["url"]))
                print("[wiki_extract={}]".format(wiki_context["extract"][:240].replace("\\n"," ")))
                print("[wiki_keywords={}]".format(",".join(wiki_context["keywords"])))
                grounded=cha_persona_wiki_respond(wiki_context,raw_user_text,persona=cha_wiki_conversation.persona)
                if grounded is None:
                    grounded=cha_wiki_grounded_reply(wiki_context,raw_user_text)
                if grounded is not None:
                    cha_wiki_conversation.offer(wiki_context)
                    print("AI> "+grounded["answer"])
                    print("[route={}, source={}, verified=False, train_ready=False, raw_generation=SKIPPED, quality_gate={}]".format(
                        grounded["route"],grounded["source"],grounded.get("quality_gate","SOURCE_EXTRACT_FALLBACK")))
                    last_ai_reply=None
                    print()
                    continue
            else:
                print("[wiki_lookup={}, term={}]".format(wiki_context["status"],term))
        normalized_user_text = normalize_runtime_input(user_text)
        if normalized_user_text and normalized_user_text != user_text:
            print(f"[normalized input: {user_text!r} -> {normalized_user_text!r}]")
            user_text = normalized_user_text
        if not user_text:
            continue

        command = user_text.lower()

        if command.startswith("/cha-load ") or command.startswith("/cha-recall ") or command in ("/cha-start", "/cha-status", "/cha-close", "/cha-sleep", "/cha-migrate"):
            try:
                if command == "/cha-start":
                    print(f"[CHA memory started: {cha_bridge.start()}]")
                elif command.startswith("/cha-load "):
                    print(json.dumps(cha_bridge.load_closed(user_text.split(None, 1)[1].strip()), ensure_ascii=False))
                    cha_user_context = UserContext()
                    cha_recent_topic = None
                elif command.startswith("/cha-recall "):
                    print(json.dumps(cha_bridge.recall(user_text.split(None, 1)[1].strip()), ensure_ascii=False, indent=2))
                elif command == "/cha-status":
                    print(json.dumps(cha_bridge.status(), ensure_ascii=False))
                elif command == "/cha-close":
                    print(json.dumps(cha_bridge.close(), ensure_ascii=False))
                elif command == "/cha-sleep":
                    print(json.dumps(cha_bridge.sleep(), ensure_ascii=False))
                elif command == "/cha-migrate":
                    print(json.dumps(cha_bridge.migrate(), ensure_ascii=False))
            except (OSError, ValueError, KeyError) as exc:
                print(f"[CHA memory error: {exc}]")
            print()
            continue

        if command in ("/exit", "exit", "quit"):
            break

        if command in ("/context-save", "/context-load"):
            if not context_recovery_path or topic_adapter is None:
                print("[context recovery disabled; set LLM_CHA_MULTITOPIC=1, LLM_CHA_CONTEXT_RECOVERY=1, LLM_CHA_CONTEXT_PATH]")
                print()
                continue
            try:
                from context_recovery_v023343 import save as context_save, load as context_load
                corpus_for_recovery = resolve_runtime_path(args.corpus_memory)
                if command == "/context-save":
                    count = context_save(
                        context_recovery_path, topic_adapter.context,
                        proposition_cursor, corpus_for_recovery
                    )
                    print(f"[context-save=OK, topics={count}]")
                else:
                    report = context_load(
                        context_recovery_path, topic_adapter, proposition_cursor,
                        corpus_for_recovery,
                        lambda subject: (
                            (lambda record: (record.state, truth_allows_direct_retrieval(record.state)))(
                                effective_truth_record(truth_store_path, subject)
                            )
                        ),
                        # Load the current overlay; never trust an old cached decision.
                        TruthOverlay(os.environ.get("LLM_CHA_PROPOSITION_TRUTH"))
                    )
                    print(f"[context-load=OK, retained={report.retained}, rejected={report.rejected}]")
            except (OSError, ValueError, TypeError) as exc:
                print(f"[context-recovery=ERROR, reason={exc}]")
            print()
            continue

        if command == "/reset":
            cha_persona_context.clear()
            if topic_adapter is not None:
                topic_adapter.context.reset()
                proposition_cursor.reset()
            history.clear()
            cha_recent_topic = None
            cha_user_context = UserContext()
            cha_wiki_conversation.clear()
            print("[conversation history cleared]")
            print()
            continue

        if command == "/info":
            print_info(
                model=model,
                tokenizer=tokenizer,
                checkpoint=checkpoint,
                device=device,
                model_path=model_path,
                tokenizer_path=tokenizer_path,
                args=args,
            )
            print("Learning capture :", learning_enabled)
            print("Learning log     :", learning_log)
            print("Saved pairs      :", learning_log_count(learning_log))
            print()
            continue

        if command == "/learn on":
            learning_enabled = True
            print("[learning capture enabled]")
            print()
            continue

        if command == "/learn off":
            learning_enabled = False
            print("[learning capture disabled]")
            print()
            continue

        if command == "/learn status":
            print(
                f"[learning={'ON' if learning_enabled else 'OFF'}, "
                f"pairs={learning_log_count(learning_log)}, "
                f"log={learning_log}]"
            )
            print()
            continue

        if command == "/condcandidates":
            rows = pending_conditional_candidates(
                conditional_candidate_path
            )
            if not rows:
                print("[conditional candidates: empty]")
            else:
                print(
                    f"[conditional candidates: {len(rows)} pending item(s)]"
                )
                for index, row in enumerate(rows, 1):
                    print(
                        f"  {index:02d}. "
                        f"subject={row.get('subject', '')!r} "
                        f"condition={row.get('condition', '')!r} "
                        f"predicate={row.get('predicate', '')!r}"
                    )
            print()
            continue

        if command.startswith("/condapprove "):
            target = user_text[len("/condapprove "):].strip().lower()
            if target == "all":
                approved = approve_conditional_candidate(
                    conditional_candidate_path,
                    conditional_proposition_path,
                    index=None,
                )
            else:
                try:
                    index = int(target)
                except ValueError:
                    print("[usage: /condapprove N | /condapprove all]")
                    print()
                    continue
                approved = approve_conditional_candidate(
                    conditional_candidate_path,
                    conditional_proposition_path,
                    index=index,
                )
            print(f"[conditional candidates approved: {approved}]")
            if approved:
                print("[approved candidates are now available for conditional retrieval]")
                print("[use /sleep to queue approved conditional knowledge for LLM internalization]")
            print()
            continue

        if command == "/conds":
            rows = load_conditional_propositions(
                conditional_proposition_path
            )
            if not rows:
                print("[conditional propositions: empty]")
            else:
                print(
                    f"[conditional propositions: {len(rows)} item(s)]"
                )
                for index, row in enumerate(rows, 1):
                    print(
                        f"  {index:02d}. subject={row.subject!r} "
                        f"condition={row.condition!r} "
                        f"predicate={row.predicate!r}"
                    )
            print()
            continue

        if command.startswith("/condteach "):
            statement = user_text[len("/condteach "):].strip()
            row = add_conditional_statement(
                conditional_proposition_path,
                statement,
            )
            if row is None:
                print(
                    "[conditional teaching rejected: expected a "
                    "condition-like statement such as 高温のCPUは停止する]"
                )
            else:
                print(
                    f"[conditional knowledge saved: "
                    f"subject={row.subject!r}, "
                    f"condition={row.condition!r}, "
                    f"predicate={row.predicate!r}]"
                )
                print(f"[canonical: {row.render()}]")
            print()
            continue

        if command == "/props":
            propositions = load_semantic_propositions(proposition_path)
            if not propositions:
                print("[semantic propositions: empty]")
            else:
                print(
                    f"[semantic propositions: {len(propositions)} atomic item(s)]"
                )
                for index, item in enumerate(propositions, 1):
                    print(
                        f"  {index:02d}. "
                        f"subject={item.subject!r} value={item.value!r}"
                    )
            print()
            continue

        if command.startswith("/propteach "):
            statement = user_text[len("/propteach "):].strip()
            added = semantic_knowledge.teach_proposition(statement)
            if not added:
                print(
                    "[proposition teaching rejected: expected "
                    "XはYである or Xは、Yであり、Zである]"
                )
            else:
                print(
                    f"[semantic knowledge teach: {len(added)} atomic item(s)]"
                )
                for item in added:
                    print(
                        f"  + subject={item.subject!r} value={item.value!r}"
                    )
                rendered = compose_semantic_proposition_subject(
                    proposition_path,
                    added[0].subject,
                )
                print(f"[proposition composed: {rendered}]")
                print(
                    "[semantic layers synchronized: "
                    "proposition -> subject -> typed -> unified]"
                )
            print()
            continue

        if command == "/propsync":
            sync = semantic_knowledge.sync_all()
            print(
                f"[semantic knowledge sync: "
                f"atomic={sync.atomic_count}, "
                f"subject_index={sync.subject_index_count}, "
                f"typed_index={sync.typed_index_count}, "
                f"unified_subjects={sync.unified_subject_count}]"
            )
            print()
            continue

        if command == "/batchstatus":
            plan = batch_repair_plan(
                Path(args.internalized_verification)
            )
            if plan.count == 0:
                print("[verification batch: no active repair tasks]")
            else:
                print(
                    f"[verification batch: tasks={plan.count}, "
                    f"fingerprints={len(plan.fingerprints)}, "
                    f"concepts={len(plan.concepts)}]"
                )
                for index, row in enumerate(plan.tasks, 1):
                    print(
                        f"  {index:02d}. "
                        f"concept={row.get('concept', '')!r} "
                        f"status={row.get('status', '')} "
                        f"attempts={row.get('attempts', 0)} "
                        f"fingerprint={str(row.get('fingerprint', ''))[:12]}"
                    )
            print()
            continue

        if command == "/verifystatus":
            summary = verification_summary(
                Path(args.internalized_verification)
            )
            print(
                f"[internalized verification: "
                f"pending={summary.pending}, "
                f"retrain={summary.retrain}, "
                f"verified={summary.verified}, "
                f"failed={summary.failed}, "
                f"total={summary.total}]"
            )
            print()
            continue

        if command == "/verifications":
            rows = active_verifications(
                Path(args.internalized_verification)
            )
            if not rows:
                print("[internalized verifications: no active tasks]")
            else:
                print(
                    f"[internalized verifications: {len(rows)} active task(s)]"
                )
                for index, row in enumerate(rows, 1):
                    missing = "|".join(
                        str(x) for x in row.get("missing_terms", [])
                    ) or "-"
                    print(
                        f"  {index:02d}. concept={row.get('concept', '')!r} "
                        f"status={row.get('status', '')} "
                        f"attempts={row.get('attempts', 0)} "
                        f"semantic={float(row.get('semantic', 0.0)):.3f} "
                        f"lexical={float(row.get('lexical', 0.0)):.3f} "
                        f"required={float(row.get('required', 0.0)):.3f} "
                        f"missing={missing}"
                    )
            print()
            continue

        if command == "/promotionstatus":
            summary = lifecycle_summary(
                Path(args.knowledge_queue)
            )
            print(
                f"[knowledge queue lifecycle: "
                f"pending={summary.pending}, "
                f"promoted={summary.promoted}, "
                f"verified={summary.verified}, "
                f"legacy_resolved={summary.legacy_resolved}, "
                f"other={summary.other}, "
                f"total={summary.total}]"
            )
            print()
            continue

        if command == "/promotions":
            pending = pending_knowledge_requests(
                Path(args.knowledge_queue)
            )
            if not pending:
                print("[knowledge promotions: no pending UNKNOWN_KNOWLEDGE requests]")
            else:
                print(
                    f"[knowledge promotions: {len(pending)} pending request(s)]"
                )
                for index, row in enumerate(pending, 1):
                    print(
                        f"  {index:02d}. user={row.get('user', '')!r}, "
                        f"reason={row.get('reason', '')!r}, "
                        f"timestamp={row.get('timestamp', '')!r}"
                    )
            print()
            continue

        if command.startswith("/promote "):
            payload = user_text[len("/promote "):].strip()
            if "=>" not in payload:
                print("[usage: /promote CONCEPT => STATEMENT]")
                print()
                continue

            concept, statement = [
                part.strip()
                for part in payload.split("=>", 1)
            ]
            if not concept or not statement:
                print("[usage: /promote CONCEPT => STATEMENT]")
                print()
                continue

            promotion = promote_knowledge(
                semantic_knowledge,
                Path(args.knowledge_queue),
                concept,
                statement,
            )
            if not promotion.promoted:
                print(
                    f"[knowledge promotion rejected: "
                    f"concept={concept!r}, reason={promotion.reason}]"
                )
            else:
                post = promotion.post_result
                truth_state = (
                    post.truth_state
                    if post is not None
                    else ""
                )
                print(
                    f"[knowledge promoted: concept={concept!r}, "
                    f"atomic={len(promotion.propositions)}, "
                    f"queue_promoted={promotion.queue_promoted}, "
                    f"post_state={post.state if post else '-'}, "
                    f"post_action={post.action if post else '-'}, "
                    f"truth_state={truth_state or '-'}]"
                )
                for item in promotion.propositions:
                    print(
                        f"  + {item.subject} => {item.value}"
                    )
                print(
                    "[promotion pipeline: UNKNOWN -> validated proposition "
                    "-> subject/typed/unified sync -> bare routing enabled]"
                )
            print()
            continue

        if command.startswith("/semantic "):
            concept = user_text[len("/semantic "):].strip()
            if not concept:
                print("[usage: /semantic CONCEPT]")
            else:
                snapshot = snapshot_semantic_knowledge(
                    semantic_knowledge,
                    concept,
                )
                result = snapshot.result
                state = result.knowledge_state
                dispatch = result.dispatch
                truth = result.truth
                truth_result = result.truth_result
                provenance = result.provenance

                print(
                    f"[semantic snapshot: concept={snapshot.concept!r}, "
                    f"query={snapshot.query!r}]"
                )

                if snapshot.atomic_propositions:
                    print(
                        f"  Proposition  : {snapshot.proposition_count} atomic item(s)"
                    )
                    for item in snapshot.atomic_propositions:
                        print(
                            f"    - {item.subject} => {item.value}"
                        )
                else:
                    print("  Proposition  : none")

                print(
                    "  Subject Index : "
                    + (snapshot.subject_answer or "none")
                )

                if snapshot.typed_rows:
                    print(
                        f"  Typed Index   : {snapshot.typed_count} item(s)"
                    )
                    for row in snapshot.typed_rows:
                        print(
                            f"    - {row.predicate_type}: {row.statement}"
                        )
                else:
                    print("  Typed Index   : none")

                if snapshot.unified_row is not None:
                    print(
                        "  Unified Memory: "
                        + str(snapshot.unified_row.get("assistant", ""))
                    )
                    print(
                        f"    source={snapshot.unified_row.get('source', '')!r}, "
                        f"updated_at={snapshot.unified_row.get('updated_at', '')!r}"
                    )
                else:
                    print("  Unified Memory: none")

                if snapshot.internalized is not None:
                    internalized = snapshot.internalized
                    print(
                        f"  Internalized : yes, "
                        f"trained_pairs={internalized.trained_pairs}, "
                        f"sources={','.join(internalized.sources)}"
                    )
                    print(
                        f"    latest_question={internalized.latest_question!r}"
                    )
                else:
                    print("  Internalized : no")

                if provenance is not None:
                    print(
                        f"  Provenance   : {provenance.compact()}"
                    )
                else:
                    print("  Provenance   : none")

                if truth is not None:
                    runtime_status = (
                        truth_result.runtime_status
                        if truth_result is not None
                        else "-"
                    )
                    warning = (
                        truth_result.warning
                        if truth_result is not None
                        else ""
                    )
                    print(
                        f"  Truth State  : {truth.state}, "
                        f"runtime={runtime_status}, warning={warning!r}"
                    )
                    if truth.correction:
                        print(
                            f"    correction={truth.correction}"
                        )
                else:
                    print("  Truth State  : none")

                print(
                    f"  Knowledge    : state={state.state}, "
                    f"reason={state.reason}"
                )
                print(
                    f"  Final Route  : action={dispatch.action}, "
                    f"route={dispatch.route}, "
                    f"reason={dispatch.reason}"
                )
                if dispatch.answer:
                    print(f"  Final Answer : {dispatch.answer}")
            print()
            continue

        if command == "/semstatus":
            status = semantic_knowledge.status()
            conditional_status = conditional_semantic_status(
                conditional_proposition_path,
                conditional_candidate_path,
                learning_state,
                checkpoint_trained_fingerprints(checkpoint),
            )
            print(
                f"[semantic knowledge architecture: "
                f"version={status['version']}, "
                f"layers={','.join(status['layers'])}]"
            )
            print(f"  proposition : {status['proposition_path']}")
            print(f"  subject     : {status['subject_index_path']}")
            print(f"  typed       : {status['typed_index_path']}")
            print(f"  unified     : {status['unified_path']}")
            print(f"  internalized: {status['learning_log']}")
            print(f"  truth       : {status['truth_store_path']}")
            print(
                f"  conditional : {conditional_proposition_path} "
                f"(stored={conditional_status.propositions}, "
                f"candidates={conditional_status.pending_candidates})"
            )
            print(
                f"  cond sleep  : internalized={conditional_status.internalized}, "
                f"pending={conditional_status.pending_internalization}"
            )
            print()
            continue

        if command == "/truths":
            records = load_truth_records(truth_store_path)
            if not records:
                print("[truth states: empty; unresolved concepts default to UNVERIFIED]")
            else:
                print(f"[truth states: {len(records)} explicit record(s)]")
                for index, record in enumerate(records, 1):
                    correction = (
                        f" correction={record.correction!r}"
                        if record.correction
                        else ""
                    )
                    print(
                        f"  {index:02d}. concept={record.concept!r} "
                        f"state={record.state} source={record.source} "
                        f"updated_at={record.updated_at!r}"
                        f"{correction}"
                    )
            print()
            continue

        if command.startswith("/truthset "):
            payload = user_text[len("/truthset "):].strip()
            left, sep, correction = payload.partition("=>")
            parts = left.strip().split()
            if len(parts) < 2:
                print(
                    "[usage: /truthset CONCEPT "
                    "TRUE|FALSE|UNVERIFIED|CONTESTED|OUTDATED "
                    "[=> CORRECTION]]"
                )
            else:
                concept = parts[0].strip()
                state_name = parts[1].strip().upper()
                if state_name not in TRUTH_STATES:
                    print(
                        "[invalid truth state: "
                        + state_name
                        + "; expected "
                        + "|".join(TRUTH_STATES)
                        + "]"
                    )
                else:
                    record = upsert_truth_record(
                        truth_store_path,
                        concept,
                        state_name,
                        correction=(correction.strip() if sep else ""),
                        source="chat-manual-truth",
                    )
                    print(
                        f"[truth state saved: concept={record.concept!r}, "
                        f"state={record.state}, "
                        f"correction={record.correction!r}, "
                        f"updated_at={record.updated_at!r}]"
                    )
                    if state_name == "TRUE":
                        verified_count = mark_concept_verified(
                            Path(args.knowledge_queue),
                            concept,
                            truth_source="chat-manual-truth",
                        )
                        if verified_count:
                            print(
                                f"[knowledge queue verified: "
                                f"concept={concept!r}, "
                                f"entries={verified_count}]"
                            )
                    else:
                        revoked_count = revoke_concept_verification(
                            Path(args.knowledge_queue),
                            concept,
                            new_truth_state=state_name,
                        )
                        if revoked_count:
                            print(
                                f"[knowledge queue verification revoked: "
                                f"concept={concept!r}, "
                                f"entries={revoked_count}, "
                                f"truth_state={state_name}]"
                            )
            print()
            continue

        if command.startswith("/truth "):
            concept = user_text[len("/truth "):].strip()
            if not concept:
                print("[usage: /truth CONCEPT]")
            else:
                record = effective_truth_record(
                    truth_store_path,
                    concept,
                )
                explicit = (
                    record.source != "truth-default"
                )
                print(
                    f"[truth concept={record.concept!r}, "
                    f"state={record.state}, explicit={explicit}, "
                    f"source={record.source!r}, "
                    f"updated_at={record.updated_at!r}, "
                    f"reason={record.reason!r}, "
                    f"correction={record.correction!r}]"
                )
            print()
            continue

        if command.startswith("/provenance "):
            query = user_text[len("/provenance "):].strip()
            if not query:
                print("[usage: /provenance QUERY]")
            else:
                result = semantic_knowledge.resolve(query)
                state = result.knowledge_state
                provenance = state.provenance
                if provenance is None:
                    print("[provenance: none]")
                else:
                    print(
                        f"[provenance state={state.state}, "
                        f"focus={state.focus!r}, "
                        f"source={provenance.source!r}, "
                        f"origin={provenance.origin!r}, "
                        f"priority={provenance.retrieval_priority}, "
                        f"timestamp={provenance.timestamp!r}, "
                        f"fingerprint={provenance.fingerprint!r}, "
                        f"evidence={provenance.evidence!r}]"
                    )
                    if provenance.metadata:
                        print(
                            "[provenance metadata: "
                            + ", ".join(
                                f"{key}={value}"
                                for key, value in provenance.metadata.items()
                            )
                            + "]"
                        )
            print()
            continue

        if command.startswith("/dispatch "):
            query = user_text[len("/dispatch "):].strip()
            if not query:
                print("[usage: /dispatch QUERY]")
            else:
                result = semantic_knowledge.resolve(query)
                dispatch = result.dispatch
                truth_record = result.truth
                truth_result = result.truth_result
                provenance_text = (
                    dispatch.provenance.compact()
                    if dispatch.provenance is not None
                    else "none"
                )
                truth_text = (
                    truth_record.state
                    if truth_record is not None
                    else "-"
                )
                warning_text = (
                    truth_result.warning
                    if truth_result is not None
                    else ""
                )
                runtime_text = (
                    truth_result.runtime_status
                    if truth_result is not None
                    else "-"
                )
                print(
                    f"[dispatch action={dispatch.action}, "
                    f"state={dispatch.state}, "
                    f"focus={dispatch.focus!r}, "
                    f"predicate_type={dispatch.predicate_type!r}, "
                    f"terminal={dispatch.is_terminal}, "
                    f"route={dispatch.route}, "
                    f"reason={dispatch.reason}, "
                    f"truth_state={truth_text}, "
                    f"truth_runtime={runtime_text}, "
                    f"truth_warning={warning_text!r}, "
                    f"bare_routed={result.bare_concept_routed}, "
                    f"bare_unknown_blocked={result.bare_unknown_blocked}, "
                    f"bare_focus={result.bare_focus!r}, "
                    f"routed_query={result.routed_query!r}, "
                    f"provenance={provenance_text}]"
                )
                if dispatch.answer:
                    print(f"[dispatch answer: {dispatch.answer}]")
            print()
            continue

        if command.startswith("/kstate "):
            query = user_text[len("/kstate "):].strip()
            if not query:
                print("[usage: /kstate QUERY]")
            else:
                result = semantic_knowledge.resolve(query)
                state = result.knowledge_state
                print(
                    f"[knowledge-state={state.state}, "
                    f"focus={state.focus!r}, "
                    f"predicate_type={state.predicate_type!r}, "
                    f"retrieval={state.is_retrieval}, "
                    f"model_generation={state.permits_model_generation}, "
                    f"bare_routed={result.bare_concept_routed}, "
                    f"bare_unknown_blocked={result.bare_unknown_blocked}, "
                    f"bare_focus={result.bare_focus!r}, "
                    f"routed_query={result.routed_query!r}, "
                    f"reason={state.reason}]"
                )
                if state.answer:
                    print(f"[resolved answer: {state.answer}]")
            print()
            continue

        if command == "/internalized":
            concepts = load_internalized_concepts(
                learning_log,
                learning_state,
            )
            if not concepts:
                print("[internalized concepts: empty]")
            else:
                print(
                    f"[internalized concepts: {len(concepts)} concept(s)]"
                )
                checkpoint_bound = (
                    semantic_config.checkpoint_fingerprints
                    or frozenset()
                )
                for index, concept in enumerate(concepts, 1):
                    source_text = ",".join(concept.sources)
                    bound = any(
                        fp in checkpoint_bound
                        for fp in concept.fingerprints
                    )
                    print(
                        f"  {index:02d}. concept={concept.concept!r} "
                        f"trained_pairs={concept.trained_pairs} "
                        f"binding={'CURRENT' if bound else 'STALE'} "
                        f"sources={source_text} "
                        f"latest_question={concept.latest_question!r}"
                    )
            print()
            continue

        if command == "/typedsubjects":
            grouped = typed_index_dict(typed_subject_index_path)
            if not grouped:
                print("[typed subject index: empty]")
            else:
                print(f"[typed subject index: {len(grouped)} subject(s)]")
                for subject, by_type in grouped.items():
                    print(f"  {subject}:")
                    for predicate_type, statements in by_type.items():
                        for statement in statements:
                            print(
                                f"    {subject} => {predicate_type} => "
                                f"{statement}"
                            )
            print()
            continue

        if command.startswith("/typedsubject "):
            subject = user_text[len("/typedsubject "):].strip()
            mappings = typed_subject_mapping(
                typed_subject_index_path,
                subject,
            )
            if not mappings:
                print(
                    f"[no typed subject propositions for {subject!r}]"
                )
            else:
                for mapping in mappings:
                    print(mapping)
            print()
            continue

        if command == "/subjects":
            grouped = subject_index_dict(subject_index_path)
            if not grouped:
                print("[subject index: empty]")
            else:
                print(f"[subject index: {len(grouped)} subject(s)]")
                for subject, statements in grouped.items():
                    print(f"  {subject}:")
                    for statement in statements:
                        print(f"    {subject} => {statement}")
            print()
            continue

        if command.startswith("/subject "):
            subject = user_text[len("/subject "):].strip()
            mappings = subject_mapping(subject_index_path, subject)
            if not mappings:
                print(f"[no subject-keyed propositions for {subject!r}]")
            else:
                for mapping in mappings:
                    print(mapping)
                composed = compose_subject_from_index(
                    subject_index_path,
                    subject,
                )
                if composed:
                    print(f"[composed: {composed}]")
            print()
            continue

        if command.startswith("/prop "):
            subject = user_text[len("/prop "):].strip()
            answer = compose_semantic_proposition_subject(
                proposition_path,
                subject,
            )
            if answer:
                print(f"AI> {answer}")
            else:
                print(f"[no semantic propositions for {subject!r}]")
            print()
            continue

        if command.startswith("/teachq "):
            payload = user_text[len("/teachq "):].strip()
            if "=>" not in payload:
                print("[usage: /teachq QUESTION => ANSWER]")
                print()
                continue

            question, corrected = [
                part.strip() for part in payload.split("=>", 1)
            ]
            if not question or not corrected:
                print("[usage: /teachq QUESTION => ANSWER]")
                print()
                continue

            input_ok, input_reason = input_quality_check(question)
            if not input_ok:
                print(f"[teaching rejected: invalid question: {input_reason}]")
                print()
                continue

            teaching_ok, teaching_reason = validate_teaching_answer(
                question,
                corrected,
            )
            if not teaching_ok:
                print(f"[teaching rejected: {teaching_reason}]")
                print(f"[hint: {teaching_hint(question)}]")
                print()
                continue

            reactivated = mark_pair_for_retraining(
                learning_state,
                question,
                corrected,
            )
            append_learning_pair(
                learning_log,
                question,
                corrected,
                source="chat-manual",
            )
            if reactivated:
                print("[previously trained pair reactivated for retraining]")
            print(
                f"[explicit manual learning pair saved; "
                f"question={question}, "
                f"pairs={learning_log_count(learning_log)}]"
            )
            print()
            continue

        if command.startswith("/teach "):
            corrected = user_text[len("/teach "):].strip()
            if not corrected:
                print("[usage: /teach corrected answer]")
            elif last_user_text is None:
                print("[no previous user turn to teach]")
            else:
                teaching_ok, teaching_reason = validate_teaching_answer(
                    last_user_text,
                    corrected,
                )
                if not teaching_ok:
                    print(f"[teaching rejected: {teaching_reason}]")
                    print(f"[hint: {teaching_hint(last_user_text)}]")
                else:
                    reactivated = mark_pair_for_retraining(
                        learning_state,
                        last_user_text,
                        corrected,
                    )
                    append_learning_pair(
                        learning_log,
                        last_user_text,
                        corrected,
                        source="chat-manual",
                    )
                    if reactivated:
                        print(
                            "[previously trained pair reactivated for retraining]"
                        )
                    print(
                        f"[manual learning pair saved; "
                        f"pairs={learning_log_count(learning_log)}]"
                    )
            print()
            continue

        if command == "/good":
            if last_user_text is None or last_ai_reply is None:
                print("[no previous AI answer to approve]")
            else:
                append_learning_pair(
                    learning_log,
                    last_user_text,
                    last_ai_reply,
                    source="chat-approved",
                )
                print(
                    f"[approved learning pair saved; "
                    f"pairs={learning_log_count(learning_log)}]"
                )
            print()
            continue

        if command in ("/maintain", "/maintain all"):
            target_question = (
                None if command == "/maintain all"
                else last_user_text
            )
            if command == "/maintain" and target_question is None:
                print("[no previous user turn to maintain]")
                print()
                continue

            matched, reactivated, rejected_old, selections = recover_forgotten_pairs_from_queue(
                Path(args.teaching_queue),
                learning_log,
                learning_state,
                target_question=target_question,
            )
            print(
                f"[maintenance matched={matched}, "
                f"reactivated={reactivated}, "
                f"rejected_old_teachers={rejected_old}]"
            )
            for queued_question, teacher_answer, detail in selections:
                if teacher_answer:
                    print(
                        f"[recovery selected: {queued_question} -> "
                        f"{teacher_answer} ({detail})]"
                    )
                else:
                    print(
                        f"[recovery selected: {queued_question} -> NONE "
                        f"({detail})]"
                    )
                    print("[recovery status=NEEDS_TEACHING]")
                    print(f"[hint: {teaching_hint(queued_question)}]")

            if reactivated:
                print("[run /train to relearn reactivated trusted pairs]")
            elif matched:
                print("[matched trusted pairs are already pending or current]")
            elif selections:
                print("[no valid trusted teacher; use /teach before /train]")
            else:
                print("[no pending teaching candidate for maintenance]")
            print()
            continue

        if command == "/sleep status":
            sleep_status = semantic_sleep_status(
                nagato_semantic_memory_path,
                learning_state,
                checkpoint_trained_fingerprints(checkpoint),
            )
            print(
                f"[semantic sleep: "
                f"memory={sleep_status.memory_subjects}, "
                f"internalized={sleep_status.internalized}, "
                f"pending={sleep_status.pending}]"
            )
            print()
            continue

        if command == "/sleep":
            # v0.7.22: PENDING candidates are trained ONLY on the isolated
            # Experimental Adapter; never append them to Trusted learning_log.
            try:
                from experimental_sleep_v0722 import experimental_sleep
                experimental_sleep_result = experimental_sleep(
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    PROJECT_ROOT / "model" / "model-gpu-v1.6.2-online.pt",
                    PROJECT_ROOT / "model" / "tokenizer-v0.7-bpe.json",
                    PROJECT_ROOT / "results" / "experimental_sleep_v0722",
                )
                print("[experimental sleep: status={}, pending={}, checkpoint={}, auto_promote=False]".format(
                    experimental_sleep_result["status"],experimental_sleep_result["pending"],
                    experimental_sleep_result.get("checkpoint","-")))
            except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
                print("[experimental sleep FAILED: {}: {}]".format(type(exc).__name__,exc))
                print("[Trusted sleep skipped to avoid partial dual sleep execution]")
                print()
                continue
            if memory_first_enabled and memory_first_mode == "constrained":
                from experimental_reload_v0723 import reload_after_sleep
                memory_first_generator, reload_info = reload_after_sleep(
                    experimental_sleep_result,
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    PROJECT_ROOT / "model" / "model-gpu-v1.6.2-online.pt",
                    PROJECT_ROOT / "model" / "tokenizer-v0.7-bpe.json",
                    memory_first_generator)
                print("[experimental adapter reload: status={}, reason={}, checkpoint={}]".format(
                    reload_info["status"],reload_info.get("reason","-"),
                    reload_info.get("checkpoint","-")))
            # v0.7.40: independently sync operationally Approved records.
            # This does not assert factual truth or mutate Trusted weights.
            from approved_semantic_sleep_v0740 import synchronize, queue_approved
            approved_sync=synchronize(
                PROJECT_ROOT / "data" / "approved_v071.jsonl",
                PROJECT_ROOT / "data" / "approved_semantic_memory_v0740.jsonl")
            approved_queue=queue_approved(
                PROJECT_ROOT / "data" / "approved_semantic_memory_v0740.jsonl",
                learning_log, learning_state)
            print("[approved semantic sync: approved={}, synced={}, added={}, queued={}, repaired={}, outstanding={}]".format(
                approved_sync["approved"],approved_sync["synced"],approved_sync["added"],
                approved_queue["queued"],approved_queue["repaired"],approved_queue["outstanding"]))
            queued, before_sleep = prepare_semantic_sleep_pairs(
                nagato_semantic_memory_path,
                learning_log,
                learning_state,
                checkpoint_trained_fingerprints(checkpoint),
            )
            conditional_queued = prepare_conditional_sleep_pairs(
                conditional_proposition_path,
                learning_log,
                learning_state,
            )
            print(
                f"[semantic sleep prepared: "
                f"memory={before_sleep.memory_subjects}, "
                f"internalized={before_sleep.internalized}, "
                f"pending={before_sleep.pending}, "
                f"newly_queued={queued}, "
                f"conditional_queued={conditional_queued}]"
            )
            if before_sleep.pending == 0 and conditional_queued == 0 and approved_queue["outstanding"] == 0:
                print("[semantic sleep: all semantic memory is already internalized]")
                print()
                continue

            new_model_path = run_online_training(args, model_path)
            if new_model_path is not None:
                model, checkpoint = LanguageModel.load_checkpoint(
                    str(new_model_path),
                    device=device,
                )
                model_path = new_model_path
                print(f"[semantic sleep checkpoint reloaded: {model_path}]")
                semantic_config = replace(
                    semantic_config,
                    checkpoint_fingerprints=(
                        checkpoint_trained_fingerprints(checkpoint)
                    ),
                )
                semantic_knowledge = SemanticKnowledgeArchitecture(
                    semantic_config
                )
                load_concept_calibration(calibration_path, device)
                history.clear()
                last_user_text = None
                last_ai_reply = None

                after_sleep = semantic_sleep_status(
                    nagato_semantic_memory_path,
                    learning_state,
                    checkpoint_trained_fingerprints(checkpoint),
                )
                print(
                    f"[semantic sleep completed: "
                    f"memory={after_sleep.memory_subjects}, "
                    f"internalized={after_sleep.internalized}, "
                    f"pending={after_sleep.pending}]"
                )
                print("[conversation history cleared after semantic sleep]")
            print()
            continue

        if command == "/trainbatch":
            verification_path = Path(
                args.internalized_verification
            )
            plan = batch_repair_plan(verification_path)
            if plan.count == 0:
                print("[verification batch: no active repair tasks]")
                print()
                continue

            protected_records = protected_internalized_records(
                learning_log,
                set(checkpoint_trained_fingerprints(checkpoint)),
                set(plan.fingerprints),
                set(plan.concepts),
            )
            print(
                f"[batch preservation baseline: "
                f"protected={len(protected_records)}, "
                f"repair_targets={plan.count}]"
            )

            reactivated_count = 0
            already_pending_count = 0
            for row in plan.tasks:
                question = str(row.get("question", "")).strip()
                teacher = str(
                    row.get("teacher_answer", "")
                ).strip()
                if mark_pair_for_retraining(
                    learning_state,
                    question,
                    teacher,
                ):
                    reactivated_count += 1
                else:
                    already_pending_count += 1

            mark_batch_retrain(
                verification_path,
                set(plan.fingerprints),
            )
            print(
                f"[verification batch prepared: "
                f"tasks={plan.count}, "
                f"reactivated={reactivated_count}, "
                f"already_pending={already_pending_count}, "
                f"concepts={'|'.join(plan.concepts)}]"
            )

            production_checkpoint = Path(args.online_output)
            production_state = Path(args.learning_state)
            (
                candidate_checkpoint,
                candidate_state,
            ) = batch_candidate_paths(
                production_checkpoint,
                production_state,
            )
            discard_batch_candidate(
                candidate_checkpoint,
                candidate_state,
            )

            if not production_state.exists():
                print(
                    f"[batch candidate aborted: learning state not found: "
                    f"{production_state}]"
                )
                print()
                continue

            candidate_state.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                production_state,
                candidate_state,
            )
            print(
                f"[batch candidate prepared: checkpoint={candidate_checkpoint}, "
                f"state={candidate_state}]"
            )
            print(
                f"[production checkpoint protected: {model_path}]"
            )

            new_candidate_path = run_online_training(
                args,
                model_path,
                output_path=candidate_checkpoint,
                state_path=candidate_state,
            )
            if new_candidate_path is None:
                discard_batch_candidate(
                    candidate_checkpoint,
                    candidate_state,
                )
                print(
                    "[batch candidate discarded: training did not produce "
                    "a usable checkpoint; production unchanged]"
                )
                print()
                continue

            candidate_model, candidate_ckpt = (
                LanguageModel.load_checkpoint(
                    str(new_candidate_path),
                    device=device,
                )
            )
            print(
                f"[loaded batch candidate checkpoint: "
                f"{new_candidate_path}]"
            )
            print(
                f"[candidate binding: "
                f"{len(checkpoint_trained_fingerprints(candidate_ckpt))} "
                "fingerprint(s)]"
            )

            (
                preservation_ok,
                preservation_passed,
                preservation_failed,
            ) = run_batch_preservation_gate(
                model=candidate_model,
                tokenizer=tokenizer,
                protected_records=protected_records,
                args=args,
                batch_fingerprints=plan.fingerprints,
            )

            if args.batch_preservation_force_fail:
                print(
                    "[batch rollback test hook: forcing preservation FAIL "
                    "after candidate evaluation]"
                )
                preservation_ok = False

            (
                repair_quality_ok,
                repair_quality_passed,
                repair_quality_failed,
            ) = run_candidate_repair_quality_gate(
                model=candidate_model,
                tokenizer=tokenizer,
                plan=plan,
                args=args,
            )

            if args.candidate_repair_force_fail:
                print(
                    "[candidate repair-quality test hook: forcing FAIL "
                    "after target evaluation]"
                )
                repair_quality_ok = False

            if not preservation_ok or not repair_quality_ok:
                discard_batch_candidate(
                    candidate_checkpoint,
                    candidate_state,
                )
                rollback_reason = (
                    "preservation=FAIL"
                    if not preservation_ok
                    else "repair_quality=FAIL"
                )
                if not preservation_ok and not repair_quality_ok:
                    rollback_reason = (
                        "preservation=FAIL; repair_quality=FAIL"
                    )
                print(
                    f"[batch rollback: {rollback_reason}; "
                    "candidate checkpoint/state discarded]"
                )
                print(
                    f"[production checkpoint retained: {model_path}]"
                )
                print(
                    "[verification tasks remain retrain; "
                    "adjust training/replay before retry]"
                )
                history.clear()
                last_user_text = None
                last_ai_reply = None
                print(
                    "[conversation history cleared after batch rollback]"
                )
                print()
                continue

            promote_batch_candidate(
                candidate_checkpoint,
                candidate_state,
                production_checkpoint,
                production_state,
            )
            model, checkpoint = LanguageModel.load_checkpoint(
                str(production_checkpoint),
                device=device,
            )
            model_path = production_checkpoint
            print(
                f"[batch candidate promoted: "
                f"{production_checkpoint}]"
            )
            print(
                f"[batch state promoted: {production_state}]"
            )

            semantic_config = replace(
                semantic_config,
                checkpoint_fingerprints=(
                    checkpoint_trained_fingerprints(
                        checkpoint
                    )
                ),
            )
            semantic_knowledge = (
                SemanticKnowledgeArchitecture(
                    semantic_config
                )
            )
            print(
                f"[checkpoint binding refreshed: "
                f"{len(semantic_config.checkpoint_fingerprints or ())} "
                "fingerprint(s)]"
            )
            print(
                f"[verification batch trained: "
                f"{plan.count} task(s); "
                "preservation=PASS; repair_quality=PASS; "
                "candidate=PROMOTED; "
                "re-query each concept to resolve verification]"
            )
            for concept in plan.concepts:
                print(f"  -> {concept}")
            load_concept_calibration(
                calibration_path,
                device,
            )
            history.clear()
            last_user_text = None
            last_ai_reply = None
            print(
                "[conversation history cleared after "
                "batch promotion]"
            )
            print()
            continue

        if command == "/train":
            new_model_path = run_online_training(args, model_path)
            if new_model_path is not None:
                model, checkpoint = LanguageModel.load_checkpoint(
                    str(new_model_path),
                    device=device,
                )
                model_path = new_model_path
                print(f"[reloaded trained checkpoint: {model_path}]")
                semantic_config = replace(
                    semantic_config,
                    checkpoint_fingerprints=(
                        checkpoint_trained_fingerprints(checkpoint)
                    ),
                )
                semantic_knowledge = SemanticKnowledgeArchitecture(
                    semantic_config
                )
                print(
                    f"[checkpoint binding refreshed: "
                    f"{len(semantic_config.checkpoint_fingerprints or ())} "
                    "fingerprint(s)]"
                )
                load_concept_calibration(calibration_path, device)
                history.clear()
                last_user_text = None
                last_ai_reply = None
                print("[conversation history cleared after training]")
            print()
            continue

        # Context routing occurs AFTER slash command handling but BEFORE
        # retrieval and Truth Gate. No topic result is treated as a fact.
        if topic_adapter is not None:
            topic_route = topic_adapter.process_user_turn(raw_user_text)
            if topic_route.action in ("CLARIFY", "NO_TOPIC"):
                print(f"AI> {topic_route.response}")
                print("[0 generated probe tokens, topic resolution]")
                print()
                last_ai_reply = None
                continue
            if topic_route.action == "READY" and topic_route.rewritten_query:
                if topic_route.rewritten_query != raw_user_text:
                    print(f"[topic route: {topic_route.topic or '-'}]")
                    user_text = topic_route.rewritten_query
        last_user_text = user_text
        internalized_record = None

        # v10.16.4 Auto-detect declarative conditional knowledge from
        # the RAW input, not from the normalized query surface. This prevents
        # questions such as "CPUが高温のときは?" from becoming
        # predicate="どうなる" candidates after normalization.
        raw_conditional_query = parse_conditional_query(raw_user_text)
        conditional_statement = (
            None
            if raw_conditional_query.matched
            else parse_conditional_statement(raw_user_text)
        )
        if conditional_statement is not None:
            queued_candidate, row = queue_conditional_candidate(
                conditional_candidate_path,
                raw_user_text,
                proposition_path=conditional_proposition_path,
            )
            if queued_candidate:
                print(
                    f"[conditional candidate queued: "
                    f"subject={row.subject!r}, "
                    f"condition={row.condition!r}, "
                    f"predicate={row.predicate!r}]"
                )
                print("[review with /condcandidates, approve with /condapprove N or /condapprove all]")
                print("[0 generated probe tokens, candidate capture]")
                print()
                last_ai_reply = None
                continue

            # Existing approved facts are not re-queued; allow normal runtime
            # processing to continue rather than swallowing the input.
            stored_match = any(
                stored.subject == conditional_statement.subject
                and stored.condition == conditional_statement.condition
                and stored.predicate == conditional_statement.predicate
                and stored.condition_polarity
                    == conditional_statement.condition_polarity
                for stored in load_conditional_propositions(
                    conditional_proposition_path
                )
            )
            if stored_match:
                print(
                    f"[conditional candidate skipped: already stored, "
                    f"subject={conditional_statement.subject!r}, "
                    f"condition={conditional_statement.condition!r}, "
                    f"predicate={conditional_statement.predicate!r}]"
                )
            else:
                print(
                    f"[conditional candidate already pending: "
                    f"subject={conditional_statement.subject!r}, "
                    f"condition={conditional_statement.condition!r}]"
                )
                print("[0 generated probe tokens, candidate capture]")
                print()
                last_ai_reply = None
                continue

        input_ok, input_reason = input_quality_check(user_text)
        if not input_ok:
            print(f"AI> {UNKNOWN_REPLY}")
            if args.show_risk and args.unknown_rejection:
                print(
                    f"[gate=UNKNOWN, confidence=0.000, "
                    f"min_tok_conf=0.000, mean_margin=0.000, "
                    f"agreement=0.000, sem_agreement=0.000, "
                    f"intent=input_quality, slots=-, slot_cov=0.00, "
                    f"qa_sim=0.000, prev_sim=-1.000, "
                    f"agr_th={args.min_agreement:.2f}, "
                    f"context_turns=0, resolution=INPUT_REJECT, "
                    f"action=ask/rephrase, reason={input_reason}]"
                )
            print("[route=request rephrase]")
            print("[0 generated probe tokens, 0.00s, 0.0 tok/s]")
            print()
            last_ai_reply = None
            continue

        # v0.2.33.82.5: grounded multi-topic follow-up only.
        # Follow-ups must not enter unconstrained generation. Truth State is
        # evaluated using the original source topic, never the rewritten text.
        if (topic_adapter is not None and topic_route.action == "READY"
                and topic_route.topic
                and raw_user_text.strip().rstrip("。！？!? ") in
                ("もう少し詳しく", "詳しく教えて", "もっと詳しく", "続き", "それについて")):
            followup_subject = topic_route.topic
            followup_memory_path = resolve_runtime_path(args.corpus_memory)
            followup_hit = retrieval_first_resolve_subject(
                followup_memory_path, followup_subject
            )
            followup_truth = effective_truth_record(
                truth_store_path, followup_subject
            )
            if (followup_hit.hit and truth_allows_direct_retrieval(
                    followup_truth.state)):
                if followup_truth.state == "UNVERIFIED":
                    print(f"[truth warning: state=UNVERIFIED, concept={followup_subject!r}]")
                proposition, seen_count, total_count = proposition_cursor.next(
                    followup_subject, followup_hit.answer
                )
                # Skip explicitly blocked individual propositions, but never
                # override the subject-level Truth Gate.
                while proposition is not None:
                    decision = proposition_truth.decide(
                        followup_subject, proposition, followup_hit.provenance,
                        followup_truth.state, True
                    )
                    if decision.allowed:
                        break
                    print(f"[proposition truth=BLOCK, id={decision.proposition_id}, state={decision.state}]")
                    proposition, seen_count, total_count = proposition_cursor.next(
                        followup_subject, followup_hit.answer
                    )
                if proposition is None:
                    print("AI> この話題について、未提示の記録はありません。")
                    print(f"[grounded-expansion=EXHAUSTED, topic={followup_subject!r}]")
                    print()
                    last_ai_reply = None
                    continue
                warning_prefix = "【未検証の記録】" if decision.state == "UNVERIFIED" else ""
                print(f"[proposition-id={decision.proposition_id}, truth_state={decision.state}, provenance={decision.source}]")
                print(f"AI> {warning_prefix}{proposition}")
                print(f"[grounded-expansion=NEXT, seen={seen_count}, total={total_count}]")
                print(f"[grounded-followup=HIT, topic={followup_subject!r}, "
                      f"truth_state={followup_truth.state}, "
                      f"provenance={followup_hit.provenance}]")
                print("[0 generated probe tokens, grounded follow-up retrieval]")
                history.append((user_text, proposition))
                last_ai_reply = proposition
            else:
                print("AI> この話題について、検証可能な追加情報がありません。")
                print(f"[grounded-followup=BLOCK, topic={followup_subject!r}, "
                      f"truth_state={followup_truth.state}, "
                      f"memory_hit={followup_hit.hit}]")
                print("[0 generated probe tokens, grounded follow-up fallback]")
                last_ai_reply = None
            print()
            continue

        # v10.16.1 Conditional Semantic Retrieval.
        conditional_query, conditional_answer = answer_conditional_query(
            conditional_proposition_path,
            user_text,
        )
        if conditional_query.matched:
            if conditional_answer:
                print(f"AI> {conditional_answer}")
                print(
                    f"[conditional-retrieval=HIT, "
                    f"subject={conditional_query.subject!r}, "
                    f"condition={conditional_query.condition!r}, "
                    f"route=conditional-semantic-v10.16.1]"
                )
                print("[0 generated probe tokens, conditional semantic retrieval]")
                print()
                history.append((user_text, conditional_answer))
                last_ai_reply = conditional_answer
                continue
            else:
                print(
                    f"[conditional-retrieval=MISS, "
                    f"subject={conditional_query.subject!r}, "
                    f"condition={conditional_query.condition!r}]"
                )

        # v10.12.16.1 Retrieval-First Runtime.
        # Exact Subject-Keyed Corpus Memory lookup precedes UNKNOWN/generation
        # for explicit or bare concept queries. Explicit FALSE/OUTDATED/
        # CONTESTED truth states bypass direct corpus retrieval and continue
        # through the existing Truth-Aware Semantic Architecture.
        retrieval_focus = extract_concept_query_focus(user_text)
        if not retrieval_focus:
            retrieval_focus = extract_bare_concept_focus(user_text)

        if retrieval_focus:
            corpus_memory_path = resolve_runtime_path(args.corpus_memory)
            synonym_terms = synonym_lexicon.expand(retrieval_focus)
            retrieval = retrieval_first_resolve_subject(
                corpus_memory_path,
                retrieval_focus,
            )
            for alias in synonym_terms[1:]:
                if retrieval.hit:
                    break
                candidate = retrieval_first_resolve_subject(corpus_memory_path, alias)
                # Never bypass explicit truth blocks on either requested or matched term.
                if (candidate.hit and
                        truth_allows_direct_retrieval(effective_truth_record(truth_store_path, retrieval_focus).state) and
                        truth_allows_direct_retrieval(effective_truth_record(truth_store_path, alias).state)):
                    retrieval = candidate
                    print("[synonym_subject_match, input={}, matched={}]".format(retrieval_focus, alias))
                    print("[retrieval_trace=" + trace_match(retrieval_focus, alias, "CORPUS_SUBJECT", str(corpus_memory_path), "LOCAL_RETRIEVAL").as_json() + "]")
            if retrieval.hit:
                retrieval_truth = effective_truth_record(
                    truth_store_path,
                    retrieval_focus,
                )
                direct_retrieval_allowed = truth_allows_direct_retrieval(
                    retrieval_truth.state
                )
                if direct_retrieval_allowed:
                    if topic_adapter is not None and topic_route.topic == retrieval_focus:
                        shown, shown_count, total_count = proposition_cursor.next(
                            retrieval_focus, retrieval.answer
                        )
                        # Restrict each fragment with the read-only overlay.
                        while shown is not None:
                            decision = proposition_truth.decide(
                                retrieval_focus, shown, retrieval.provenance,
                                retrieval_truth.state, True
                            )
                            if decision.allowed:
                                break
                            print(f"[proposition truth=BLOCK, id={decision.proposition_id}, state={decision.state}]")
                            shown, shown_count, total_count = proposition_cursor.next(
                                retrieval_focus, retrieval.answer
                            )
                        if shown is None:
                            print("AI> この話題について提示できる記録はありません。")
                            print("[grounded-expansion=BLOCKED]")
                            print()
                            last_ai_reply = None
                            continue
                        print(f"[proposition-id={decision.proposition_id}, truth_state={decision.state}, provenance={decision.source}]")
                        display_answer = (
                            "【未検証の記録】" + shown
                            if decision.state == "UNVERIFIED" else shown
                        )
                        if retrieval_truth.state == "UNVERIFIED" and retrieval.route == "CORPUS_MEMORY":
                            from evidence_reference_v0738 import count_evidence
                            evidence_count=count_evidence(
                                PROJECT_ROOT / "data" / "approved_v071.jsonl",
                                PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                                retrieval_focus, retrieval.answer,
                                retrieval.provenance,
                                threshold=int(os.environ.get("LLM_CHA_AUTO_APPROVE_REFERENCES","10")),
                                route="CORPUS_MEMORY")
                            print("[evidence_reference: status={}, count={}, promoted={}]".format(
                                evidence_count["status"],evidence_count.get("reference_count"),
                                evidence_count["promoted"]))
                            from approved_evidence_state_v0739 import evidence_state
                            approval=evidence_state(
                                PROJECT_ROOT / "data" / "approved_v071.jsonl",
                                PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                                retrieval_focus, retrieval.answer, retrieval.provenance,
                                "CORPUS_MEMORY")
                            print("[evidence_approval: state={}, count={}, factual_truth={}]".format(
                                approval["approval_state"],approval.get("reference_count","-"),approval["truth_state"]))

                            from raw_wiki_parallel_v0735 import parallel_evidence
                            corpus_wiki=parallel_evidence(display_answer,retrieval_focus,cha_wikipedia_lookup)
                            display_answer=corpus_wiki["answer"]
                            print("[raw_wiki_parallel={}, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]".format(corpus_wiki["wiki_status"]))
                        print(f"AI> {display_answer}")
                        print(f"[grounded-expansion=INITIAL, shown={shown_count}, total={total_count}]")
                    else:
                        shown = retrieval.answer
                        if retrieval_truth.state == "UNVERIFIED" and retrieval.route == "CORPUS_MEMORY":
                            from evidence_reference_v0738 import count_evidence
                            evidence_count=count_evidence(
                                PROJECT_ROOT / "data" / "approved_v071.jsonl",
                                PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                                retrieval_focus, retrieval.answer,
                                retrieval.provenance,
                                threshold=int(os.environ.get("LLM_CHA_AUTO_APPROVE_REFERENCES","10")),
                                route="CORPUS_MEMORY")
                            print("[evidence_reference: status={}, count={}, promoted={}]".format(
                                evidence_count["status"],evidence_count.get("reference_count"),
                                evidence_count["promoted"]))
                            from approved_evidence_state_v0739 import evidence_state
                            approval=evidence_state(
                                PROJECT_ROOT / "data" / "approved_v071.jsonl",
                                PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                                retrieval_focus, retrieval.answer, retrieval.provenance,
                                "CORPUS_MEMORY")
                            print("[evidence_approval: state={}, count={}, factual_truth={}]".format(
                                approval["approval_state"],approval.get("reference_count","-"),approval["truth_state"]))

                            from raw_wiki_parallel_v0735 import parallel_evidence
                            corpus_wiki=parallel_evidence(shown,retrieval_focus,cha_wikipedia_lookup)
                            shown=corpus_wiki["answer"]
                            print("[raw_wiki_parallel={}, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]".format(corpus_wiki["wiki_status"]))
                        print(f"AI> {shown}")
                    function_part = ""
                    if retrieval.function_structure is not None:
                        fs = retrieval.function_structure
                        function_part = (
                            f", action={fs.action}, target={fs.target}, "
                            f"purpose={fs.purpose}"
                        )
                    print(
                        f"[retrieval-first=HIT, concept={retrieval.subject!r}, "
                        f"relation={retrieval.relation or '-'}, "
                        f"route={retrieval.route}, provenance={retrieval.provenance}, "
                        f"truth_state={retrieval_truth.state}{function_part}]"
                    )
                    print("[0 generated probe tokens, corpus-memory retrieval]")
                    print()
                    if (os.environ.get("LLM_CHA_CORPUS_FOLLOWUP", "0") == "1"
                            and retrieval.route == "CORPUS_MEMORY"
                            and retrieval_truth.state == "UNVERIFIED"):
                        corpus_followup_context = {
                            "subject": retrieval.subject,
                            "truth_state": retrieval_truth.state,
                        }
                        from corpus_cursor_bridge_v074417 import bridge_records
                        from evidence_cursor_v074416 import EvidenceCursor
                        cursor_preflight = bridge_records(
                            retrieval.records, retrieval.subject, retrieval_truth.state)
                        corpus_evidence_cursor = EvidenceCursor()
                        if cursor_preflight.status == "READY":
                            # Use the actual answer shown, not generated paraphrases.
                            corpus_evidence_cursor.reset(
                                retrieval.subject, list(cursor_preflight.evidence), shown)
                        print("[corpus_cursor=status:{}, records={}, missing_ids={}, remaining={}]".format(
                            cursor_preflight.status, cursor_preflight.count,
                            cursor_preflight.missing_ids, corpus_evidence_cursor.remaining()))
                    history.append((user_text, shown))
                    last_ai_reply = shown
                    continue
                else:
                    print(
                        f"[retrieval-first=HIT-BUT-TRUTH-BYPASS, "
                        f"concept={retrieval.subject!r}, "
                        f"truth_state={retrieval_truth.state}]"
                    )

        # v0.6.16: dialogue/persona intent precedes lexical raw corpus retrieval.
        from raw_evidence_priority_v0616 import conversational_intercept, allow_raw_evidence
        if (os.environ.get("LLM_CHA_FOLLOWUP_RELEVANCE", "0") == "1"
                and last_explicit_knowledge_topic
                and raw_user_text.strip().rstrip("。！？? ") in (
                    "もっと詳しく", "もう少し詳しく", "詳しく", "詳しく教えて",
                    "もっと詳しく教えて", "もう少し詳しく教えて")):
            # Only reached when established evidence routes did not answer.
            # Never let identity/model generation masquerade as topic details.
            print("AI> " + followup_exhaustion.respond(last_explicit_knowledge_topic))
            print("[route=FOLLOWUP_RELEVANCE_NO_EVIDENCE, topic={}, train_ready=False, auto_promote=False]".format(
                last_explicit_knowledge_topic))
            print()
            last_ai_reply = None
            continue
        identity_result = identity_context.respond(user_text)
        if identity_result is not None:
            immediate_reply, identity_route = identity_result
            print("AI> " + immediate_reply)
            print("[route={}, train_ready=False]".format(identity_route))
            print()
            last_ai_reply = immediate_reply
            continue

        # v0.6.15: subject miss -> search raw evidence without assuming subjecthood.
        # Truth-blocked indexed records are NOT bypassed via raw corpus fallback.
        if retrieval_focus and not retrieval.hit and allow_raw_evidence(user_text, retrieval_focus):
            from raw_concept_evidence_v0615 import find_mentions, present_mentions
            raw_path = resolve_runtime_path(DEFAULT_RAW_KNOWLEDGE_CORPUS)
            raw_hits = best_raw_mentions(raw_path, synonym_lexicon.expand(retrieval_focus))
            if raw_hits:
                raw_answer = present_mentions(raw_hits)
                from evidence_reference_v0738 import count_evidence
                evidence_count=count_evidence(
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    retrieval_focus, raw_answer, str(raw_path),
                    threshold=int(os.environ.get("LLM_CHA_AUTO_APPROVE_REFERENCES","10")),
                    route="RAW_CONCEPT_EVIDENCE")
                print("[evidence_reference: status={}, count={}, promoted={}]".format(
                    evidence_count["status"],evidence_count.get("reference_count"),
                    evidence_count["promoted"]))
                from approved_evidence_state_v0739 import evidence_state
                approval=evidence_state(
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    retrieval_focus, raw_answer, str(raw_path),
                    "RAW_CONCEPT_EVIDENCE")
                print("[evidence_approval: state={}, count={}, factual_truth={}]".format(
                    approval["approval_state"],approval.get("reference_count","-"),approval["truth_state"]))
                from raw_wiki_parallel_v0735 import parallel_evidence
                raw_wiki = parallel_evidence(raw_answer, retrieval_focus, cha_wikipedia_lookup)
                raw_answer = raw_wiki["answer"]
                print("AI> " + raw_answer)
                print("[raw_wiki_parallel={}, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]".format(raw_wiki["wiki_status"]))
                print("[route=RAW_CONCEPT_EVIDENCE, concept={}, hits={}, source={}, truth_state=UNVERIFIED, train_ready=False, auto_promote=False]".format(
                    repr(retrieval_focus), len(raw_hits), str(raw_path)))
                print()
                history.append((user_text, raw_answer))
                last_ai_reply = raw_answer
                continue

        # v0.6.18: for named-topic dialogue, seek external evidence before
        # accepting an unsupported raw model completion as KNOWN.
        from topic_evidence_gate_v0618 import topic_for_external_evidence, source_is_usable
        named_topic = topic_for_external_evidence(user_text)
        if named_topic and (not retrieval_focus or not retrieval.hit):
            named_truth = effective_truth_record(truth_store_path, named_topic)
            if named_truth.state not in ("FALSE", "REJECTED", "BLOCKED", "CONTRADICTED"):
                from wikipedia_relation_evidence_v0621 import resolve_entity
                entity_resolved = resolve_entity(named_topic)
                wiki_lookup_term = entity_resolved.get("title", named_topic) if entity_resolved.get("status") == "FOUND" else named_topic
                if entity_resolved.get("status") == "FOUND" and named_topic != wiki_lookup_term:
                    active_evidence_topic = named_topic
                    active_evidence_extract = entity_resolved.get("extract", "")
                    active_evidence_source = entity_resolved.get("url", "")
                    topic_evidence.remember(active_evidence_topic, active_evidence_extract, active_evidence_source)
                    print("AI> 【Wikipediaの概要・未検証】" + entity_resolved["extract"].split("。")[0] + "。どの点について知りたい？")
                    print("[route=NAMED_TOPIC_WIKIPEDIA_EVIDENCE, term={}, resolved_title={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                        named_topic, wiki_lookup_term, entity_resolved["url"]))
                    print()
                    continue
                wiki_topic = cha_unknown_wiki_fallback(
                    wiki_lookup_term, raw_user_text, cha_wiki_conversation.persona,
                    cha_wikipedia_lookup, cha_persona_wiki_respond,
                    grounded=cha_wiki_grounded_reply, cache=cha_persona_wiki_cache)
                if source_is_usable(wiki_topic):
                    cha_wiki_conversation.offer(wiki_topic["wiki_context"])
                    print("AI> " + wiki_topic["answer"])
                    print("[route=NAMED_TOPIC_WIKIPEDIA_EVIDENCE, term={}, source={}, truth_state=EXTERNAL_UNVERIFIED, verified=False, train_ready=False, auto_promote=False, model_generation=SKIPPED]".format(
                        named_topic, wiki_topic["source"]))
                    print()
                    last_ai_reply = None
                    cha_wiki_last_generated = None
                    continue
                print("[named_topic_evidence={}, term={}]".format(
                    wiki_topic.get("status","UNAVAILABLE"), named_topic))
                print("AI> {}について、確かな回答根拠を取得できなかった。どの点について話したい？".format(named_topic))
                print("[route=NAMED_TOPIC_CLARIFY, train_ready=False, model_generation=SKIPPED]")
                print()
                continue

        semantic_result = semantic_knowledge.resolve(
            user_text
        )
        resolver_query = (
            semantic_result.routed_query
            or user_text
        )
        if semantic_result.bare_concept_routed:
            print(
                f"[semantic bare routing: {user_text!r} -> "
                f"{resolver_query!r}]"
            )
        elif semantic_result.bare_unknown_blocked:
            print(
                f"[bare unknown safety gate: "
                f"concept={semantic_result.bare_focus!r}, "
                "generation=blocked]"
            )
        knowledge_state = semantic_result.knowledge_state
        dispatch = semantic_result.dispatch
        truth_record = semantic_result.truth
        truth_result = semantic_result.truth_result

        if truth_result is not None and truth_result.warning:
            print(
                f"[truth warning: state={truth_record.state}, "
                f"concept={truth_record.concept!r}, "
                f"message={truth_result.warning}]"
            )

        verification_override_record = (
            active_internalized_verification_record(
                Path(args.internalized_verification),
                learning_log,
                learning_state,
                dispatch.focus,
            )
        )
        force_internalized_verification = (
            verification_override_record is not None
        )
        if (
            force_internalized_verification
            and dispatch.action == "RETRIEVE"
        ):
            print(
                "[verification override: "
                f"concept={dispatch.focus!r}, "
                f"semantic_route={dispatch.route}, "
                "verification=model-weights]"
            )

        if (
            dispatch.action == "RETRIEVE"
            and not force_internalized_verification
        ):
            print(f"AI> {dispatch.answer}")
            predicate_part = (
                f", predicate_type={dispatch.predicate_type}"
                if dispatch.predicate_type
                else ""
            )
            provenance_text = (
                dispatch.provenance.compact()
                if dispatch.provenance is not None
                else "none"
            )
            truth_part = (
                f", truth_state={truth_record.state}"
                if truth_record is not None
                else ""
            )
            correction_part = (
                ", truth_correction=True"
                if truth_result is not None
                and truth_result.correction_applied
                else ""
            )
            truth_runtime_part = (
                f", truth_runtime={truth_result.runtime_status}"
                if truth_result is not None
                else ""
            )
            print(
                f"[gate=KNOWN, knowledge_state={dispatch.state}, "
                f"concept={dispatch.focus}{predicate_part}, "
                f"route={dispatch.route}, reason={dispatch.reason}, "
                f"provenance={provenance_text}"
                f"{truth_part}{correction_part}{truth_runtime_part}]"
            )
            print("[0 generated probe tokens, retrieval]")
            print()

            resolved = resolve_teaching_queue(
                Path(args.teaching_queue),
                resolver_query,
            )
            if resolved:
                print(f"[resolved teaching queue entries: {resolved}]")
            history.append((resolver_query, dispatch.answer))
            last_ai_reply = dispatch.answer
            continue

        if dispatch.action == "BLOCK" and not force_internalized_verification:
            truth_block = (
                truth_result is not None
                and truth_result.runtime_status == "BLOCK"
            )
            stale_internalized = (
                dispatch.state == "INTERNALIZED_STALE"
                and not truth_block
            )
            # An ordinary UNKNOWN has no validated local answer. Try a
            # source-grounded Wikipedia response before queuing teaching.
            # Explicit truth blocks and stale checkpoints must not be bypassed.
            if not truth_block and not stale_internalized:
                from wiki_synonym_articles_v0628 import exact_title, distinct_pages, render_pages
                direct_article = exact_title(dispatch.focus)
                wiki_fallback=cha_unknown_wiki_fallback(
                    dispatch.focus,raw_user_text,cha_wiki_conversation.persona,
                    cha_wikipedia_lookup,cha_persona_wiki_respond,
                    grounded=cha_wiki_grounded_reply,cache=cha_persona_wiki_cache)
                # v0.6.27: when the surface form is UNKNOWN on Wikipedia,
                # retry approved lexical equivalents without changing the
                # user's query, the source trust state, or model weights.
                if wiki_fallback["status"]!="FOUND":
                    for synonym_term in synonym_lexicon.expand(dispatch.focus)[1:]:
                        if not truth_allows_direct_retrieval(
                                effective_truth_record(truth_store_path, dispatch.focus).state):
                            break
                        if not truth_allows_direct_retrieval(
                                effective_truth_record(truth_store_path, synonym_term).state):
                            continue
                        synonym_wiki = cha_unknown_wiki_fallback(
                            synonym_term, synonym_term + "とは",
                            cha_wiki_conversation.persona,
                            cha_wikipedia_lookup, cha_persona_wiki_respond,
                            grounded=cha_wiki_grounded_reply,
                            cache=cha_persona_wiki_cache)
                        if synonym_wiki["status"]=="FOUND":
                            wiki_fallback = synonym_wiki
                            print("[synonym_wiki_fallback, input={}, resolved={}]".format(
                                dispatch.focus, synonym_term))
                            print("[retrieval_trace=" + trace_match(dispatch.focus, synonym_term, "WIKIPEDIA", synonym_wiki.get("source","-"), "EXTERNAL_UNVERIFIED").as_json() + "]")
                            break
                if direct_article is not None:
                    synonym_article = None
                    if wiki_fallback["status"] == "FOUND":
                        synonym_article = exact_title(wiki_fallback.get("term", dispatch.focus))
                    distinct = distinct_pages([direct_article, synonym_article])
                    if len(distinct) > 1 or wiki_fallback["status"] != "FOUND":
                        print("AI> " + render_pages(distinct))
                        print("[route=WIKIPEDIA_SYNONYM_ARTICLES, count={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(len(distinct)))
                        print()
                        last_ai_reply = None
                        cha_wiki_last_generated = None
                        continue
                if wiki_fallback["status"]=="FOUND":
                    active_evidence_topic = wiki_fallback.get("term", dispatch.focus)
                    active_evidence_extract = ""
                    active_evidence_source = wiki_fallback.get("source", "")
                    topic_evidence.remember(active_evidence_topic, active_evidence_extract, active_evidence_source)
                    cha_wiki_conversation.offer(wiki_fallback["wiki_context"])
                    print("AI> "+wiki_fallback["answer"])
                    print("[route=UNKNOWN_WIKIPEDIA_FALLBACK, term={}, source={}, truth_state=EXTERNAL_UNVERIFIED, verified=False, train_ready=False, auto_promote=False, model_generation=SKIPPED]".format(
                        wiki_fallback["term"],wiki_fallback["source"]))
                    last_ai_reply=None
                    cha_wiki_last_generated=None
                    print()
                    continue
                print("[unknown_wiki_lookup={}, term={}]".format(
                    wiki_fallback["status"],dispatch.focus))
            if truth_block:
                route_result = "truth-state block"
                resolution_name = "TRUTH_BLOCK"
                action_name = "review/correct"
            elif stale_internalized:
                route_result = "checkpoint rebind required"
                resolution_name = "INTERNALIZED_STALE"
                action_name = "rebind/train"
            else:
                route_result = route_resolution_action(
                    args=args,
                    resolution="UNKNOWN_KNOWLEDGE",
                    action="retrieve/teach",
                    user_text=resolver_query,
                    candidate_answer="",
                    reason=(
                        f"knowledge state {dispatch.state}: "
                        f"{dispatch.reason}"
                    ),
                )
                resolution_name = "UNKNOWN_KNOWLEDGE"
                action_name = "retrieve/teach"
            block_reply = (
                truth_result.user_message
                if truth_result is not None
                and truth_result.runtime_status == "BLOCK"
                and truth_result.user_message
                else (
                    "学習証拠はありますが、現在のcheckpointには未反映です。"
                    if stale_internalized
                    else UNKNOWN_REPLY
                )
            )
            experimental_fallback = None
            if resolution_name == "UNKNOWN_KNOWLEDGE" and memory_first_enabled:
                try:
                    experimental_fallback = cha_memory_first_resolve(
                        raw_user_text,
                        PROJECT_ROOT / "data" / "approved_v071.jsonl",
                        PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                        enabled=True, mode=memory_first_mode,
                        generator=memory_first_generator,
                        resolution=resolution_name)
                    if experimental_fallback and experimental_fallback.get("answer"):
                        block_reply = experimental_fallback["answer"]
                except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
                    experimental_fallback = {"route":"EXPERIMENTAL_UNAVAILABLE",
                        "reason":type(exc).__name__, "truth_state":"UNKNOWN",
                        "auto_promote":False}
            if resolution_name == "UNKNOWN_KNOWLEDGE" and not memory_first_enabled and experimental_backend is not None:
                try:
                    experimental_fallback = fallback_on_structured_unknown(
                        raw_user_text, experimental_backend, allow=True)
                    if experimental_fallback and experimental_fallback["answer"]:
                        block_reply = experimental_fallback["answer"]
                except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
                    experimental_fallback = {"route": "EXPERIMENTAL_UNAVAILABLE",
                                             "reason": type(exc).__name__,
                                             "truth_state": "UNKNOWN", "auto_promote": False}
            if (experimental_fallback and experimental_fallback.get("answer")
                    and experimental_fallback.get("truth_state")=="EXPERIMENTAL_UNVERIFIED"):
                from experimental_wiki_append_v0734 import append_wikipedia
                wiki_append=append_wikipedia(block_reply,raw_user_text,lookup=cha_wikipedia_lookup)
                block_reply=wiki_append["answer"]
                print("[experimental_wiki_append={}, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]".format(
                    wiki_append["wiki_status"]))
            if experimental_fallback and experimental_fallback.get("reference_audit"):
                audit=experimental_fallback["reference_audit"]
                print("[candidate_reference: status={}, count={}, threshold={}, promoted={}]".format(
                    audit["status"],audit["reference_count"],audit["threshold"],audit["promoted"]))
            print(f"AI> {block_reply}")
            if experimental_fallback is not None:
                print("[experimental_route={}, truth_state={}, quality_reason={}, auto_promote=False]".format(
                    experimental_fallback["route"], experimental_fallback["truth_state"],
                    experimental_fallback["reason"]))
            print(
                f"[knowledge-state={dispatch.state}, "
                f"concept={dispatch.focus}, generation=blocked]"
            )
            print(f"[route={route_result}]")
            if truth_block:
                print(
                    "[truth path: set a correction with "
                    "/truthset CONCEPT FALSE|OUTDATED => CORRECTION]"
                )
            elif stale_internalized:
                print(
                    "[checkpoint path: run /train to replay trusted pairs "
                    "into the current checkpoint]"
                )
            else:
                print(
                    "[teaching path: /teach ANSWER -> /train "
                    "(or /teachq QUESTION => ANSWER)]"
                )
            provenance_text = (
                dispatch.provenance.compact()
                if dispatch.provenance is not None
                else "none"
            )
            truth_part = (
                f", truth_state={truth_record.state}"
                if truth_record is not None
                else ""
            )
            truth_runtime_part = (
                f", truth_runtime={truth_result.runtime_status}"
                if truth_result is not None
                else ""
            )
            print(
                f"[gate=UNKNOWN, resolution={resolution_name}, "
                f"action={action_name}, route={dispatch.route}, "
                f"reason={dispatch.reason}, provenance={provenance_text}"
                f"{truth_part}{truth_runtime_part}]"
            )
            print("[0 generated probe tokens, 0.00s, 0.0 tok/s]")
            print()
            last_ai_reply = None
            continue

        # GENERATE: INTERNALIZED, NON_CONCEPT, or active repair verification.
        if force_internalized_verification:
            internalized_record = verification_override_record
            print(
                "[internalized verification route: "
                f"concept={dispatch.focus!r}, "
                "generation=model-weights, "
                f"shadowed_semantic_state={dispatch.state}, "
                f"truth_state={truth_record.state if truth_record else 'UNVERIFIED'}]"
            )
        elif dispatch.state == "INTERNALIZED":
            internalized_records = load_internalized_records(
                learning_log,
                learning_state,
            )
            internalized_record = internalized_record_for_focus(
                internalized_records,
                dispatch.focus,
            )
            print(
                "[internalized route: "
                f"concept={dispatch.focus!r}, "
                "generation=model-weights, "
                f"truth_state={truth_record.state if truth_record else 'UNVERIFIED'}]"
            )
        else:
            internalized_record = None

        user_text = resolver_query

        generation_user_text = (
            internalized_record.question
            if internalized_record is not None
            else normalize_identity_query(user_text)
        )
        if cha_bridge.enabled:
            try:
                cha_bridge.record_user(raw_user_text)
            except (OSError, ValueError, KeyError) as exc:
                cha_bridge.enabled = False
                print(f"[CHA memory capture stopped: {exc}]")
        cha_user_context.observe(raw_user_text)
        generation_user_text = cha_resolve_context(generation_user_text, cha_recent_topic)
        user_topic = cha_topic_for(user_text)
        if user_topic:
            cha_recent_topic = user_topic
        prompt, selected_history = build_prompt(
            history=history,
            user_text=generation_user_text,
            history_turns=args.history_turns,
        )

        start = time.perf_counter()

        # Primary response: greedy when rejection is enabled so that the
        # displayed candidate itself is deterministic and reproducible.
        primary_temperature = 0.0 if args.unknown_rejection else args.temperature
        results = [
            generate_reply(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                max_new_tokens=args.max_new_tokens,
                temperature=primary_temperature,
                top_k=args.top_k,
                repetition_penalty=args.repetition_penalty,
                seed=0,
            )
        ]

        if args.unknown_rejection:
            for probe in range(max(0, args.probe_count - 1)):
                results.append(
                    generate_reply(
                        model=model,
                        tokenizer=tokenizer,
                        prompt=prompt,
                        max_new_tokens=args.max_new_tokens,
                        temperature=args.probe_temperature,
                        top_k=args.probe_top_k,
                        repetition_penalty=args.repetition_penalty,
                        seed=1000 + probe,
                    )
                )

        primary = results[0]

        accepted = True
        confidence = primary.mean_confidence
        agreement = 1.0
        semantic_agreement = 1.0
        reason = "rejection disabled"
        qa_similarity = 0.0
        previous_similarity = -1.0
        intent = "general"
        slots: list[str] = []
        slot_coverage = 1.0

        semantic_ok = True
        semantic_reason = "semantic check disabled"

        if args.semantic_consistency:
            # Run semantic verification first. v1.5.8 may relax agreement
            # only after slots/entities/intent are semantically validated.
            (
                semantic_ok,
                qa_similarity,
                previous_similarity,
                semantic_reason,
                intent,
                slots,
                slot_coverage,
            ) = semantic_consistency_check(
                model=model,
                tokenizer=tokenizer,
                current_question=user_text,
                answer=primary.text,
                history=selected_history,
                contamination_margin=args.history_contamination_margin,
            )

        answer_concept_ok, answer_concept_reason = answer_concept_consistency(
            user_text,
            primary.text,
        )
        if semantic_ok and not answer_concept_ok:
            semantic_ok = False
            semantic_reason = answer_concept_reason

        if args.unknown_rejection:
            effective_agreement = calibrated_agreement_threshold(
                intent=intent,
                semantic_ok=semantic_ok,
                slot_coverage=slot_coverage,
                base_threshold=args.min_agreement,
            )
            (
                accepted,
                confidence,
                agreement,
                semantic_agreement,
                reason,
            ) = evaluate_unknown_gate(
                model=model,
                tokenizer=tokenizer,
                results=results,
                min_confidence=args.min_confidence,
                min_token_confidence=args.min_token_confidence,
                min_mean_margin=args.min_mean_margin,
                min_agreement=effective_agreement,
                min_semantic_agreement=args.min_semantic_agreement,
                allow_semantic_rescue=(
                    semantic_ok
                    and slot_coverage >= 1.0
                    and internalized_record is None
                ),
            )
        else:
            effective_agreement = args.min_agreement

        if accepted and args.semantic_consistency:
            if not semantic_ok:
                accepted = False
                reason = semantic_reason
            elif reason == "accepted":
                reason = semantic_reason
            # Preserve diagnostic reasons such as "semantic probe agreement".

        # Do not accept a definition that does not mention the requested concept.
        if accepted and args.unknown_rejection and internalized_record is None:
            definition_ok, definition_reason = cha_definition_grounded(
                raw_user_text, primary.text
            )
            if not definition_ok:
                accepted = False
                reason = definition_reason

        if accepted and internalized_record is None and args.semantic_consistency:
            grounded_ok, grounding_reason = cha_topic_grounded(
                generation_user_text, primary.text, cha_recent_topic
            )
            if not grounded_ok:
                accepted = False
                reason = grounding_reason

        internalized_fidelity = -1.0
        internalized_lexical_coverage = -1.0
        internalized_required_coverage = -1.0
        internalized_contradiction = False
        internalized_missing_terms: tuple[str, ...] = ()
        if internalized_record is not None:
            composite_fidelity = composite_internalized_teacher_fidelity(
                model=model,
                tokenizer=tokenizer,
                generated_answer=primary.text,
                teacher_answer=internalized_record.teacher_answer,
                concept=internalized_record.concept,
            )
            internalized_fidelity = (
                composite_fidelity.semantic_similarity
            )
            internalized_lexical_coverage = (
                composite_fidelity.lexical_coverage
            )
            internalized_required_coverage = (
                composite_fidelity.required_coverage
            )
            internalized_contradiction = (
                composite_fidelity.contradiction
            )
            internalized_missing_terms = (
                composite_fidelity.missing_terms
            )
            fidelity_ok, fidelity_reason = (
                apply_composite_internalized_fidelity_policy(
                    accepted=accepted,
                    result=composite_fidelity,
                    semantic_threshold=args.min_internalized_fidelity,
                    lexical_threshold=(
                        args.min_internalized_lexical_coverage
                    ),
                    required_threshold=(
                        args.min_internalized_required_coverage
                    ),
                )
            )
            if not fidelity_ok:
                accepted = False
                if fidelity_reason:
                    reason = fidelity_reason
            elif accepted:
                reason = fidelity_reason

        resolution, action = classify_resolution(
            accepted,
            reason,
            user_text,
        )
        if internalized_record is not None and not accepted:
            resolution = "INTERNALIZED_UNSTABLE"
            action = "retrain/review"
            verification_path = Path(
                args.internalized_verification
            )
            upsert_internalized_unstable(
                verification_path,
                concept=internalized_record.concept,
                question=internalized_record.question,
                teacher_answer=internalized_record.teacher_answer,
                candidate_answer=primary.text,
                reason=reason,
                semantic=internalized_fidelity,
                lexical=internalized_lexical_coverage,
                required=internalized_required_coverage,
                contradiction=internalized_contradiction,
                missing_terms=internalized_missing_terms,
                fingerprint=internalized_record.fingerprint,
            )
            reactivated = mark_pair_for_retraining(
                learning_state,
                internalized_record.question,
                internalized_record.teacher_answer,
            )
            if reactivated:
                mark_internalized_verification_retrain(
                    verification_path,
                    internalized_record.fingerprint,
                )
            route_result = (
                "internalized verification loop: "
                + (
                    "trusted pair reactivated for /train"
                    if reactivated
                    else "verification task pending/retrain"
                )
            )
        else:
            route_result = route_resolution_action(
                args=args,
                resolution=resolution,
                action=action,
                user_text=user_text,
                candidate_answer=primary.text,
                reason=reason,
            )

        if accepted and internalized_record is not None:
            verified = mark_internalized_verification_verified(
                Path(args.internalized_verification),
                internalized_record.concept,
                internalized_record.fingerprint,
            )
            route_result = "internalized model generation"
            if verified:
                route_result += f"; verification resolved={verified}"

        recovery_reply = None
        recovery_evidence = []
        if not accepted and args.unknown_rejection and internalized_record is None and concept_from(raw_user_text) is None:
            if cha_bridge.source is not None and (
                cha_user_context.continuation(raw_user_text)
                or cha_topic_for(raw_user_text) is not None
            ):
                try:
                    from conversation_retrieval_v0509 import restore_user_context
                    stored_context, recovery_evidence = restore_user_context(
                        cha_bridge.source, raw_user_text
                    )
                    if stored_context is not None and (
                        cha_user_context.topic is None
                        or cha_user_context.continuation(raw_user_text)
                    ):
                        cha_user_context = stored_context
                except (OSError, ValueError, KeyError) as exc:
                    print(f"[CHA retrieval unavailable: {exc}]")
            recovery_reply = cha_user_context.recovery(raw_user_text)
        unknown_question = None
        if not accepted and args.unknown_rejection and internalized_record is None and not recovery_reply:
            unknown_question = cha_unknown_teacher.begin(raw_user_text, reason)
        reply = primary.text if accepted else (recovery_reply or unknown_question or UNKNOWN_REPLY)
        new_tokens = sum(r.token_count for r in results)

        if device.type == "cuda":
            torch.cuda.synchronize()

        elapsed = time.perf_counter() - start
        rate = new_tokens / elapsed if elapsed > 0 else 0.0

        if not reply:
            reply = UNKNOWN_REPLY if args.unknown_rejection else "(no response)"

        # v0.7.12: only an explicitly UNKNOWN GATE_REVIEW may consult
        # a matching PENDING Candidate, never an accepted Trusted answer.
        candidate_fallback = None
        if (not accepted and memory_first_enabled and internalized_record is None
                and not recovery_reply and args.unknown_rejection
                and reason == "low response agreement"):
            try:
                candidate_fallback = cha_memory_first_resolve(
                    raw_user_text,
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    enabled=True,mode=memory_first_mode,
                    generator=memory_first_generator,resolution="GATE_REVIEW")
                if candidate_fallback and candidate_fallback.get("answer"):
                    reply = candidate_fallback["answer"]
            except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
                candidate_fallback = {"route":"EXPERIMENTAL_UNAVAILABLE",
                    "reason":type(exc).__name__,"truth_state":"UNKNOWN",
                    "auto_promote":False}
        if (not accepted and not memory_first_enabled and experimental_backend is not None
                and internalized_record is None and not recovery_reply
                and args.unknown_rejection):
            try:
                from candidate_aware_fallback_v0712 import gate_review_fallback
                candidate_fallback = gate_review_fallback(
                    raw_user_text,
                    PROJECT_ROOT / "data" / "approved_v071.jsonl",
                    PROJECT_ROOT / "data" / "candidates_v071.jsonl",
                    experimental_backend,
                    resolution="GATE_REVIEW" if reason == "low response agreement" else "OTHER",
                    enabled=True,
                )
                if candidate_fallback and candidate_fallback["answer"]:
                    reply = candidate_fallback["answer"]
            except (OSError, ValueError, RuntimeError, KeyError, ImportError) as exc:
                candidate_fallback = {"route":"EXPERIMENTAL_UNAVAILABLE",
                                      "truth_state":"UNKNOWN",
                                      "reason":type(exc).__name__,
                                      "auto_promote":False}
        if (candidate_fallback and candidate_fallback.get("answer")
                and candidate_fallback.get("truth_state")=="EXPERIMENTAL_UNVERIFIED"):
            from experimental_wiki_append_v0734 import append_wikipedia
            wiki_append=append_wikipedia(reply,raw_user_text,lookup=cha_wikipedia_lookup)
            reply=wiki_append["answer"]
            print("[experimental_wiki_append={}, truth_state=EXTERNAL_UNVERIFIED, auto_promote=False]".format(
                wiki_append["wiki_status"]))
        if candidate_fallback and candidate_fallback.get("reference_audit"):
            audit=candidate_fallback["reference_audit"]
            print("[candidate_reference: status={}, count={}, threshold={}, promoted={}]".format(
                audit["status"],audit["reference_count"],audit["threshold"],audit["promoted"]))
        # v0.7.44.5 opt-in guard for accepted raw model generation only.
        # Do not alter Trusted retrieval, Candidate fallback or Wikipedia evidence.
        cha_quality_guard_status = None
        if (os.environ.get("LLM_CHA_RESPONSE_GATE", "0") == "1"
                and accepted and candidate_fallback is None):
            from response_quality_gate_v07443 import assess_response
            cha_persona_raw_audit = cha_persona_audit(
                "MODEL_GENERATION", reply, persona=cha_wiki_conversation.persona,
                persona_applied=False)
            cha_persona_gap = bool(cha_persona_raw_audit.get("persona_gap"))
            cha_quality_decision = assess_response(
                reply, persona_gap=cha_persona_gap, route="GENERATED",
                truth_state="UNKNOWN")
            # A missing persona presentation alone should not suppress all
            # answers. A suspicious low-token-confidence / agreement response
            # cannot pass on fluent-looking text alone.
            cha_low_signal = (primary.min_confidence < 0.10
                              or agreement < 0.10)
            cha_quality_guard_status = cha_quality_decision.action
            if cha_low_signal:
                cha_quality_guard_status = "LOW_SIGNAL_REJECT"
            elif cha_quality_guard_status == "REVIEW":
                # No live reviewer is available. Allow only high-signal text,
                # but clearly mark that persona presentation remains missing.
                cha_quality_guard_status = "PERSONA_GAP_OBSERVED"
            if cha_quality_guard_status in ("RETRY", "HOLD", "LOW_SIGNAL_REJECT"):
                reply = "回答をうまく生成できませんでした。もう一度質問してください。"
                # Do not admit a failed generated reply into context/learning.
                accepted = False
                # Recover a bare synonym through the existing Wikipedia evidence
                # route, without admitting rejected model text into learning.
                if cha_quality_guard_status == "LOW_SIGNAL_REJECT":
                    from synonym_recovery_v07448 import recover_bare_synonym
                    def _synonym_truth_allowed(term):
                        return truth_allows_direct_retrieval(
                            effective_truth_record(truth_store_path, term).state)
                    def _synonym_lookup(term):
                        return cha_unknown_wiki_fallback(
                            term, term + "とは", cha_wiki_conversation.persona,
                            cha_wikipedia_lookup, cha_persona_wiki_respond,
                            grounded=cha_wiki_grounded_reply,
                            cache=cha_persona_wiki_cache)
                    cha_recovered = recover_bare_synonym(
                        raw_user_text, synonym_lexicon,
                        _synonym_lookup, _synonym_truth_allowed)
                    if cha_recovered is not None:
                        from response_presentation_v07449 import present_synonym_recovery
                        reply = present_synonym_recovery(raw_user_text, cha_recovered["term"], cha_recovered["answer"])
                        cha_quality_guard_status = "SYNONYM_WIKIPEDIA_RECOVERY"
                        print("[synonym_recovery=FOUND, term={}, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(
                            cha_recovered["term"], cha_recovered["source"]))
        # v0.8.0.3: use isolated Wikipedia Semantic evidence only when
        # generation failed and no existing recovery provided a valid answer.
        if reply in (UNKNOWN_REPLY, "回答をうまく生成できませんでした。もう一度質問してください。"):
            from unapproved_fallback_v0803 import fallback_on_failure
            semantic_recovery = fallback_on_failure(raw_user_text, failed=True)
            if semantic_recovery["status"] == "FOUND":
                reply = semantic_recovery["answer"]
                accepted = False
                cha_quality_guard_status = "UNAPPROVED_SEMANTIC_FALLBACK"
                print("[unapproved_semantic_fallback=FOUND, source={}, truth_state=EXTERNAL_UNVERIFIED, train_ready=False, auto_promote=False]".format(semantic_recovery["source"]))
        cha_wiki_last_generated = reply
        print(f"AI> {reply}")
        if cha_quality_guard_status is not None:
            print("[response_quality_gate={}, opt_in=True, train_ready={}]".format(
                cha_quality_guard_status, accepted))
        if candidate_fallback is not None:
            print("[experimental_route={}, truth_state={}, reason={}, auto_promote=False]".format(
                candidate_fallback["route"],candidate_fallback["truth_state"],
                candidate_fallback["reason"]))
        print("[persona_audit="+json.dumps(cha_persona_audit(
            "MODEL_GENERATION",reply,persona=cha_wiki_conversation.persona,
            persona_applied=False),ensure_ascii=False)+"]")
        if unknown_question is not None:
            print("[unknown=KNOWLEDGE_CLARIFICATION, gate=UNKNOWN, train_ready=False]")
        if recovery_reply is not None:
            print("[recovery=USER_CONTEXT_TEMPLATE, gate=UNKNOWN, trusted=False, train_ready=False]")
            if recovery_evidence:
                item = recovery_evidence[0]
                print("[retrieval=user-report, conversation_id={}, source_turn={}, truth_state=USER_REPORTED_UNVERIFIED]".format(
                    item["conversation_id"], item["turn_id"]
                ))

        if args.show_risk and args.unknown_rejection and not accepted:
            print(f"[candidate={primary.text}]")

        if args.show_risk and args.unknown_rejection:
            if accepted and internalized_record is not None:
                status = "INTERNALIZED"
            else:
                status = "KNOWN" if accepted else "UNKNOWN"
            semantic_part = ""
            internalized_part = (
                (
                    f", internalized_concept={internalized_record.concept}"
                    f", teacher_sem={internalized_fidelity:.3f}"
                    f", teacher_lex={internalized_lexical_coverage:.3f}"
                    f", teacher_req={internalized_required_coverage:.3f}"
                    f", teacher_contra={internalized_contradiction}"
                    f", fidelity_th={args.min_internalized_fidelity:.3f}"
                    f", lex_th={args.min_internalized_lexical_coverage:.3f}"
                    f", req_th={args.min_internalized_required_coverage:.3f}"
                    f", missing={'|'.join(internalized_missing_terms) or '-'}"
                )
                if internalized_record is not None
                else ""
            )
            if args.semantic_consistency:
                slot_text = "|".join(slots) if slots else "-"
                internalized_part = (
                    (
                        f", internalized_concept={internalized_record.concept}"
                        f", teacher_sem={internalized_fidelity:.3f}"
                        f", teacher_lex={internalized_lexical_coverage:.3f}"
                        f", teacher_req={internalized_required_coverage:.3f}"
                        f", teacher_contra={internalized_contradiction}"
                        f", fidelity_th={args.min_internalized_fidelity:.3f}"
                        f", lex_th={args.min_internalized_lexical_coverage:.3f}"
                        f", req_th={args.min_internalized_required_coverage:.3f}"
                        f", missing={'|'.join(internalized_missing_terms) or '-'}"
                    )
                    if internalized_record is not None
                    else ""
                )
                semantic_part = (
                    f", intent={intent}"
                    f", slots={slot_text}"
                    f", slot_cov={slot_coverage:.2f}"
                    f", qa_sim={qa_similarity:.3f}"
                    f", prev_sim={previous_similarity:.3f}"
                    f", agr_th={effective_agreement:.2f}"
                )
            truth_part = (
                f", truth_state={truth_record.state}"
                if truth_record is not None
                else ""
            )
            print(
                f"[gate={status}, "
                f"confidence={confidence:.3f}, "
                f"min_tok_conf={primary.min_confidence:.3f}, "
                f"mean_margin={primary.mean_top2_margin:.3f}, "
                f"agreement={agreement:.3f}, "
                f"sem_agreement={semantic_agreement:.3f}"
                f"{semantic_part}"
                f"{internalized_part}"
                f"{truth_part}, "
                f"context_turns={len(selected_history)}, "
                f"resolution={resolution}, action={action}, "
                f"route={route_result}, reason={reason}]"
            )

        # Read-only suggestion: never auto-fetch Wikipedia or override the answer.
        from wiki_retry_v0539 import resolve_topic as cha_wiki_resolve_topic
        quality=cha_answer_quality_evaluate(
            raw_user_text, reply, accepted=accepted, agreement=agreement,
            resolution=resolution, wiki_topic=cha_wiki_resolve_topic(raw_user_text))
        print("[answer_quality={}, reason={}, wiki_suggested={}]".format(
            quality["status"],quality["reason"],quality["suggest_wiki"]))
        if quality["suggest_wiki"]:
            print("[wiki_repair_hint=根拠を確認するには /wiki を入力してください。]")

        print(
            f"[{new_tokens} generated probe tokens, "
            f"{elapsed:.2f}s, "
            f"{rate:.1f} tok/s]"
        )
        print()

        # v1.5.4 clean-history policy:
        # only accepted KNOWN turns may enter future generation context.
        # UNKNOWN/rejected turns are intentionally discarded.
        if accepted:
            resolved = resolve_teaching_queue(
                Path(args.teaching_queue),
                user_text,
            )
            if resolved:
                print(f"[resolved teaching queue entries: {resolved}]")
            history.append((user_text, reply))
            if cha_bridge.enabled:
                try:
                    cha_bridge.record_assistant(reply)
                except (OSError, ValueError, KeyError) as exc:
                    cha_bridge.enabled = False
                    print(f"[CHA memory capture stopped: {exc}]")
            last_ai_reply = reply
            if learning_enabled:
                print("[learning candidate ready: use /good to approve or /teach TEXT to correct]")
        else:
            last_ai_reply = None


if __name__ == "__main__":
    main()
