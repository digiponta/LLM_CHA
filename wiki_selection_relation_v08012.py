"""v0.8.0.12: preserve the requested subject when selecting a Wikipedia hit.

Without verified equivalence evidence, different titles are related articles,
not aliases. No assertion about factual relationship is inferred.
"""
def selection_relation(requested_topic, selected_article):
    requested=(requested_topic or "").replace("_"," ").strip()
    selected=(selected_article or "").replace("_"," ").strip()
    if not requested or not selected:return "UNKNOWN"
    if requested==selected:return "EXACT"
    return "RELATED_UNVERIFIED"

def selection_notice(requested_topic, selected_article):
    status=selection_relation(requested_topic,selected_article)
    if status=="EXACT":return ""
    return ("注意：質問対象は「{}」ですが、選択された記事は「{}」です。"
            "同じ概念とは確認されていません。以下は選択記事の説明です。\n").format(
                requested_topic,selected_article)
