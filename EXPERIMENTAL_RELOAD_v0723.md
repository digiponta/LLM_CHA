# LLM_CHA v0.7.23: /sleep Experimental Adapter Reload

After an Experimental /sleep returns TRAINED or ALREADY_TRAINED, if
`LLM_CHA_MEMORY_FIRST=1` and `LLM_CHA_MEMORY_FIRST_MODE=constrained`,
the running chat process verifies and hot-reloads that specific newly
trained Experimental checkpoint.

Validation requires:
- Experimental route and `approved=False`.
- Exact current PENDING Candidate ID set.
- Valid rank, adapter weights and Base model hash verified by the backend.
- A successful Experimental inference initialization.

A rejected checkpoint leaves the earlier inference backend unchanged.
Approved Semantic Memory, Trusted LLM weights and Trusted training are not
modified by this reload. Candidate answers remain tagged
`EXPERIMENTAL_UNVERIFIED`. Even after successful reload, generated text
must exactly match the Candidate evidence to count as consistent; otherwise
Memory-First retains the registered unverified Evidence answer.

This version reloads after `/sleep` in the **current process** only;
a process restart does not automatically select the last sleep checkpoint.
It also does not prove that the Experimental LLM learned to generalize.
Compare generated consistency in subsequent experiments.

## Run in Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.23
python -m unittest -v test_experimental_reload_v0723.py test_experimental_sleep_v0722.py test_dual_runtime_bridge_v0721.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat.py
```

In chat, enter `/sleep` and inspect the
`[experimental adapter reload: status=LOADED]` diagnostic,
then query the matching experimental Candidate. The checkpoint is loaded
lazily from Base + Experimental Adapter, not into Trusted weights.
