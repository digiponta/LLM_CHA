"""Explicit and conservative normalization of episodic observations."""
import re

RULES = (
 ("smell","香り",r"香り|匂い",((r"良かっ|よかっ|いい|良い","positive"),(r"悪い|嫌|臭い","negative"))),
 ("taste","苦味",r"苦かっ|苦い",((r"苦","negative"),)),
 ("taste","甘味",r"甘み|甘味|甘い",((r"良い|良かっ|よかっ|美味","positive"),)),
 ("taste","酸味",r"酸味|酸っぱ",((r"良い|良かっ|よかっ|美味","positive"),)),
 ("taste","美味しさ",r"美味|おいし|旨い",((r"美味|おいし|旨い","positive"),)),
 ("vision","色",r"黄色|赤色|青色|緑色",((r"好き|きれい|綺麗","positive"),)),
 ("emotion","満足",r"満足",((r"不満足|満足できな","negative"),(r"満足","positive"))),
 ("preference","好み",r"好き|気に入",((r"好きじゃない|嫌い","negative"),(r"好き|気に入","positive"))),
)
def normalize_observation(clause):
    result=[]
    for sense,attribute,pattern,polarity_rules in RULES:
        if not re.search(pattern,clause):
            continue
        polarity=next((label for p,label in polarity_rules if re.search(p,clause)),"neutral")
        if re.search(r"少し苦",clause):
            value="少し苦い"
        elif attribute=="香り" and polarity=="positive":
            value="良い"
        elif attribute=="満足":
            value="満足" if polarity=="positive" else "不満足"
        else:
            value=clause
        result.append({"dimension":sense,"attribute":attribute,"value":value,
                       "polarity":polarity,"source":"USER_SELF_REPORTED"})
    return result
