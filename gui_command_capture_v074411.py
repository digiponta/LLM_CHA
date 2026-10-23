"""Capture multiline slash-command output until the next CLI prompt."""
class CommandOutputCapture:
    def __init__(self, max_chars=50000):
        self.max_chars = max_chars
        self.active = False
        self.buffer = ""
    def start(self):
        self.buffer = ""
        self.active = True
    def feed(self, char):
        if not self.active:
            return None
        self.buffer += char
        marker = self.buffer.find("You> ")
        if marker >= 0:
            result = self.buffer[:marker].strip()
            self.active = False
            self.buffer = ""
            return result
        if len(self.buffer) > self.max_chars:
            result = self.buffer[:self.max_chars] + "\n[output truncated]"
            self.active = False
            self.buffer = ""
            return result
        return None
