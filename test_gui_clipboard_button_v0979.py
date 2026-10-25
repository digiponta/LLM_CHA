"""Regression guard for the GUI clipboard button wiring (no Tk display needed)."""
import ast
import inspect
import unittest
import chat_window_v061

class ClipboardGuiButtonTests(unittest.TestCase):
    def test_button_handler_sends_existing_command(self):
        source=inspect.getsource(chat_window_v061.run)
        tree=ast.parse(source)
        handlers=[node for node in ast.walk(tree)
                  if isinstance(node,ast.FunctionDef) and node.name=="trigger_read_clipboard"]
        self.assertEqual(len(handlers),1)
        handler=handlers[0]
        calls=[node for node in ast.walk(handler) if isinstance(node,ast.Call)]
        self.assertTrue(any(isinstance(call.func,ast.Name)
                            and call.func.id=="send_to_chat"
                            and len(call.args)>=1
                            and isinstance(call.args[0],ast.Constant)
                            and call.args[0].value=="/read-clipboard"
                            for call in calls))
        self.assertIn("クリップボード読込",source)

if __name__=="__main__":
    unittest.main()
