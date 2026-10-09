# LLM_CHA v0.2.16 — EOS and Decoding Collapse Root-Cause Study

This branch **does not train or change** any models. It directly compares greedy and seeded sampling on identical held-out prompts for checkpoints v0.2.8, v0.2.11 and v0.2.12.

## Measurements

At each generated step: post-repetition-penalty, pre-temperature EOS probability and rank; EOS probability under the actual decoding distribution (0/1 for deterministic greedy), selected token EOS indicator. Record answer length in tokens, EOS stopping fraction, generic-response proxy, fraction shorter than eight Japanese characters, and initial EOS probability/rank.

Configurations: greedy temperature 0, sampling temperature 0.7/top_k 40, sampling temperature 1.0/top_k 40. All use repetition penalty 1.15 and each row's deterministic seed. Unlike chat.py inference these tests deliberately bypass retrieval, dialogue reranking, persona router, and Unknown Gate.

The probabilistic EOS analysis is post-repetition-penalty: tokens already seen in the prompt can affect it. The evaluation does not apply chat.py generation cleanup; compare text manually, and avoid assuming any differences are caused *only* by EOS. Short replies may end naturally or truncate at max_new_tokens: the report distinguishes EOS stops.

## Commands

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.2.16
python -m unittest -v test_eos_decoding_v0216.py
python diagnose_eos_decoding_v0216.py --max-rows 30
```

Output: `results/eos_decoding_v0216.json` contains all per-token traces.

## Interpretation

- High EOS rank-1 frequency on initial generation steps or high EOS stop frequency with short lengths: stopping behavior may contribute.
- Greedy short and generic, sampling longer/more diverse without unacceptable incoherence: decoding bias likely contributes. Human review required.
- EOS probability low early but short/generic text remains: investigate generation distribution, pretraining and repetition, not just EOS.
- Similar issues across decoders: likely structural, learned distribution or tokenizer/pretraining limits rather than a single decoding choice.
- Check normalization, reference text lengths and time-to-EOS curves before tuning decoding. No EOS suppression or minimum reply length is imposed.

These are observational diagnostics and cannot establish causal root cause in isolation. Conduct controlled decoding/training interventions after reviewing results.
