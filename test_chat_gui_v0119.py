import unittest
from pathlib import Path
from chat_gui_v0119 import CHOICES, launch_command

class GUIContractTests(unittest.TestCase):
    def test_command_uses_local_chat_py(self):
        command=launch_command()
        self.assertEqual(Path(command[-1]).name,"chat.py")
        self.assertTrue(Path(command[-1]).is_file())
    def test_reconciliation_buttons(self):
        self.assertEqual(set(CHOICES),{"prefer_a","prefer_b","both_contextual","neither","skip"})

if __name__=="__main__": unittest.main()
