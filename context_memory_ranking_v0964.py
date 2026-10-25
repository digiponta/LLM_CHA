"""v0.9.6.4: Context-dependent ranking of unverified memory excerpts.

Article choice is a ranking hint, not proof that the requested topic and
Wikipedia article are equivalent. Original text and position are unchanged.
"""
from memory_subtopic_v0963 import retrieve, retrieve_from_file

ARTICLE_PREFERENCES={
    "記憶装置":("CPU_MEMORY","VIRTUAL_MEMORY","DATABASE_MEMORY","EXTERNAL_MEMORY"),
    "フラッシュメモリ":("EXTERNAL_MEMORY","CPU_MEMORY","VIRTUAL_MEMORY"),
    "仮想記憶":("VIRTUAL_MEMORY","CPU_MEMORY"),
    "仮想メモリ":("VIRTUAL_MEMORY","CPU_MEMORY"),
    "データベース":("DATABASE_MEMORY","VIRTUAL_MEMORY"),
    "脳の記憶":("BIOLOGICAL_MEMORY",),
}

def rank_memory_evidence(evidence, selected_article=None, max_items=3):
    article=str(selected_article or "").strip()
    preferred=ARTICLE_PREFERENCES.get(article,())
    rows=[]
    for item in evidence:
        label=item["subtopic"]
        priority=preferred.index(label) if label in preferred else len(preferred)
        # Exact evidence is preserved; preserve natural document order inside tier.
        rows.append({**item,"article_context":article or None,
                     "rank_priority":priority,"context_match":label in preferred})
    if preferred:
        rows.sort(key=lambda item:(item["rank_priority"],item["position"]))
    return rows[:max_items]

def ranked_from_corpus(topic, corpus, selected_article=None, max_items=3):
    all_hits=retrieve(topic,corpus,max_items=10000)
    return rank_memory_evidence(all_hits,selected_article,max_items)

def ranked_from_file(topic,path="data/data-nagato.txt",selected_article=None,max_items=3):
    all_hits=retrieve_from_file(topic,path)
    # retrieve_from_file caps output at three; read full corpus for ranking.
    from pathlib import Path
    source=Path(path)
    if not source.is_file():
        return []
    return ranked_from_corpus(topic,source.read_text(encoding="utf-8-sig"),
                              selected_article,max_items)
