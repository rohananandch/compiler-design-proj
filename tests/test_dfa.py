"""
Unit tests for Subset Construction (Powerset DFA) and Hopcroft Minimization.
"""

import unittest
from regex_to_dfa.parser import infix_to_postfix
from regex_to_dfa.nfa import build_nfa_from_postfix
from regex_to_dfa.dfa import nfa_to_dfa, compute_epsilon_closure
from regex_to_dfa.minimizer import minimize_dfa_hopcroft


class TestDFAAndMinimizer(unittest.TestCase):

    def test_dfa_subset_construction(self):
        postfix = infix_to_postfix("(a|b)*abb")
        nfa = build_nfa_from_postfix(postfix)
        dfa = nfa_to_dfa(nfa)

        # Standard DFA for (a|b)*abb has 5 states
        self.assertEqual(len(dfa.states), 5)
        self.assertEqual(dfa.alphabet, ["a", "b"])
        # Exactly one accept state (D4)
        self.assertEqual(len(dfa.accept_states), 1)

    def test_hopcroft_minimization(self):
        postfix = infix_to_postfix("(a|b)*abb")
        nfa = build_nfa_from_postfix(postfix)
        dfa = nfa_to_dfa(nfa)
        min_dfa = minimize_dfa_hopcroft(dfa)

        # Minimal DFA for (a|b)*abb has exactly 4 states
        self.assertEqual(len(min_dfa.states), 4)
        self.assertEqual(len(min_dfa.accept_states), 1)
        # States D0 and D2 merged into M0
        self.assertIn("M0", min_dfa.partition_mapping)
        self.assertEqual(sorted(min_dfa.partition_mapping["M0"]), ["D0", "D2"])

    def test_already_minimal_dfa(self):
        # 'a|b' produces 3 DFA states: start, accept on a/b, dead
        postfix = infix_to_postfix("a|b")
        nfa = build_nfa_from_postfix(postfix)
        dfa = nfa_to_dfa(nfa)
        min_dfa = minimize_dfa_hopcroft(dfa)
        self.assertLessEqual(len(min_dfa.states), len(dfa.states))


if __name__ == "__main__":
    unittest.main()
