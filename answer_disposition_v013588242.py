"""Truthful per-answer display of LLM candidate disposition."""

def answer_disposition(route, gate=None):
    if route == "EVIDENCE_GATE":
        if str(gate).startswith("REJECT_"):
            return "［LLM回答：破棄／Evidence Gate: " + str(gate) + "。表示文は参考資料・代替回答］"
        return "［LLM回答：採用／Evidence Gate: " + str(gate or "UNSPECIFIED") + "］"
    if route == "UNKNOWN_FALLBACK":
        return "［LLM回答：採用せず／未学習判定。参考資料を検索］"
    if route == "WIKI_RETRIEVAL":
        return "［LLM生成：なし／Wikipedia検索結果（外部未検証）］"
    if route == "NO_CANDIDATE":
        return "［LLM生成：なし／参考資料または代替回答］"
    if route == "CLI_ANSWER":
        return "［LLM回答：採否未判定／CLIの生成・検索ルートをGUIで識別できません］"
    raise ValueError("UNKNOWN_DISPOSITION_ROUTE")
