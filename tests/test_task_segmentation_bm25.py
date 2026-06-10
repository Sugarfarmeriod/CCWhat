"""Tests for task_segments.bm25 and task_segments.overlap (tasks 5.1–5.5)."""

import unittest

from ccwhat.task_segments.bm25 import BM25, tokenize
from ccwhat.task_segments.overlap import (
    compute_file_weights,
    compute_overlap,
    module_weights,
    weighted_jaccard,
)


# ---------------------------------------------------------------------------
# Task 5.1 – tokenize
# ---------------------------------------------------------------------------


class TestTokenize(unittest.TestCase):
    def test_english_basic(self):
        tokens = tokenize("hello world")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)

    def test_identifier_split(self):
        # snake_case should produce both the full token and sub-parts
        tokens = tokenize("snake_case_name")
        self.assertIn("snake", tokens)
        self.assertIn("case", tokens)
        self.assertIn("name", tokens)

    def test_chinese_bigrams(self):
        tokens = tokenize("实现功能")
        # expected 2-grams
        self.assertIn("实现", tokens)
        self.assertIn("现功", tokens)
        self.assertIn("功能", tokens)

    def test_chinese_full_run(self):
        tokens = tokenize("任务分割")
        self.assertIn("任务", tokens)
        self.assertIn("务分", tokens)
        self.assertIn("分割", tokens)
        # full run should also appear
        self.assertIn("任务分割", tokens)

    def test_mixed_chinese_english(self):
        tokens = tokenize("实现 BM25 ranking")
        self.assertIn("bm25", tokens)
        self.assertIn("ranking", tokens)
        self.assertIn("实现", tokens)

    def test_file_path_tokens(self):
        tokens = tokenize("ccwhat/task_segments/bm25.py")
        # basename
        self.assertIn("bm25.py", tokens)
        # stem
        self.assertIn("bm25", tokens)
        # directory segments
        self.assertIn("ccwhat", tokens)
        self.assertIn("task_segments", tokens)

    def test_no_short_tokens(self):
        tokens = tokenize("a b cd ef")
        for tok in tokens:
            self.assertGreaterEqual(len(tok), 2, f"Short token found: {repr(tok)}")

    def test_all_lowercase(self):
        tokens = tokenize("Hello World UPPER")
        for tok in tokens:
            self.assertEqual(tok, tok.lower(), f"Non-lowercase token: {repr(tok)}")

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])


# ---------------------------------------------------------------------------
# Task 5.2 – BM25
# ---------------------------------------------------------------------------


class TestBM25(unittest.TestCase):
    def setUp(self):
        self.corpus = [
            "BM25 is a ranking function used in information retrieval",
            "Python is a general purpose programming language",
            "BM25 scoring uses term frequency and inverse document frequency",
            "Machine learning models are trained on data",
        ]
        self.bm25 = BM25(self.corpus)

    def test_relevant_doc_scores_higher(self):
        query = "BM25 ranking information retrieval"
        scores = dict(self.bm25.rank(query))
        # docs 0 and 2 are relevant; doc 1 and 3 are not
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[2], scores[3])

    def test_rank_returns_all_docs(self):
        ranked = self.bm25.rank("python")
        self.assertEqual(len(ranked), len(self.corpus))

    def test_rank_descending(self):
        ranked = self.bm25.rank("BM25")
        for i in range(len(ranked) - 1):
            self.assertGreaterEqual(ranked[i][1], ranked[i + 1][1])

    def test_score_non_negative(self):
        for i in range(len(self.corpus)):
            s = self.bm25.score("BM25 python", i)
            self.assertGreaterEqual(s, 0.0)

    def test_empty_corpus(self):
        bm25 = BM25([])
        self.assertEqual(bm25.rank("anything"), [])

    def test_exact_match_top(self):
        corpus = ["apple banana cherry", "dog cat fish", "apple orange"]
        bm25 = BM25(corpus)
        ranked = bm25.rank("apple")
        top_idx = ranked[0][0]
        self.assertIn(top_idx, {0, 2})  # both contain apple


# ---------------------------------------------------------------------------
# Task 5.3 – compute_file_weights
# ---------------------------------------------------------------------------


class TestComputeFileWeights(unittest.TestCase):
    def test_edit_weight_higher_than_read(self):
        w = compute_file_weights(
            files_read=["src/foo.py"],
            files_changed=["src/bar.py"],
        )
        self.assertGreater(w["src/bar.py"], w["src/foo.py"])

    def test_readme_downgraded(self):
        w = compute_file_weights(
            files_read=[],
            files_changed=["README.md", "src/main.py"],
        )
        self.assertLess(w["README.md"], w["src/main.py"])

    def test_lock_file_downgraded(self):
        w = compute_file_weights(
            files_read=[],
            files_changed=["uv.lock", "src/app.py"],
        )
        self.assertLess(w["uv.lock"], w["src/app.py"])

    def test_accumulation_capped(self):
        # editing the same file many times should be capped at 6.0
        files = ["src/heavy.py"] * 10
        w = compute_file_weights(files_read=[], files_changed=files)
        self.assertLessEqual(w["src/heavy.py"], 6.0)

    def test_read_accumulates(self):
        w = compute_file_weights(
            files_read=["src/foo.py", "src/foo.py"],
            files_changed=[],
        )
        # two reads: 1.0 + 1.0 = 2.0
        self.assertAlmostEqual(w["src/foo.py"], 2.0)

    def test_read_then_edit_accumulates(self):
        w = compute_file_weights(
            files_read=["src/foo.py"],
            files_changed=["src/foo.py"],
        )
        # 1.0 + 3.0 = 4.0
        self.assertAlmostEqual(w["src/foo.py"], 4.0)

    def test_custom_rules(self):
        rules = {
            "file_weights": {
                "edit_weight": 5.0,
                "read_weight": 2.0,
                "downgrade_patterns": {},
            }
        }
        w = compute_file_weights(
            files_read=["a.py"],
            files_changed=["b.py"],
            rules=rules,
        )
        self.assertAlmostEqual(w["a.py"], 2.0)
        self.assertAlmostEqual(w["b.py"], 5.0)

    def test_empty_inputs(self):
        w = compute_file_weights([], [])
        self.assertEqual(w, {})


