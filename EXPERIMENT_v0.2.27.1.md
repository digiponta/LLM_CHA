# LLM_CHA v0.2.27.1 — Context-Selective Initiation / Raw Runtime Diagnostics

Experimental branch derived from v0.2.27. No GPU runs or quality improvements claimed yet.

## Installation / tests

```powershell
git fetch origin
git switch v0.2.27.1
python -m unittest -v test_response_initiation_v0227.py test_context_selective_v02271.py test_raw_runtime_v02271.py
python run_context_selective_v02271.py --dry-run
```

## Train (same input, base checkpoint, exposures and LRs as v0.2.27)

```powershell
python run_context_selective_v02271.py --init-k 8 --init-weight 0.5
```

Original comparison checkpoints remain untouched. Contrast v0.2.27's baseline and full initiation with this new selective checkpoint. The context flag is tied to the expansion-data provenance, *not* substring or topic matching. Base replay and persona examples remain standard SFT.

## Isolate raw model generation

```powershell
python diagnose_raw_runtime_v02271.py --model model/model-llm-cha-v0227-baseline.pt --out results/raw-baseline-v02271.jsonl
python diagnose_raw_runtime_v02271.py --model model/model-llm-cha-v0227-init-k8.pt --out results/raw-init-v02271.jsonl
python diagnose_raw_runtime_v02271.py --model model/model-llm-cha-context-selective-v02271.pt --out results/raw-selective-v02271.jsonl
```

The raw diagnostic uses direct deterministic (`temperature=0`) generation from
the common prompt template `人: {query}\nAI: `. It bypasses all chat.py
preprocessing and routing. It is *not* guaranteed to match chat.py's raw
internal candidate, especially for multi-turn prompts.

Optionally capture terminal text from a real chat.py run (as UTF-8), then:
```powershell
python diagnose_raw_runtime_v02271.py --model model/model-llm-cha-context-selective-v02271.pt --runtime-log results/chat-log.txt --out results/selective-with-runtime.jsonl
```
Only exactly matching prompt lines are joined, in occurrence order.
A missing runtime answer is recorded as null, never invented.

## Follow-up evaluation
- compare raw and final response separately
- context-topic grounding at initiation and at the end
- holdout topic generalization, and ordinary conversation preservation
- use full multi-turn prompts when evaluating conversational context
- retain the untouched checkpoints as comparison points

**Important:** A runtime mismatch in this diagnostic does not prove Gate changed
the candidate because raw and runtime prompt shaping may differ.
