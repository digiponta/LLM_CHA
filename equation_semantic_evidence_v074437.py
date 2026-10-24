"""v0.7.44.37: evidence-bound equation meaning."""
def equation_meaning(wiki, blocks):
    if not isinstance(wiki, dict) or wiki.get("title") != "量子ビット":
        return None
    if not isinstance(blocks, list):
        return None
    formulas = [b.get("latex", "") for b in blocks if isinstance(b, dict) and b.get("source") == wiki.get("url")]
    sup = next((t for t in formulas if "rangle" in t and "+" in t), None)
    norm = next((t for t in formulas if "=" in t and "^2" in t), None)
    if not sup or not norm:
        return None
    return {"topic": "量子ビット", "source": wiki["url"],
            "equations": [{"role": "SUPERPOSITION", "latex": sup}, {"role": "NORMALIZATION", "latex": norm}],
            "meaning": ["重ね合わせの式には2つの基底状態と係数がある。", "正規化条件は係数の絶対値の2乗の和が1であることを示す。"],
            "truth_state": "EXTERNAL_UNVERIFIED", "train_ready": False, "auto_promote": False}

def render_meaning(block):
    if not block:
        return None
    return "取得したWikipedia数式の構造を説明する。\n" + "\n".join(block["meaning"]) + "\n出典：" + block["source"] + "\n（外部資料・未検証）"
