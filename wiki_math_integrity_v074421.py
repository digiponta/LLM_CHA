"""v0.7.44.21: reject plaintext Wikipedia evidence with missing math operands.

MediaWiki extracts with explaintext=1 can lose formula objects. We must not
pretend that an equation-less sentence is complete source evidence.
"""
import re

_MISSING_OPERAND = re.compile(
    r"(?:状態ベクトル|波動関数|状態|式|確率振幅|係数)\s{2,}"
)
def has_missing_math_operand(sentence):
    if not isinstance(sentence, str):
        return False
    return bool(_MISSING_OPERAND.search(sentence))

def safe_evidence_sentence(sentence):
    return isinstance(sentence, str) and not has_missing_math_operand(sentence)
