"""
End-to-End Pipeline & Ground Truth Verification Tests.
Compares automaton simulation decisions against Python's native `re` module.
"""

import unittest
import re
from regex_to_dfa.visualizer import run_pipeline
from regex_to_dfa.simulator import AutomatonSimulator


class TestPipelineGroundTruth(unittest.TestCase):

    def _verify_regex_equivalence(self, regex_str: str, python_pattern: str, test_strings: list):
        """Helper to verify our automaton matches Python's re module on all test strings."""
        pipeline_res = run_pipeline(regex_str)
        py_compiled = re.compile(f"^{python_pattern}$")

        for s in test_strings:
            expected_accept = bool(py_compiled.match(s))
            sim_res = AutomatonSimulator.test_string(
                s,
                pipeline_res.nfa,
                pipeline_res.dfa,
                pipeline_res.min_dfa
            )

            # Check all automata agreed
            self.assertTrue(
                sim_res["equivalent_across_all"],
                f"Mismatch among NFA/DFA/MinDFA for regex '{regex_str}' on input '{s}'"
            )
            # Check match against python re ground truth
            self.assertEqual(
                sim_res["accepted"],
                expected_accept,
                f"Ground truth discrepancy for regex '{regex_str}' on input '{s}'. "
                f"Got {sim_res['accepted']}, expected {expected_accept}"
            )

    def test_ends_with_abb(self):
        tests = ["abb", "aabb", "babb", "ababb", "bbabb", "", "a", "b", "ab", "ba", "abba", "abbb"]
        self._verify_regex_equivalence("(a|b)*abb", "(a|b)*abb", tests)

    def test_second_to_last_is_a(self):
        tests = ["aa", "ab", "aaa", "aab", "baa", "bab", "bba", "bbb", "", "a", "b", "baaa"]
        self._verify_regex_equivalence("(a|b)*a(a|b)", "(a|b)*a[ab]", tests)

    def test_binary_contains_00(self):
        tests = ["00", "100", "001", "1001", "010010", "010101", "111", "0", "1", ""]
        self._verify_regex_equivalence("(0|1)*00(0|1)*", "[01]*00[01]*", tests)

    def test_prefix_with_alternatives(self):
        tests = ["a", "ab", "ac", "abbc", "acbb", "b", "c", ""]
        self._verify_regex_equivalence("a(b|c)*", "a[bc]*", tests)

    def test_efficiency_metrics_sanity(self):
        res = run_pipeline("(a|b)*abb")
        m = res.metrics
        # Min DFA states <= DFA states <= NFA states
        self.assertLessEqual(m.min_dfa_states, m.dfa_states)
        self.assertLessEqual(m.dfa_states, m.nfa_states)
        # Reduction percentage should be positive
        self.assertGreater(m.nfa_to_min_dfa_total_reduction_pct, 0)
        self.assertGreaterEqual(m.dfa_to_min_dfa_state_reduction_pct, 0)


if __name__ == "__main__":
    unittest.main()
