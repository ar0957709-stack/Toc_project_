import itertools
import os
import re
import unittest

from eqchecker import (RegexSyntaxError, check_equivalence, compile_language,
                       minimize, nfa_to_dfa, regex_to_nfa)

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def dfa_of(regex):
    return compile_language(regex).dfa


def words(alphabet, max_len):
    for n in range(max_len + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield "".join(t)


class ThompsonAndSubset(unittest.TestCase):
    CASES = ["a", "ab", "a|b", "a*", "(a|b)*abb", "a+b?", "(ab|a)*", "ε|a"]

    def test_nfa_and_dfa_agree_with_python_re(self):
        for rx in self.CASES:
            py = re.compile(rx.replace("ε", "(?:)"))
            nfa = regex_to_nfa(rx)
            dfa = nfa_to_dfa(nfa)
            for w in words("ab", 6):
                expected = py.fullmatch(w) is not None
                self.assertEqual(nfa.accepts(w), expected, (rx, w))
                self.assertEqual(dfa.accepts(w), expected, (rx, w))

    def test_syntax_errors(self):
        for bad in ["(a", "a)", "*a", "a**+(", "\\"]:
            with self.assertRaises(RegexSyntaxError, msg=bad):
                regex_to_nfa(bad)


class Minimization(unittest.TestCase):
    def test_classic_abb_has_four_states(self):
        self.assertEqual(len(minimize(dfa_of("(a|b)*abb")).states), 4)

    def test_star_collapses_to_one_state(self):
        self.assertEqual(len(minimize(dfa_of("(a*)*")).states), 1)

    def test_minimization_preserves_language(self):
        for rx in ["(a|b)*abb", "a(b|c)*", "(ab)*a?"]:
            d = dfa_of(rx)
            m = minimize(d)
            for w in words(sorted(d.alphabet), 6):
                self.assertEqual(d.accepts(w), m.accepts(w), (rx, w))


class Equivalence(unittest.TestCase):
    EQUIVALENT = [
        ("(a|b)*", "(a*b*)*"),
        ("a*", "(a*)*"),
        ("(ab)*a", "a(ba)*"),
        ("a+", "aa*"),
        ("a?", "a|ε"),
        ("a(b|c)", "ab|ac"),
        ("(a|b)*abb", "(a|b)*abb"),
    ]
    DIFFERENT = [
        ("a*b", "ab*"),
        ("(a|b)*", "a*b*"),
        ("(ab)*", "a*b*"),
        ("a+", "a*"),
        ("(a|b)*abb", "(a|b)*aab"),
    ]

    def test_equivalent_pairs(self):
        for r1, r2 in self.EQUIVALENT:
            res = check_equivalence(dfa_of(r1), dfa_of(r2))
            self.assertTrue(res.equivalent, (r1, r2))
            self.assertTrue(res.isomorphic, (r1, r2))
            self.assertIsNone(res.counterexample)

    def test_different_pairs_give_valid_shortest_counterexample(self):
        for r1, r2 in self.DIFFERENT:
            res = check_equivalence(dfa_of(r1), dfa_of(r2))
            self.assertFalse(res.equivalent, (r1, r2))
            w = res.counterexample
            in1 = re.fullmatch(r1, w) is not None
            in2 = re.fullmatch(r2, w) is not None
            self.assertNotEqual(in1, in2, (r1, r2, w))
            self.assertEqual(res.accepted_by, "A" if in1 else "B")
            # shortest: no shorter word separates the languages
            for v in words("abc", len(w) - 1):
                self.assertEqual(re.fullmatch(r1, v) is None,
                                 re.fullmatch(r2, v) is None, (r1, r2, v))

    def test_different_alphabets(self):
        res = check_equivalence(dfa_of("a*"), dfa_of("a*|b"))
        self.assertFalse(res.equivalent)
        self.assertEqual(res.counterexample, "b")

    def test_empty_string_counterexample(self):
        res = check_equivalence(dfa_of("a+"), dfa_of("a*"))
        self.assertEqual(res.counterexample, "")
        self.assertEqual(res.accepted_by, "B")


class JsonInputs(unittest.TestCase):
    def path(self, name):
        return os.path.join(EXAMPLES, name)

    def test_redundant_dfa_equals_minimal_dfa(self):
        a = compile_language(self.path("even_a.json")).dfa
        b = compile_language(self.path("even_a_redundant.json")).dfa
        res = check_equivalence(a, b)
        self.assertTrue(res.equivalent)
        self.assertEqual(len(res.min_b.states), 2)

    def test_nfa_json_equals_regex(self):
        a = compile_language(self.path("nfa_ends_ab.json")).dfa
        res = check_equivalence(a, dfa_of("(a|b)*ab"))
        self.assertTrue(res.equivalent)

    def test_json_vs_wrong_regex(self):
        a = compile_language(self.path("even_a.json")).dfa
        res = check_equivalence(a, dfa_of("(b*ab*a)*b*|a"))
        self.assertFalse(res.equivalent)


if __name__ == "__main__":
    unittest.main()
