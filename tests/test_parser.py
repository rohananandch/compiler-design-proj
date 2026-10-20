"""
Unit tests for Regex Parser & Shunting-Yard Infix to Postfix Converter.
"""

import unittest
from regex_to_dfa.parser import (
    infix_to_postfix,
    insert_explicit_concatenations,
    validate_syntax,
    extract_alphabet,
    RegexParseError,
    EPSILON
)


class TestRegexParser(unittest.TestCase):

    def test_explicit_concatenation(self):
        self.assertEqual(insert_explicit_concatenations("ab"), "a.b")
        self.assertEqual(insert_explicit_concatenations("a(b|c)"), "a.(b|c)")
        self.assertEqual(insert_explicit_concatenations("(a|b)c"), "(a|b).c")
        self.assertEqual(insert_explicit_concatenations("a*b"), "a*.b")
        self.assertEqual(insert_explicit_concatenations("(a|b)*abb"), "(a|b)*.a.b.b")

    def test_infix_to_postfix_basic(self):
        self.assertEqual(infix_to_postfix("ab"), "ab.")
        self.assertEqual(infix_to_postfix("a|b"), "ab|")
        self.assertEqual(infix_to_postfix("a*"), "a*")
        self.assertEqual(infix_to_postfix("(a|b)*abb"), "ab|*a.b.b.")
        self.assertEqual(infix_to_postfix("a(b|c)*"), "abc|*.")

    def test_operator_precedence(self):
        # Kleene star binds tighter than concatenation, which binds tighter than union
        self.assertEqual(infix_to_postfix("ab*|c"), "ab*.c|")
        self.assertEqual(infix_to_postfix("a|b*c"), "ab*c.|")

    def test_extended_operators(self):
        self.assertEqual(infix_to_postfix("a+b?"), "a+b?.")

    def test_syntax_validation_errors(self):
        # Empty input
        with self.assertRaises(RegexParseError):
            validate_syntax("")

        # Unbalanced parentheses
        with self.assertRaises(RegexParseError):
            validate_syntax("(a|b")
        with self.assertRaises(RegexParseError):
            validate_syntax("a|b)")

        # Misplaced unary operator at start
        with self.assertRaises(RegexParseError):
            validate_syntax("*ab")
        with self.assertRaises(RegexParseError):
            validate_syntax("+ab")

        # Misplaced binary operator at start or end
        with self.assertRaises(RegexParseError):
            validate_syntax("|ab")
        with self.assertRaises(RegexParseError):
            validate_syntax("ab|")

        # Consecutive invalid operators
        with self.assertRaises(RegexParseError):
            validate_syntax("a||b")
        with self.assertRaises(RegexParseError):
            validate_syntax("()")

    def test_extract_alphabet(self):
        self.assertEqual(extract_alphabet("(a|b)*abb"), ["a", "b"])
        self.assertEqual(extract_alphabet("0(0|1)*1"), ["0", "1"])
        self.assertEqual(extract_alphabet("x|y|z"), ["x", "y", "z"])


if __name__ == "__main__":
    unittest.main()
