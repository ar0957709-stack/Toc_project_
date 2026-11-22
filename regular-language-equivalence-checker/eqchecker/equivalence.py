"""Equivalence test via product automaton (symmetric difference) + BFS."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional

from .automata import DFA
from .minimize import minimize


@dataclass
class EquivalenceResult:
    equivalent: bool
    counterexample: Optional[str]      # raw word ("" == empty string)
    accepted_by: Optional[str]         # "A" or "B" (the one that accepts it)
    min_a: DFA
    min_b: DFA
    isomorphic: bool                   # minimal DFAs identical up to renaming
    explored_pairs: int                # product states visited


def format_word(word: str) -> str:
    return word if word else "ε"


def check_equivalence(dfa_a: DFA, dfa_b: DFA) -> EquivalenceResult:
    """Decide L(A) == L(B).

    1. Complete both DFAs over the union alphabet and minimize them.
    2. BFS over the product automaton; a reachable pair where exactly one
       component accepts is a state of L(A) XOR L(B). BFS yields the shortest
       distinguishing word. If none is reachable, the languages are equal.
    """
    sigma = sorted(dfa_a.alphabet | dfa_b.alphabet)
    a = minimize(dfa_a.with_alphabet(sigma))
    b = minimize(dfa_b.with_alphabet(sigma))
    isomorphic = (a.delta == b.delta and a.accepting == b.accepting
                  and a.start == b.start)

    start = (a.start, b.start)
    parent = {start: None}
    queue = deque([start])
    while queue:
        pair = queue.popleft()
        p, q = pair
        if (p in a.accepting) != (q in b.accepting):
            symbols = []
            node = pair
            while parent[node] is not None:
                node, sym = parent[node]
                symbols.append(sym)
            word = "".join(reversed(symbols))
            return EquivalenceResult(
                False, word, "A" if p in a.accepting else "B",
                a, b, isomorphic, len(parent))
        for sym in sigma:
            nxt = (a.delta[(p, sym)], b.delta[(q, sym)])
            if nxt not in parent:
                parent[nxt] = (pair, sym)
                queue.append(nxt)
    return EquivalenceResult(True, None, None, a, b, isomorphic, len(parent))
