"""
Unit tests for Thompson's NFA Construction.
"""

import unittest
from regex_to_dfa.parser import infix_to_postfix, EPSILON
from regex_to_dfa.nfa import build_nfa_from_postfix, thompson_literal, NFAStateFactory


class TestNFAConstruction(unittest.TestCase):

    def test_single_literal_nfa(self):
        factory = NFAStateFactory()
        nfa = thompson_literal("a", factory)
        self.assertEqual(len(nfa.states), 2)
        self.assertEqual(nfa.alphabet, {"a"})
        self.assertIn(nfa.accept_state.id, nfa.get_transitions(nfa.start_state.id, "a"))

    def test_concatenation_nfa(self):
        postfix = infix_to_postfix("ab")
        # Merged concat (Image 1 Option 1): (0) --a--> (1) --b--> (2) -> 3 states
        nfa_merged = build_nfa_from_postfix(postfix, merge_concat=True)
        self.assertEqual(len(nfa_merged.states), 3)
        self.assertEqual(nfa_merged.alphabet, {"a", "b"})

        # Unmerged concat (Image 1 Option 2): (0) --a--> (1) --eps--> (2) --b--> (3) -> 4 states
        nfa_unmerged = build_nfa_from_postfix(postfix, merge_concat=False)
        self.assertEqual(len(nfa_unmerged.states), 4)

    def test_union_nfa(self):
        postfix = infix_to_postfix("a|b")
        nfa = build_nfa_from_postfix(postfix)
        # 2 states for 'a', 2 states for 'b', + 2 new states (start, accept) = 6 states
        self.assertEqual(len(nfa.states), 6)
        self.assertEqual(nfa.alphabet, {"a", "b"})

    def test_star_nfa(self):
        postfix = infix_to_postfix("a*")
        nfa = build_nfa_from_postfix(postfix)
        # 2 states for 'a' + 2 new states (start, accept) = 4 states
        self.assertEqual(len(nfa.states), 4)
        self.assertEqual(nfa.count_epsilon_transitions(), 4)

    def test_complex_nfa(self):
        postfix = infix_to_postfix("(a|b)*abb")
        nfa = build_nfa_from_postfix(postfix)
        self.assertGreater(len(nfa.states), 0)
        self.assertEqual(nfa.alphabet, {"a", "b"})
        self.assertEqual(len(nfa.accept_states), 1)


if __name__ == "__main__":
    unittest.main()
