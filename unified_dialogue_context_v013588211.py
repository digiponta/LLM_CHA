"""Session-only multi-topic dialogue context; never persists user preferences."""
import re
from dataclasses import dataclass, field

@dataclass
class UnifiedDialogueContext:
    active_topic: str = ""
    previous_topics: list = field(default_factory=list)
    last_experience: str = ""
    def switch(self, topic):
        topic=(topic or "").strip()
        if not topic:return self.active_topic
        if topic != self.active_topic:
            if self.active_topic:
                self.previous_topics=[t for t in self.previous_topics if t!=self.active_topic]
                self.previous_topics.append(self.active_topic)
                self.previous_topics=self.previous_topics[-8:]
            self.active_topic=topic
        return self.active_topic
    def resolve(self, utterance):
        text=(utterance or "").strip()
        if re.search(r"(?:さっき|先ほど|前に).{0,10}(?:宝石|石)",text):
            for topic in reversed(self.previous_topics):
                if topic in ("スファレライト","閃亜鉛鉱"):
                    return topic
        if re.search(r"(?:さっき|先ほど|前の)(?:話題|話)",text) and self.previous_topics:
            return self.previous_topics[-1]
        return None
