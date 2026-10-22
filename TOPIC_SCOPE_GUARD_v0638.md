# v0.6.38 — Topic-Scoped Wikipedia Evidence and Greeting Guard

- Saves topic, extract and URL when a named entity is resolved from Wikipedia, or
  the UNKNOWN Wikipedia fallback returns a topic.
- Handles short followups such as `メニューは` for Starbucks and `所在地は`
  for Toyota **before** the generic Wikipedia synonym-article route.
- For an address, uses only a matching sentence from the active entity's
  captured extract; otherwise explicitly says that the current source is
  insufficient. Always labels Wikipedia evidence EXTERNAL_UNVERIFIED.
- Simple standalone greetings are answered with conservative pre-reviewed
  templates instead of low-quality model-generation candidates.
- Approved QA routing and slash commands remain available.

## Test

```powershell
git fetch origin
git switch --track origin/v0.6.38
python -m unittest -v test_topic_scope_guard_v0638.py test_approved_synonym_qa_v0637.py

python chat.py --approved-qa-overlay data/my_approved_qa_test.jsonl
```

Try `こんにちは`, `スターバックスとは` → `メニューは`, and
`トヨタの話題` → `所在地は`. No automatic knowledge promotion.

This is a narrow scoped rule, not a general multi-turn entity tracker.
The Wikipedia extract may not contain the requested fact; in that case no
invented answer is provided. Expand entity/property coverage separately.
