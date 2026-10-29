import unittest
from unittest.mock import Mock
from chat_gui import ChatGUI

class GuiStreamTests(unittest.TestCase):
    def test_answer_routed_to_conversation(self):
        app=ChatGUI.__new__(ChatGUI)
        app.pending=""
        app.booted=False
        app.diagnostics=object()
        app.conversation=object()
        app.status_label=Mock()
        calls=[]
        app.add=lambda widget,text,tag=None:calls.append((widget,text,tag))
        app.process_output("boot header\nYou> AI> こんにちは。\nYou> ")
        answers=[t for widget,t,tag in calls if tag=="assistant"]
        self.assertEqual(answers,["AI: こんにちは。\n"])
        self.assertTrue(app.booted)
    def test_utf8_split_boundaries(self):
        import codecs
        decoder=codecs.getincrementaldecoder("utf-8")("replace")
        data="こんにちは".encode("utf-8")
        out=decoder.decode(data[:2])+decoder.decode(data[2:])
        self.assertEqual(out,"こんにちは")
if __name__=="__main__":
    unittest.main()
