# LLM_CHA v0.9.7.14 — Grounded LLM Generation (opt-in diagnostic)

This release connects the *actual chat.py checkpoint* through its existing
`generate_reply(model, tokenizer, prompt, ...)` function to the clipboard
evidence flow. It is not simulated text or a hand-authored candidate.

The existing v0.9.6 heuristic gate compares the generated candidate with
retrieved source evidence. **That gate cannot guarantee factual entailment**
(especially for Japanese questions and English quotations). Therefore the
answer shown to the user remains the prior source-quotation baseline, even
when the diagnostic gate reports acceptance. The raw candidate and gate
details are printed to the CLI for comparison, without auto-promotion.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.14
python -m unittest -v test_clipboard_grounded_generation_v09714.py test_clipboard_structured_association_v09713.py
python chat.py
```

After manually copying WIZG.org research text into clipboard:

```text
You> /read-clipboard
You> /clipboard-generate このページでQuantum Hyper-Aetherについて記述は？
```

The command calls the loaded LLM once using an evidence-conditioned prompt,
prints the baseline and generation diagnostics, and keeps
`train_ready=false`. Generated text is experimental and not injected into
conversation context or Semantic Memory. It may be poor because the current
small model was not trained for English-evidence Japanese QA.

Next step: record held-out answer quality and add strong attribution/
entailment checks before enabling model output as a normal answer.
