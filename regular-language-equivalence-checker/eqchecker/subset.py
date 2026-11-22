"""Subset construction: NFA -> complete DFA."""

from __future__ import annotations

from collections import deque
from typing import Iterable, Optional

from .automata import DFA, NFA


def nfa_to_dfa(nfa: NFA, alphabet: Optional[Iterable[str]] = None) -> DFA:
    """Convert ``nfa`` to a complete DFA. The empty subset acts as the dead state."""
    sigma = frozenset(alphabet) if alphabet is not None else frozenset(nfa.alphabet)
    start = nfa.epsilon_closure({nfa.start})
    seen = {start}
    delta = {}
    queue = deque([start])
    while queue:
        subset = queue.popleft()
        for a in sorted(sigma):
            target = nfa.epsilon_closure(nfa.move(subset, a))
            delta[(subset, a)] = target
            if target not in seen:
                seen.add(target)
                queue.append(target)
    accepting = {s for s in seen if s & nfa.accepting}
    return DFA(seen, sigma, delta, start, accepting)
