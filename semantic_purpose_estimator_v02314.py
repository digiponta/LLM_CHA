"""v0.2.31.4: corpus-derived character n-gram semantic-similarity baseline.

No synonym substitutions, keyword-to-purpose patterns, or trained LLM_SEM
encoder. This is an honest lexical-vector proxy for the proposed
Semantic Purpose Estimator, for comparison before importing LLM_SEM.
"""
import math,re
from collections import Counter,defaultdict

EXAMPLES={
 "learning":[
  "Pythonの使い方を学ぶ","LLMについて勉強する","画像認識の仕組みを理解する",
  "文法を習得する","Pythonの基礎を覚える","ニューラルネットを学習したい",
  "LLMの基礎を教わりたい","操作方法を知りたい"],
 "development":[
  "Pythonでアプリを作る","LLMを自作する","画像認識を実装する",
  "ゲームを開発する","新しいツールを組み立てる","プログラムを書きたい",
  "AIを構築する","ソフトウェアを製作する"],
 "troubleshooting":[
  "Pythonのエラーを直す","LLMが動かない","プログラムの不具合を調べる",
  "起動できなくなった","画像認識の動作がおかしい","例外が発生する",
  "バグを解決する","故障の原因を調べたい"],
 "casual":[
  "Pythonについて雑談する","LLMでおしゃべりしたい",
  "気軽に話をしませんか","少し会話を楽しみたい",
  "最近のことを話す","話し相手になってほしい",
  "雑談したい","ちょっと話そう"],
}
def grams(text):
    normalized=re.sub(r"\s+","",text.lower())
    # Character ngrams avoid hard-coded canonical replacement rules.
    return Counter(normalized[i:i+n] for n in (2,3,4)
                   for i in range(max(0,len(normalized)-n+1)))
class SemanticPurposeEstimator:
    def __init__(self,examples=None):
        self.examples=examples or EXAMPLES
        if len(self.examples)<2:raise ValueError("need >=2 purpose classes")
        docs=[(label,text) for label,texts in self.examples.items() for text in texts]
        if not docs:raise ValueError("empty samples")
        df=Counter()
        self.entries=[]
        for label,text in docs:
            g=grams(text)
            for term in g:df[term]+=1
            self.entries.append((label,g,text))
        self.idf={term:math.log((len(docs)+1)/(count+1))+1 for term,count in df.items()}
        self.vectors=[(label,self.vector(g),text) for label,g,text in self.entries]
    def vector(self,g):
        v={term:(1+math.log(count))*self.idf.get(term,1.0)
           for term,count in g.items()}
        norm=math.sqrt(sum(w*w for w in v.values()))
        return {term:w/norm for term,w in v.items()} if norm else {}
    @staticmethod
    def dot(a,b):
        return sum(w*b.get(t,0.0) for t,w in a.items())
    def predict(self,text,threshold=0.25,margin=0.04):
        q=self.vector(grams(text))
        scores=defaultdict(float)
        neighbors=[]
        for label,v,sample in self.vectors:
            sim=self.dot(q,v)
            scores[label]=max(scores[label],sim)
            neighbors.append((sim,label,sample))
        ranked=sorted(((label,scores[label]) for label in self.examples),
                      key=lambda item:(-item[1],item[0]))
        top,score=ranked[0]
        difference=score-ranked[1][1]
        # Abstention expresses insufficient evidence; scores are cosine
        # similarity, not probabilities or calibrated confidence.
        accept=score>=threshold and difference>=margin
        return {"purpose":top if accept else None,
                "candidate":top,"similarity":score,"margin":difference,
                "accepted":accept,"scores":dict(ranked),
                "nearest":sorted(neighbors,reverse=True)[:3]}
