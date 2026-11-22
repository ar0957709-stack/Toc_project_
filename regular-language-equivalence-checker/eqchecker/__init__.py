"""Equivalence Checker for Regular Languages.

Pipeline: regex -> NFA (Thompson) -> DFA (subset construction)
          -> minimal DFA (partition refinement) -> product automaton BFS.
"""

from .automata import DFA, NFA, AutomatonError
from .equivalence import EquivalenceResult, check_equivalence, format_word
from .loader import Compiled, compile_language
from .minimize import canonicalize, minimize
from .regex_parser import RegexSyntaxError, parse_regex
from .subset import nfa_to_dfa
from .thompson import regex_to_nfa

__version__ = "1.0.0"

__all__ = [
    "DFA", "NFA", "AutomatonError", "RegexSyntaxError",
    "EquivalenceResult", "check_equivalence", "format_word",
    "Compiled", "compile_language",
    "canonicalize", "minimize", "parse_regex", "nfa_to_dfa", "regex_to_nfa",
]
