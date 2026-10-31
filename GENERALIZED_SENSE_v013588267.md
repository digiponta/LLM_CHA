# v0.13.58.82.67 Generalized Sense Binding

Adds evidence_generalized_sense_v013588267.py for a narrow, extensible Subject/Sense/Relation/Value/Evidence registry. Initial senses: computer memory versus human memory; machine-learning model versus physics model. Each accepted sense requires a source sentence with explicit lexical cues and the existing exact-source Evidence Gate. If the question is ambiguous and multiple supported senses appear, select one supported sense and include a notice about alternatives; if the user explicitly requests an unsupported sense, abstain.

The existing universe/universe-space logic remains first in the shared bridge and is not replaced. chat.py and chat_gui.py continue to use the shared bridge from v0.65. This is research-only source interpretation, NOT general-purpose semantic understanding or truth verification.

Run on Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.67-generalized-sense-binding
    python -m unittest -v test_generalized_sense_v013588267.py test_universe_sense_notice_v013588266.py test_chat_unified_grounding_v013588265.py

New memory/model senses need corresponding evidence records in the snapshot (source title matching the subject), since the current collector only captures eight astronomy/mineral/CPU sources. Without such evidence, normal chat retains the existing fallback. Tests do not require fetching or approving new data.

No production weights, human-reviewed approvals or /good policy have been changed.
