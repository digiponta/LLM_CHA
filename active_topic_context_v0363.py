"""v0.3.6.3 opt-in active topic admission adapter.

Makes a bounded authoritative topic index using the existing MultiTopicContext
routing interface. Never writes or validates any semantic proposition.
"""
from multi_topic_context_v0233821 import MultiTopicContext, Resolution, Topic

class ActiveTopicContext(MultiTopicContext):
    def __init__(self,max_topics=8,ttl_turns=12,pinned_topics=()):
        super().__init__(max_topics=max_topics,ttl_turns=ttl_turns)
        self.pinned=set(pinned_topics)
        if len(self.pinned)>max_topics or any(not isinstance(t,str) or not t for t in self.pinned):
            raise ValueError("invalid pins")
        self.admission_rejections=0
        self.evictions=0
        self.observations={}

    def observe(self,topic):
        if not isinstance(topic,str):
            return Resolution("MISSING")
        topic=topic.strip()
        if not topic or topic.startswith("/"):
            return Resolution("MISSING")
        self._expire()
        if topic not in self._topics and len(self._topics)>=self.max_topics:
            candidates=[t for t in self._topics if t not in self.pinned]
            if not candidates:
                self.admission_rejections+=1
                return Resolution("MISSING")
            victim=min(candidates,key=lambda t:(self.observations.get(t,0),self._topics[t].last_turn,self._topics[t].first_turn,t))
            del self._topics[victim]
            self.observations.pop(victim,None)
            self.evictions+=1
            if self.active_topic==victim:
                self.active_topic=None
        result=super().observe(topic)
        if result.status=="RESOLVED":
            self.observations[topic]=self.observations.get(topic,0)+1
        return result

    def reset(self):
        self.observations.clear()
        self.admission_rejections=0
        self.evictions=0
        return super().reset()

    def metrics(self):
        return {"mode":"active","capacity":self.max_topics,
                "topics":list(self.topics),"pins":sorted(self.pinned & set(self.topics)),
                "evictions":self.evictions,"admission_rejections":self.admission_rejections}
