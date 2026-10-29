"""Session-only general sensory impression context; no implicit knowledge claims."""
import re

QUESTION = re.compile(r"[？?]|(?:とは|の意味|の語源|について|教えて|説明して)")
SENSES = (
 ("vision", re.compile(r"^(黄色|赤|青|緑|きらきら|キラキラ|きれい|綺麗|美しい)(?:です|だ|だった|ね)?[。！!]*$")),
 ("smell", re.compile(r"^(いい香り|良い香り|香ばしい|香りがいい|いい匂い|良い匂い)(?:です|だ|だった|ね)?[。！!]*$")),
 ("hearing", re.compile(r"^(いい音|良い音|心地よい音|きれいな音|うるさい|騒がしい|静か)(?:です|だ|だった|ね)?[。！!]*$")),
 ("emotion_joy", re.compile(r"^(嬉しい|うれしい|楽しい|幸せ|喜んだ|わくわく|感動した)(?:です|だ|だった|ね)?[。！!]*$")),
 ("emotion_anger", re.compile(r"^(怒った|腹が立つ|むかつく|イライラする|悔しい)(?:です|だ|だった|ね)?[。！!]*$")),
 ("emotion_sadness", re.compile(r"^(悲しい|寂しい|さみしい|がっかり|落ち込んだ)(?:です|だ|だった|ね)?[。！!]*$")),
 ("emotion_pleasure", re.compile(r"^(楽しかった|気持ちいい|心地よい|安心した|ほっとした)(?:です|だ|だった|ね)?[。！!]*$")),
 ("touch", re.compile(r"^(柔らかい|やわらかい|ふわふわ|もちもち|なめらか|滑らか)(?:です|だ|だった|ね)?[。！!]*$")),
 ("taste", re.compile(r"^(美味|美味しい|おいしい|うまい|旨い|最高|さっぱり|あっさり|甘い|酸っぱい|苦い)(?:です|だ|だった|ね)?[。！!]*$")),
 ("satisfaction", re.compile(r"^(満足|大満足|気に入った|よかった|良かった)(?:です|だ|だった|した|ね)?[。！!]*$")),
)
PROMPT_SENSE = (
 ("taste",re.compile(r"どんな味だった[？?]|味はどうだった[？?]|味は[？?]")),
 ("smell",re.compile(r"どんな香り|香りはどう|匂いはどう")),
 ("vision",re.compile(r"どんな色|色はどう|見た目はどう|どんな輝き")),
 ("touch",re.compile(r"食感はどう|どんな食感|触り心地はどう|手触りはどう")),
 ("hearing",re.compile(r"どんな音|音はどう|聞こえ方|響きはどう")),
 ("emotion",re.compile(r"どんな気持ち|どう感じた|気分はどう|どう思った")),
 ("satisfaction",re.compile(r"満足した[？?]|気に入った[？?]|どうだった[？?]")),
)
class GeneralDialogueIntentContext:
 def __init__(self):
  self.expected=None
  self.subject=""
  self.topic=""
 def observe(self,reply,subject="",topic=""):
  self.expected=next((name for name,pattern in PROMPT_SENSE if pattern.search(reply or "")),None)
  self.subject=subject or self.subject
  self.topic=topic or self.topic
 def clear(self):
  self.expected=None
  self.subject=""
  self.topic=""
 def respond(self,utterance,topic=""):
  s=(utterance or "").strip()
  if not s or QUESTION.search(s):
   self.expected=None
   return None
  if topic and self.topic and topic!=self.topic:
   self.expected=None
   return None
  found=next(((sense,m.group(1)) for sense,pattern in SENSES if (m:=pattern.fullmatch(s))),None)
  if not found:
   self.expected=None
   return None
  sense,value=found
  # Short impressions require a recent assistant question, except a self-evident
  # satisfaction statement that can stand alone in the active conversation.
  if not self.expected and sense not in ("satisfaction","emotion_joy","emotion_anger","emotion_sadness","emotion_pleasure"):
   return None
  if self.expected and sense not in (self.expected,"satisfaction") and not (self.expected=="emotion" and sense.startswith("emotion_")):
   return None
  subject=self.subject
  self.expected=None
  if sense=="taste":
   return f"{subject+'は' if subject else ''}おいしかったんだね。気に入ったようでよかった。" if value in ("美味","美味しい","おいしい","うまい","旨い","最高") else f"{value}と感じたんだね。"
  if sense=="smell":
   return f"{subject+'は' if subject else ''}香りがよかったんだね。"
  if sense=="vision":
   return f"{subject+'は' if subject else ''}{value}ところが印象に残ったんだね。" if value not in ("黄色","赤","青","緑") else f"{subject+'は' if subject else ''}{value}が印象に残ったんだね。"
  if sense=="hearing":
   return f"{value}と感じたんだね。"
  if sense=="emotion_joy":
   return "嬉しい気持ちになったんだね。"
  if sense=="emotion_anger":
   return "腹が立ったんだね。何があったの？"
  if sense=="emotion_sadness":
   return "悲しい気持ちなんだね。話したければ聞くよ。"
  if sense=="emotion_pleasure":
   return "心地よく感じたんだね。"
  if sense=="touch":
   return f"{subject+'は' if subject else ''}{value}と感じたんだね。"
  return "満足できたんだね。気に入ったようでよかった。"
