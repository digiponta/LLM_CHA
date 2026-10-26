"""Run from LLM_CHA repo root: python -m unittest -v test_chat_gui_multiturn_v0130.py

Data-driven headless replay of GUI conversation turns. No network or CUDA needed.
"""
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from chat_gui_v0119 import ChatGUI

DATA = Path(__file__).parent / 'data' / 'gui_multiturn_regression_v0130.json'


class GUIMultiturnRegression(TestCase):
    def test_scenarios(self):
        examples = json.loads(DATA.read_text(encoding='utf-8'))['scenarios']
        for scenario in examples:
            with self.subTest(scenario=scenario['id']):
                gui = ChatGUI.__new__(ChatGUI)
                gui.entry = Mock()
                gui._append = Mock()
                gui.submit = Mock()
                gui.clipboard_context = scenario['clipboard_text']
                gui.last_clipboard_source = scenario['clipboard_text']
                gui.active_food_item = ''
                gui.active_preference_topic = ''
                for index, turn in enumerate(scenario['turns']):
                    with self.subTest(index=index, utterance=turn['input']):
                        gui.entry.get.return_value = turn['input']
                        old_count = gui._append.call_count
                        gui.send()
                        self.assertEqual(gui._append.call_count, old_count + 1)
                        response = gui._append.call_args.args[0]
                        self.assertIn(turn['expected_contains'], response)
                        self.assertNotIn('資料のどの部分について知りたいですか', response)
                        self.assertEqual(gui.last_clipboard_source, scenario['clipboard_text'])
                gui.submit.assert_not_called()
