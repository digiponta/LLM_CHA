# LLM_CHA v0.13.58.82.57: Definition and Temporal Anaphora Filtering

Based on the v0.56 evaluation: "宇宙とは" incorrectly selected a historical opinion sentence; "ビッグバンはいつ" correctly selected a local anaphoric age sentence, but extracted "今から138.2億年" without the trailing "前".

This branch provides a strictly offline alternative to the v0.56 binding module:
- Reject historical-opinion language ("考え方", "支配的", "世紀前半", etc.) as universe definitions.
- Require an explicit definition predicate for Universe, rather than matching generic "宇宙は...という".
- Require a local previous sentence with the Big Bang event for "その時刻"/"その時期".
- Capture age expressions with a mandatory trailing "前", optionally after the parenthetical scientific-year notation.
- Abstain on unsupported causal, subject, or relation claims; retain strict substring Evidence Gate.
- No checkpoint training or production GUI changes.

These rules are deliberately conservative and heuristic. Scientific correctness, cross-document coreference, other event types, and semantically equivalent paraphrases are not established.

## Windows PowerShell

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.57-definition-anaphora
    python -m unittest -v test_evidence_definition_anaphora_v013588257.py test_evidence_relation_binding_v013588256.py
    python evaluate_definition_anaphora_v013588257.py --evidence-json results/evidence_snapshot_v013588249.json --output results/definition_anaphora_v013588257.json
    Get-Content results/definition_anaphora_v013588257.json -Encoding UTF8

Expected for the saved snapshot: Universe definition abstains; Big Bang time selects the age sentence with "前" in the value; Universe cause abstains; Universe composition abstains. Do not integrate into production until independent holdouts confirm low false-accept rate.
