"""Thompson's construction: regular expression -> epsilon-NFA."""

from __future__ import annotations

from collections import defaultdict
from typing import Tuple

from .automata import NFA
from .regex_parser import Node, parse_regex


class _Builder:
    def __init__(self) -> None:
        self.count = 0
        self.trans = defaultdict(set)
        self.alphabet = set()

    def new(self) -> int:
        self.count += 1
        return self.count - 1

    def add(self, s: int, sym, t: int) -> None:
        self.trans[(s, sym)].add(t)

    def build(self, node: Node) -> Tuple[int, int]:
        """Return (start, accept) of the fragment for ``node``."""
        kind = node[0]
        if kind == "eps":
            s, a = self.new(), self.new()
            self.add(s, None, a)
            return s, a
        if kind == "sym":
            s, a = self.new(), self.new()
            self.add(s, node[1], a)
            self.alphabet.add(node[1])
            return s, a
        if kind == "cat":
            s1, a1 = self.build(node[1])
            s2, a2 = self.build(node[2])
            self.add(a1, None, s2)
            return s1, a2
        if kind == "alt":
            s, a = self.new(), self.new()
            s1, a1 = self.build(node[1])
            s2, a2 = self.build(node[2])
            for x in (s1, s2):
                self.add(s, None, x)
            for x in (a1, a2):
                self.add(x, None, a)
            return s, a
        if kind == "star":
            s, a = self.new(), self.new()
            s1, a1 = self.build(node[1])
            self.add(s, None, s1)
            self.add(s, None, a)
            self.add(a1, None, s1)
            self.add(a1, None, a)
            return s, a
        if kind == "plus":      # x+  ==  x x*
            return self.build(("cat", node[1], ("star", node[1])))
        if kind == "opt":       # x?  ==  x | ε
            return self.build(("alt", node[1], ("eps",)))
        raise ValueError(f"unknown AST node {kind!r}")


def regex_to_nfa(regex: str) -> NFA:
    b = _Builder()
    start, accept = b.build(parse_regex(regex))
    return NFA(
        states=set(range(b.count)),
        alphabet=set(b.alphabet),
        transitions=dict(b.trans),
        start=start,
        accepting={accept},
    )