# ---------------------------------------------------------------------------
# Task 5.4 – weighted_jaccard
# ---------------------------------------------------------------------------


class TestWeightedJaccard(unittest.TestCase):
    def test_identical_dicts_returns_one(self):
        d = {"a": 2.0, "b": 1.0}
        self.assertAlmostEqual(weighted_jaccard(d, d), 1.0)

    def test_disjoint_dicts_returns_zero(self):
        a = {"x": 3.0}
        b = {"y": 2.0}
        self.assertAlmostEqual(weighted_jaccard(a, b), 0.0)

    def test_partial_overlap(self):
        a = {"x": 2.0, "y": 1.0}
        b = {"x": 2.0, "z": 1.0}
        # intersection = min(2,2) = 2; union = max(2,2)+max(1,0)+max(0,1) = 2+1+1 = 4
        expected = 2.0 / 4.0
        self.assertAlmostEqual(weighted_jaccard(a, b), expected)

    def test_empty_dicts(self):
        self.assertAlmostEqual(weighted_jaccard({}, {}), 0.0)

    def test_one_empty(self):
        a = {"x": 1.0}
        self.assertAlmostEqual(weighted_jaccard(a, {}), 0.0)
        self.assertAlmostEqual(weighted_jaccard({}, a), 0.0)


# ---------------------------------------------------------------------------
# Task 5.4 – module_weights
# ---------------------------------------------------------------------------


class TestModuleWeights(unittest.TestCase):
    def test_aggregates_by_depth_2(self):
        fw = {
            "ccwhat/task_segments/bm25.py": 3.0,
            "ccwhat/task_segments/overlap.py": 2.0,
            "tests/test_bm25.py": 1.0,
        }
        mw = module_weights(fw, depth=2)
        self.assertAlmostEqual(mw["ccwhat/task_segments"], 5.0)
        self.assertAlmostEqual(mw["tests/test_bm25.py"], 1.0)

    def test_depth_1(self):
        fw = {
            "ccwhat/a.py": 1.0,
            "ccwhat/b.py": 2.0,
            "other/c.py": 1.0,
        }
        mw = module_weights(fw, depth=1)
        self.assertAlmostEqual(mw["ccwhat"], 3.0)
        self.assertAlmostEqual(mw["other"], 1.0)

    def test_empty(self):
        self.assertEqual(module_weights({}), {})

    def test_flat_file_no_slash(self):
        fw = {"setup.py": 1.0}
        mw = module_weights(fw, depth=2)
        self.assertIn("setup.py", mw)


# ---------------------------------------------------------------------------
# Task 5.4 – compute_overlap
# ---------------------------------------------------------------------------


class TestComputeOverlap(unittest.TestCase):
    def test_low_overlap(self):
        task_w = {
            "frontend/components/Button.tsx": 3.0,
            "frontend/styles/main.css": 1.0,
        }
        window_w = {
            "backend/api/users.py": 3.0,
            "backend/models/user.py": 2.0,
        }
        file_ov, module_ov = compute_overlap(task_w, window_w)
        self.assertLess(file_ov, 0.25)
        self.assertLess(module_ov, 0.25)

    def test_high_overlap(self):
        task_w = {
            "src/auth/login.py": 3.0,
            "src/auth/utils.py": 2.0,
        }
        window_w = {
            "src/auth/login.py": 3.0,
            "src/auth/register.py": 1.0,
        }
        file_ov, module_ov = compute_overlap(task_w, window_w)
        self.assertGreater(file_ov, 0.3)
        self.assertGreater(module_ov, 0.5)

    def test_identical_weights(self):
        w = {"src/foo.py": 3.0, "src/bar.py": 1.0}
        file_ov, module_ov = compute_overlap(w, w)
        self.assertAlmostEqual(file_ov, 1.0)
        self.assertAlmostEqual(module_ov, 1.0)

    def test_empty_weights(self):
        file_ov, module_ov = compute_overlap({}, {})
        self.assertAlmostEqual(file_ov, 0.0)
        self.assertAlmostEqual(module_ov, 0.0)

    def test_returns_tuple_of_two_floats(self):
        result = compute_overlap({"a.py": 1.0}, {"b.py": 1.0})
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        for v in result:
            self.assertIsInstance(v, float)


if __name__ == "__main__":
    unittest.main()
