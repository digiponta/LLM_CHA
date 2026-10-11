import subprocess,sys,unittest
from chat_runtime_benchmark_v023377 import child_environment

class WindowsUtf8SubprocessTests(unittest.TestCase):
    def test_utf8_environment(self):
        env=child_environment()
        self.assertEqual(env["PYTHONUTF8"],"1")
        self.assertEqual(env["PYTHONIOENCODING"],"utf-8")
    def test_japanese_roundtrip(self):
        sample="こんにちは、宇宙について教えて"
        program="import sys; s=sys.stdin.readline().rstrip('\\n'); print(s); print(len(s))"
        p=subprocess.run([sys.executable,"-c",program],input=sample+"\n",
            capture_output=True,text=True,encoding="utf-8",errors="strict",
            env=child_environment(),check=True)
        self.assertEqual(p.stdout.splitlines()[0],sample)
        self.assertEqual(int(p.stdout.splitlines()[1]),len(sample))
    def test_surrogate_is_not_introduced(self):
        sample="量子力学とは\n"
        p=subprocess.run([sys.executable,"-c","import sys;print(repr(sys.stdin.readline()))"],
            input=sample,text=True,capture_output=True,encoding="utf-8",errors="strict",
            env=child_environment(),check=True)
        self.assertNotIn("surrogate",p.stdout.lower())
        self.assertEqual(p.returncode,0)
if __name__=="__main__":unittest.main()
