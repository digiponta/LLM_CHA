# v0.7.44.21 — Missing Formula Integrity Gate

Observed after successful topic-context repair:
- `状態ベクトル   （もしくは波動関数   ）`
- `状態   と別の状態   で次のような状態   を作る`

The current Wikipedia evidence extension uses MediaWiki
`explaintext=1`, which may drop math payloads entirely. The GUI's
`LATEX(...)` renderer cannot reconstruct markup that was removed upstream.

This update conservatively excludes source sentences containing
suspicious multiple-space gaps after mathematical operands.
No equation is invented. Further valid prose segments may still be
returned; absent eligible evidence, the existing exhaustion response is used.

```powershell
git pull
python -m unittest -v test_wiki_math_integrity_v074421.py test_wiki_math_wiring_v074421.py
python chat_gui_v07447.py
```

Manual regression: 量子ビットとは？ → 量子重ね合わせについて教えて →
もっと詳しく ×2. Neither reply should display missing-operand
fragments. This is a targeted guard, not full Wikipedia MathML/LaTeX
reconstruction. GPU/GUI acceptance is pending.
