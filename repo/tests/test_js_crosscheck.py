"""The JavaScript engine shipped in app/index.html must agree with the Python reference on all 180 configurations."""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import xr_prioritization as x  # noqa: E402


class TestJsCrossCheck(unittest.TestCase):
    def test_js_equals_python(self):
        proc = subprocess.run(["node", os.path.join(HERE, "dump_js.js")], capture_output=True, text=True, check=True)
        js = json.loads(proc.stdout)
        model = x.load()
        self.assertEqual(len(js), 180)
        worst = 0.0
        for item in js:
            c = item["config"]
            py = x.prioritize(model, c["technology"], c["hardware"], c["domain"], c["activity"])
            for a, b in zip(item["scores"], py["scores"]):
                worst = max(worst, abs(a - b))
            for a, b in zip(item["wT"], py["w_t"]):
                worst = max(worst, abs(a - b))
            self.assertEqual(item["ranking"], [e["id"] for e in py["ranking"]], c)
            self.assertEqual([item["support"][d] for d in x.DIMENSIONS], [py["support"][d] for d in x.DIMENSIONS])
        self.assertLess(worst, 1e-12)


if __name__ == "__main__":
    unittest.main()
