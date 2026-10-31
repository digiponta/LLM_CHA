# v0.13.58.82.90 — Real Persona Chat Readiness Audit

Target local folder: `C:\Users\inoma\git\misc\LLM_CHA\data-src\real-persona-chat`. Its actual content is NOT currently available in GitHub. Do not train without inspecting actual schema, roles, and permission to use the dialogues.

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.90-real-persona-audit
python -m unittest -v test_real_persona_audit_v013588290.py
python inspect_real_persona_v013588290.py --source data-src/real-persona-chat
```

The inventory reports file names, sizes, extensions and **field names only**; it does not output dialogue text. Review the result at `results/real_persona_inventory_v013588290.json`.

Next, based on the real schema, convert only authorized dialogue turns into distinct training pairs, de-identify private content, keep separate original validation and evaluation by *conversation*, preserve persona tags and turn boundaries, and ensure that the five v0.83 holdout questions and answers never appear in training. Run learning from the original checkpoint with **a distinct model output and distinct training state**. Evaluate against existing daily holdout, unseen new persona dialogs, and the semantic memory regression tests before promotion.

No model weights changed; no training automatically started in this version.
