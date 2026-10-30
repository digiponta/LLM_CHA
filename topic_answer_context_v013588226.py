"""Bounded per-topic answer context, explicit returns and safe elaboration.

Keeps previous runtime answers as *reported text*, not verified factual truth.
No automatic semantic promotion, model training or persistent private storage.
"""
import re
from dataclasses import dataclass
from collections import OrderedDict

UNKNOWN=re.compile(r"未学習|検索結果がありません|資料がありません|確認できません")
BAD=re.compile(r"^.{0,12}(?:無用反面|知能。)$")
RETURN=re.compile(r"^(.{1,80}?)(?:の話|の話題|について)(?:に)?戻(?:って|りたい|ろう|れますか)[。！？!?]*$")
MORE=re.compile(r"^(?:もう少し|もっと|さらに)(?:詳しく|詳しく説明して|説明して|教えて)[。！？!?]*$")
TOPIC=re.compile(r"^(.{1,60}?)(?:とは|について(?:教えて|説明して)?)[。！？!?]*$")
GENERIC={"それ","これ","さっき","先ほど","前","今"}
@dataclass
class AnswerRecord:
 topic:str
 question:str
 answer:str
 source:str
 status:str="ANSWERED"

class TopicAnswerContext:
 def __init__(self,capacity=12):
  self.capacity=capacity
  self.history=OrderedDict()
  self.active=None
  self.returned_topic=None
 def topic_of(self,question):
  q=(question or "").strip()
  match=TOPIC.fullmatch(q)
  if match:return match.group(1).strip()
  if len(q)<=30 and re.fullmatch(r"[\w\u3040-\u30ff\u3400-\u9fffー・]+",q):
   return q
  return None
 def note_question(self,question):
  topic=self.topic_of(question)
  if topic:self.active=topic;self.returned_topic=None
  return topic
 def record(self,question,answer,source="LLM_RUNTIME"):
  if not answer or UNKNOWN.search(answer) or BAD.search(answer):return False
  topic=self.topic_of(question) or self.active
  if not topic:return False
  item=AnswerRecord(topic,question,answer,source)
  self.history.pop(topic,None)
  self.history[topic]=item
  while len(self.history)>self.capacity:self.history.popitem(last=False)
  self.active=topic
  return True
 def navigate(self,text):
  q=(text or "").strip()
  m=RETURN.fullmatch(q)
  if m:
   topic=m.group(1).strip()
   if topic in GENERIC:return None
   if topic not in self.history:
    return ("TOPIC_NOT_RECORDED",topic,"「"+topic+"」について、参照できる以前の回答はありません。")
   self.active=topic;self.returned_topic=topic
   rec=self.history[topic]
   # Extracting a previous response does not endorse unsupported claims.
   excerpt=rec.answer[:180].rstrip(" /、。 ")
   return ("RETURNED",topic,"「"+topic+"」の話に戻るね。先ほどの回答は「"+excerpt+"」だったよ。これは以前の応答の再掲で、内容の検証を意味しないよ。")
  if MORE.fullmatch(q):
   if not self.active or self.active not in self.history:
    return ("NO_CONTEXT",None,"何について詳しく知りたいか、話題を指定してね。")
   rec=self.history[self.active]
   return ("ELABORATE",rec.topic,None)
  return None
 def elaborate(self,topic):
  rec=self.history.get(topic)
  if not rec:return "その話題の以前の回答を参照できません。"
  # A safe, grounded prompt for the existing LLM: no implicit factual promotion.
  first=re.split(r"[。／/]",rec.answer,maxsplit=1)[0].strip()[:180]
  return ("「"+topic+"」について、先ほどは「"+first+"」と説明したよ。"
          " これは前回の回答内容を参照したもので、科学的な正しさを保証しない。"
          " 詳しい説明には根拠の確認が必要だから、基本原理・観測結果・仮説のどれを知りたいか教えてね。")
