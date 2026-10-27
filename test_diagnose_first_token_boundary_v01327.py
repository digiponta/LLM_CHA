import unittest
from diagnose_first_token_boundary_v01327 import inspect_boundary

class BoundaryDiagnosticsTests(unittest.TestCase):
    def test_function_exists(self):
        self.assertTrue(callable(inspect_boundary))
    def test_no_mutation_expected(self):
        import inspect
        sig=inspect.signature(inspect_boundary)
        self.assertEqual(list(sig.parameters)[:4],["model","tokenizer","question","answer"])

if __name__=="__main__":unittest.main()
