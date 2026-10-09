# LLM_CHA v0.2.27 — Response Initiation & Grounded Generation Learning

Status: experimental scaffold; no GPU training/evaluation results claimed.

## Hypothesis
Even when context is identified correctly, generic high-frequency response
openers can dominate autoregressive generation. Training the *first assistant
response tokens* separately may improve topic-grounded initiation without
damaging general conversation.

## Controlled comparisons
- A: v0.2.26 checkpoint, evaluation only (no training).
- B: standard SFT, identical samples/updates.
- C: same SFT plus initiation auxiliary loss (K=4/8/16, lambda=0.25/0.5/1).
- D: C plus separately specified context-persistence supervision (future extension).

For comparable attribution, hold seed, optimizer, data ordering, train steps,
batch composition, evaluation prompts, and generation settings constant.

## Module integration
The new `response_initiation_v0227.initiation_loss(logits, targets, mask, k, weight)`
expects **causally aligned** logits and targets. Construct `mask` using the
conversation renderer's assistant-role token spans; prompt/padding tokens must
be 0. If the training loop uses unshifted `input_ids`, shift logits, targets,
and role masks together before calling the loss. Verify label/token offsets,
especially at assistant delimiters and with truncation.

## Suggested experiment grid
- K: 4, 8, 16
- lambda: 0, 0.25, 0.5, 1.0
- Compare distinct known-topic and unseen-topic prompt sets.
- Evaluate Japanese fluency, topic grounding, persistence, and persona/general chat retention.
- Semantic grounding must *not* require literal topic-string copying.

## Acceptance criteria
Any claim of generalization requires independent, topic-disjoint holdouts.
Improvements on trained topics alone are insufficient. Keep the v0.2.26
checkpoint unchanged and record actual per-condition seeds, sample counts,
losses, metrics, and decoded examples before drawing conclusions.

## Unit tests
```powershell
python -m unittest -v test_response_initiation_v0227.py
```
