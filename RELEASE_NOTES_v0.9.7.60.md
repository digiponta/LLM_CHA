# LLM_CHA v0.9.7.60 — Evidence-Based Causal Questions

Experimental extension from v0.9.7.59.

Changes:
- clipboard_causal_evidence_v09760.py finds a literal causal explanation in a short copied-source line.
- chat.py calls this retrieval before short-context fallback.
- test_clipboard_causal_evidence_v09760.py has seven focused tests.
- GUI continues to launch the shared chat.py, so it inherits the route.

Retrieval is conservative, limited to cutting difficulty, rainbow/fire, and fragility word patterns. It requires an explicit reason connector (ため/により/ので/から) and a unique supporting line. It returns a source quotation labeled EXTERNAL_UNVERIFIED, never inferred science.

### Windows verification

```powershell
git fetch origin
git switch v0.9.7.60
git pull --ff-only
python -m unittest -v test_clipboard_causal_evidence_v09760.py test_clipboard_attribute_retrieval_v09759.py test_gui_clipboard_v09758.py
python chat_window_v061.py
```

After copying the sphalerite results using the GUI clipboard button, test `なぜカットが難しいの？` and `なぜ虹色に輝くの？`. Both should return quoted evidence with the CLIPBOARD_CAUSAL_EVIDENCE route, assuming the topic has first been registered by a question such as `スファレライトの硬度は？`.

No Windows runtime verification or independent source-truth verification has yet been performed. No source promotion/persistent memory updates are introduced.
