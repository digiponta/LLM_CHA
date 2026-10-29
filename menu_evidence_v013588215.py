"""Evidence-grounded menu category and exhaustive-in-source item listing.

Never claims to enumerate an entire vendor catalogue: only the complete set
extractable from the currently loaded, potentially truncated evidence records.
"""
import re

DRINK=re.compile(r"フラペチーノ|コーヒー|エスプレッソ|ラテ|カプチーノ|ティー|フラットホワイト|マキアート|ドリンク|抹茶|フルーツジュース|レモネード|チャイ|フロート")
FOOD=re.compile(r"サンド|バゲット|ベーグル|マフィン|スコーン|ケーキ|ドーナツ|クッキー|ペストリー|キッシュ|ラップサンド|クロワッサン|サラダ|デニッシュ|フード|パン|ブラウニー|フィローネ|チョコレートチャンク")
NOISE=re.compile(r"^(?:https?://|www\.|Read more|画像|ニュース|検索|ウェブ|すべて|他の人はこちらも検索|AI Mode|スポンサー|広告|Shopping|Images|Videos|More|Skip to|カート|ログイン|アカウント|詳細を見る|商品一覧|店舗検索|お問い合わせ)\b",re.I)
MENU_WORDS=re.compile(r"メニュー|フード|食べ物|飲み物|ドリンク|商品の種類|商品一覧")
DRINK_QUERY=re.compile(r"ドリンク|飲み物|飲料|コーヒーの種類")
FOOD_QUERY=re.compile(r"フード|食べ物|食事|軽食|パンの種類")
CURRENCY=re.compile(r"^[¥￥]?\s*[\d,]+\s*円?$")
CATEGORY_HEADS={
 "ドリンク":re.compile(r"^(?:ドリンク|飲み物|ビバレッジ|BEVERAGE|DRINKS)(?:メニュー|一覧|商品)?$",re.I),
 "フード":re.compile(r"^(?:フード|食べ物|FOOD)(?:メニュー|一覧|商品)?$",re.I),
}
def query_kind(question):
 q=(question or "").strip()
 if not MENU_WORDS.search(q):return None
 if FOOD_QUERY.search(q):return "フード"
 if DRINK_QUERY.search(q):return "ドリンク"
 return "メニュー"

def clean_line(raw):
 x=re.sub(r"^[\s•・●▪★☆*+\-]+","",raw.strip())
 x=x.replace("\u3000"," ").strip()
 # Distinguish product name from prices/navigation after pipe/tab.
 x=re.split(r"\s*[|｜]\s*|\t",x,maxsplit=1)[0].strip()
 return x

def product_type(line):
 d=bool(DRINK.search(line));f=bool(FOOD.search(line))
 # Named food product wins over drink ingredient words, e.g. coffee-flavoured cake.
 if f and re.search(r"ケーキ|サンド|バゲット|マフィン|スコーン|ドーナツ|クッキー|パン|クロワッサン|ペストリー|ベーグル|キッシュ|サラダ|デニッシュ|ブラウニー|フィローネ|ラップ",line):
  return "フード"
 if d:return "ドリンク"
 if f:return "フード"
 return None

def extract_menu(records,topic):
 sections={"ドリンク":[],"フード":[]}
 categories=set()
 # Oldest to newest so the source order is preserved.
 for rec in records:
  if rec.get("topic")!=topic:continue
  context=None
  for raw in rec.get("text","").splitlines():
   line=clean_line(raw)
   if not line or len(line)>110 or NOISE.search(line) or CURRENCY.fullmatch(line):
    continue
   head=next((key for key,p in CATEGORY_HEADS.items() if p.fullmatch(line)),None)
   if head:
    context=head;categories.add(head)
    continue
   if re.fullmatch(r"メニュー|商品|商品一覧|店舗|新商品|季節限定|おすすめ",line):
    context=None;continue
   # Avoid long descriptive snippets and standalone section labels as products.
   if len(line)<4 or re.search(r"[。！？?]",line) or re.search(r"^(?:メニュー|商品の一覧|詳しくはこちら|公式サイト)",line):
    continue
   kind=product_type(line)
   if not kind and context and 4<=len(line)<=70 and not re.match(r"^\d",line):
    # Section-scoped named items may not repeat category keywords.
    kind=context
   if kind and line not in sections[kind]:
    # Unrelated category navigation is not a product.
    if line in ("フードメニュー","ドリンクメニュー"):continue
    sections[kind].append(line)
    categories.add(kind)
 return categories,sections

def retrieve_menu(store,question):
 kind=query_kind(question)
 if kind is None or not store.topic:return None
 records=[r for r in store.records if r.get("topic")==store.topic]
 if not records:
  return {"status":"NO_EVIDENCE","topic":store.topic}
 categories,sections=extract_menu(records,store.topic)
 if not categories:
  return {"status":"NO_MATCH","topic":store.topic}
 sources=list(dict.fromkeys(r.get("source","unknown") for r in records))
 return {"status":"MENU","topic":store.topic,"kind":kind,
         "categories":[c for c in ("ドリンク","フード") if c in categories],
         "items":sections,"source":", ".join(sources),"truth_state":"EXTERNAL_UNVERIFIED"}

def format_menu(result):
 if result["status"]!="MENU":return None
 topic=result["topic"];kind=result["kind"]
 prefix=f"【外部未検証資料：{result['source']}】"
 if kind=="メニュー":
  cats="、".join(result["categories"])
  return f"{prefix}{topic}のメニューには、読み込んだ資料から{cats}が確認できます。各商品の一覧は「ドリンクの種類」「フードの種類」で表示できます。"
 items=result["items"][kind]
 if not items:
  return f"{prefix}{topic}の{kind}商品名は、読み込んだ資料から確認できません。"
 return (f"{prefix}{topic}の{kind}（読み込んだ資料から抽出した全{len(items)}件）:\n"+
         "\n".join(f"  ・{x}" for x in items)+
         "\n※検索結果の抜粋に含まれる全件です。店舗の全商品を保証するものではありません。")
