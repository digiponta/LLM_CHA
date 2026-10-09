# LLM_CHA v0.2.17 — Human-Blind Decoding Quality Benchmark

Purpose: choose decoding based on **actual response quality**, not answer length or EOS frequency alone. This experiment changes no model weights or `chat.py` defaults.

## Build evaluation sheet

```powershell
git fetch origin
git switch --track origin/v0.2.17
python -m unittest -v test_decoding_quality_v0217.py test_eos_decoding_v0216.py

# Rebuild v0.2.16 traces if absent
python diagnose_eos_decoding_v0216.py --max-rows 30

python evaluate_decoding_quality_v0217.py
```

This reads `results/eos_decoding_v0216.json` and produces:
- `results/decoding_quality_v0217/blind_ratings.csv`
- `results/decoding_quality_v0217/blind_key.json` (mapping from anonymous response IDs to model/decoding conditions; **do not consult before rating**)

The sheet includes all three previously compared models and three decoding settings (up to 270 anonymous responses for 30 test prompts), randomized with a fixed seed. To avoid bias, scores are entered for outputs without labels for the originating model or decoder. Each answer is rated 1–5 on **naturalness, topic relevance, substance, coherence** and 0/1 for **unintelligible**. Empty rows are skipped, and partially filled rows cause an error. `--score` summarizes conditions only when at least 10 samples were rated for that condition.

```powershell
python evaluate_decoding_quality_v0217.py --score
```

Result: `results/decoding_quality_v0217/scores.json`.

## Evaluation guidance

The weighted composite is 30% naturalness + 35% topic relevance + 20% substance + 15% coherence. It is a predeclared descriptive index, **not** a validated measure of intelligence, and is not a substitute for examining individual failures. Report each dimension and the unintelligible fraction.

With a 30-example preliminary dataset, differences may not be robust. If two methods have close scores, rerun the EOS decoding benchmark on more prompts and multiple seeds, then obtain independent ratings. For method comparison, use matched prompts and consistent scorer rules. Use manual inspection to ensure long outputs are not merely nonsensical.

## Decision gate (manual)

Recommend a decoding candidate only if it:
1. obtains higher topic-relevance and naturalness ratings on matched prompts;
2. does not increase unintelligible output frequency;
3. performs acceptably on continuation requests and held-out topics;
4. preserves the downstream Unknown/Semantic safety checks when tested with the actual chat runtime.

Do not change default decoding parameters solely because sampled text is longer. Do not change EOS constraints or train the checkpoint during this evaluation. All three settings currently share the same repetition penalty (1.15); the measured differences are exploratory. The evaluation is *raw generation*, without retrieval, persona routing, reranking and quality gates.

## Limitations

Blindness masks model/decoder labels but not the actual generated text; the key file must remain hidden. Ratings from a single reviewer are subjective; they should be repeated or adjudicated. Greedy is deterministic while sampling has random seed variance. Use the full saved per-token EOS traces for diagnostic reproduction.
