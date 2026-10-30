# LLM_CHA v0.13.58.82.38 — Corpus–Evidence Interference Probe

Purpose: investigate whether the small model blends distinct meanings of "脳と宇宙" from data-nagato.txt with an external Wikipedia cosmology excerpt. A keyword overlap is **not** proof of a shared meaning or of a causal source for the output.

Four deterministic greedy generation prompts, with the same checkpoint:
- A: topic only
- B: externally retrieved evidence only
- C: matching raw corpus passage only
- D: both sources, explicitly labeled separately

The diagnostic `/interference-compare` command reads local `data/data-nagato.txt`, selecting a line ranked by containing both terms ("脳", "宇宙"). This is lexical retrieval only; confirm the chosen text and its true semantic meaning before conclusions. The experiment prints the corpus line number, each raw candidate, and two **lexical** similarity values. No generated text is approved, added to history, queued for training, or internalized.

## Windows steps

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.38-corpus-evidence-interference
python -m unittest -v test_corpus_evidence_interference_v013588238.py test_evidence_aware_route_v013588236.py
python prepare_interference_command_v013588238.py --topic 宇宙
python chat.py
```

Copy the printed `/interference-compare ...` line into **chat.py's console input** (not the GUI: the GUI currently has no special renderer for this diagnostic command). Copy the resulting `[interference-experiment]` JSON for inspection.

The helper's default evidence text is a brief illustrative cosmology sentence, **not** a live Wikipedia retrieval. To substitute verified actual source text pass `--evidence "..." ` and record its URL separately.

Caveats: The command runs four separate model generations, so this may take some seconds. It uses the active chat.py checkpoint. The selected corpus *line* can be an incomplete passage; a later revision should select annotated semantic spans. The output distinguishes lexical signals but cannot prove the origin of a specific word from model weights. No semantic similarity or entailment is claimed.
