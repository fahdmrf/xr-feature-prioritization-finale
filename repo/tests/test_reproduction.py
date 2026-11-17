"""Reproduction tests: the repository data must reproduce the figures reported in the article."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import xr_prioritization as x  # noqa: E402

MODEL = x.load()

# Top-10 shown by the prioritization tool in the article for VR / VR HMD only / Production / Assembly
ARTICLE_TOP10 = [
    ("EF14", 0.0647), ("EF17", 0.0613), ("EF23", 0.0476), ("EF25", 0.0409), ("EF22", 0.0409),
    ("EF2", 0.0407), ("EF9", 0.0400), ("EF21", 0.0397), ("EF3", 0.0372), ("EF27", 0.0367),
]


class TestData(unittest.TestCase):
    def test_dimensions_of_data(self):
        self.assertEqual(len(MODEL["crs"]), 37)
        self.assertEqual(len(MODEL["efs"]), 33)
        self.assertEqual(len(MODEL["studies"]), 55)
        self.assertEqual(sum(1 for r in MODEL["R"] for v in r if v > 0), 355)
        self.assertTrue(all(0 <= v <= 5 for r in MODEL["R"] for v in r))
        self.assertTrue(all(sum(r) > 0 for r in MODEL["R"]))

    def test_parameters(self):
        p = MODEL["params"]
        self.assertEqual(p["alpha"], 0.1462)
        self.assertEqual(len(p["beta"]), 4)
        self.assertAlmostEqual(sum(p["beta"].values()), 1.0, places=5)
        self.assertAlmostEqual(sum(MODEL["w_indus"]), 1.0, delta=3e-4)  # Table B1 is rounded to 4 decimals

    def test_study_support(self):
        n = lambda d, m: x.modality_weights(MODEL, d, m)[1]
        self.assertEqual((n("xr_technology", "AR"), n("xr_technology", "VR")), (31, 16))
        self.assertEqual([n("application_domain", d) for d in x.DOMAINS], [9, 37, 9])
        self.assertEqual(n("industrial_activity", "Assembly"), 17)
        self.assertEqual(n("hardware_configuration", "VR HMD only"), 7)
        self.assertEqual(n("hardware_configuration", "AR HMD only"), 15)

    def test_modality_weights_sum_to_one(self):
        for dim, mods in (("xr_technology", x.XR_TECHNOLOGIES), ("application_domain", x.DOMAINS),
                          ("industrial_activity", x.ACTIVITIES)):
            for m in mods:
                self.assertAlmostEqual(sum(x.modality_weights(MODEL, dim, m)[0]), 1.0, places=12)


class TestExample(unittest.TestCase):
    def setUp(self):
        self.res = x.prioritize(MODEL, "VR", "VR HMD only", "Production", "Assembly")

    def test_ranking_matches_article(self):
        got = [e["id"] for e in self.res["ranking"][:10]]
        self.assertEqual(got, [e for e, _ in ARTICLE_TOP10])

    def test_scores_match_article_within_rounding(self):
        # the tool reports 4 decimals computed from unrounded inputs; Table B1 weights are rounded
        for entry, (ef, value) in zip(self.res["ranking"], ARTICLE_TOP10):
            self.assertAlmostEqual(entry["score"], value, delta=1.5e-4, msg=ef)

    def test_scores_sum_to_one(self):
        self.assertAlmostEqual(sum(self.res["scores"]), 1.0, places=12)

    def test_cr_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(self.res["w_t"]), 1.0, delta=3e-4)

    def test_top_cr_weights(self):
        w = self.res["w_t"]
        top = sorted(range(37), key=lambda i: -w[i])[:5]
        self.assertEqual([MODEL["crs"][i]["id"] for i in top], ["CR13", "CR26", "CR25", "CR28", "CR29"])
        self.assertEqual([round(w[i], 3) for i in top], [0.070, 0.068, 0.062, 0.058, 0.055])


class TestAllConfigurations(unittest.TestCase):
    def test_properties_over_all_configurations(self):
        configs = x.valid_configurations()
        self.assertEqual(len(configs), 180)
        for c in configs:
            r = x.prioritize(MODEL, *c)
            top10 = [e["id"] for e in r["ranking"][:10]]
            self.assertAlmostEqual(sum(r["scores"]), 1.0, places=12)
            self.assertIn("EF14", top10)       # reported in the article: EF14 in the model Top-10 in every configuration
            self.assertNotIn("EF32", top10)    # reported in the article: EF32 never in the model Top-10


if __name__ == "__main__":
    unittest.main()
