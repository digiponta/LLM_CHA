"""v0.7.44.24: bounded repeated no-evidence follow-up response."""
class FollowupExhaustion:
    def __init__(self):
        self.topic = None
        self.count = 0
    def reset(self):
        self.topic = None
        self.count = 0
    def respond(self, topic):
        if not topic:
            self.reset()
            return None
        if topic != self.topic:
            self.topic, self.count = topic, 0
        self.count += 1
        if self.count == 1:
            return "取得した資料には、「{}」について追加で説明できる明確な根拠がない。".format(topic)
        return ("「{}」の追加根拠は、現在の資料からは取得できていない。"
                "知りたい観点を指定して。例えば、基本原理、数式、実験、応用のどれ？").format(topic)
