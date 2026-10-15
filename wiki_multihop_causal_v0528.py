"""v0.5.28 explicit two-hop causal chains with per-edge provenance.

Only joins two independently sourced, explicitly stated causal edges.
No inferred bridges, no training, no automatic semantic promotion.
The limited term vocabulary is intentionally restrictive.
"""
from wiki_causal_direction_v0527 import check_direction

MARKERS=("によって","により","ことで","ため")
TERMS={
 "JOSEPHSON":("ジョセフソン効果","ジョセフソン接合"),
 "QUANTUM_INTERFERENCE":("量子干渉",),
 "FLUX_DETECTION":("磁束の変化","磁束変化","磁束を検出"),
 "WEAK_FIELD":("微弱な磁場","弱い磁場","小さな磁場"),
 "HIGH_SENSITIVITY":("高感度","感度が高"),
 "MRI":("MRI","撮像"),
}
def _label(s):
 hits=[k for k,forms in TERMS.items() if any(f in s for f in forms)]
 return hits[0] if len(hits)==1 else None

def edge(sentence,source):
 if not isinstance(sentence,str) or not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/"):
  return None
 pairs=[(sentence.find(m),m) for m in MARKERS if m in sentence]
 if not pairs:return None
 p,m=min(pairs)
 left,right=sentence[:p],sentence[p+len(m):]
 a,b=_label(left),_label(right)
 if not a or not b or a==b:return None
 return {"cause":a,"effect":b,"sentence":sentence,"source":source}

def compose(question,evidences):
 if "なぜ" not in question or "高感度" not in question:
  return {"status":"NOT_APPLICABLE"}
 edges=[]
 for item in evidences[:20]:
  if not isinstance(item,dict):continue
  e=edge(item.get("sentence"),item.get("source"))
  if e:edges.append(e)
 for first in edges:
  for second in edges:
   if first is second or first["effect"]!=second["cause"]:continue
   if second["effect"] not in ("HIGH_SENSITIVITY","WEAK_FIELD"):continue
   if first["cause"] in ("MRI", "HIGH_SENSITIVITY"):continue
   # Existing per-sentence causal checker cannot establish multi-hop
   # entailment, so preserve exact two-edge evidence and no prose synthesis.
   return {"status":"CHAIN_FOUND","hops":[first,second],"verified":False,
           "train_ready":False,"quality_gate":"EXPLICIT_TWO_EDGE_CHAIN"}
 return {"status":"NO_SUPPORTED_CHAIN","verified":False,"train_ready":False}
