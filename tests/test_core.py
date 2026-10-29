import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from abstract_checker.cli import extract_abstract, main
from abstract_checker.core import check_abstract, classify_sentence, split_sentences

GOOD = ("Antibiotic resistance is a growing threat, however little is known about its spread in rural clinics. "
        "We aimed to estimate resistance prevalence in 12 rural clinics. "
        "We collected 1,204 samples and used logistic regression to identify risk factors. "
        "Resistance was found in 23.5% of samples and prior antibiotic use increased risk (odds ratio 2.1, p < 0.001). "
        "These findings suggest that stewardship programmes should target rural settings.")
WEAK = "Deep learning is popular [1]. We propose a new model, shown in Fig. 2. It is good."


class SentenceTests(unittest.TestCase):
    def test_split_keeps_decimals_and_abbreviations(self):
        self.assertEqual(len(split_sentences("Values were 3.5 vs. 2.1, e.g. high. Smith et al. agree.")), 2)

    def test_classify(self):
        self.assertEqual(classify_sentence("We found a 20% reduction (p < 0.01).", 0.7)[0], "results")
        self.assertEqual(classify_sentence("We recruited 300 patients in a randomized trial.", 0.4)[0], "methods")
        self.assertEqual(classify_sentence("In conclusion, these findings suggest new policies.", 1)[0], "conclusion")


class CheckTests(unittest.TestCase):
    def test_good_abstract_has_no_warnings(self):
        res = check_abstract(GOOD)
        self.assertEqual(res["components"], ["background", "objective", "methods", "results", "conclusion"])
        self.assertEqual([i for i in res["issues"] if i[0] != "info"], [])

    def test_weak_abstract_issues(self):
        codes = {i[1] for i in check_abstract(WEAK)["issues"]}
        self.assertTrue({"citation", "figure-ref", "missing-methods", "missing-results", "missing-conclusion"} <= codes)

    def test_word_limit(self):
        self.assertIn("over-limit", {i[1] for i in check_abstract(GOOD, word_limit=20)["issues"]})

    def test_structured_headings(self):
        res = check_abstract("Background: X. Methods: Y. Results: Z. Conclusions: W.")
        self.assertEqual(res["structured_headings"], ["background", "methods", "results", "conclusion"])

    def test_extract_and_cli(self):
        tex = "\\begin{abstract}\n" + GOOD.replace("%", "\\%") + " % private\n\\end{abstract}\n\\section{Intro} Long text."
        self.assertNotIn("Intro", extract_abstract(tex))
        self.assertNotIn("private", extract_abstract(tex))
        self.assertIn("23.5%", extract_abstract(tex))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "paper.tex")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(tex)
            with redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(main([p, "--show"]), 0)
            self.assertIn("[results   ]", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
