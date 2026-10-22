import unittest
from menu_intent_v0619 import menu_request,menu_answer
class MenuIntentTests(unittest.TestCase):
    def test_direct_menu(self):
        self.assertEqual(menu_request("スターバックスのメニュー")["status"],"FOUND")
    def test_ambiguous_name(self):
        self.assertEqual(menu_request("スターバックのメニュー")["status"],"AMBIGUOUS")
    def test_followup(self):
        self.assertEqual(menu_request("メニュー","スターバックス")["topic"],"スターバックス")
    def test_no_context(self):
        self.assertIsNone(menu_request("メニュー"))
    def test_identity_not_intercepted(self):
        self.assertIsNone(menu_request("長門"))
    def test_no_fabricated_products(self):
        self.assertIn("公式メニュー",menu_answer(menu_request("スターバックスのメニュー")))
if __name__=="__main__":unittest.main()
