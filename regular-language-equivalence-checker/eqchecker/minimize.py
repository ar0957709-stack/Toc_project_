"""DFA minimization by partition refinement (Myhill-Nerode / Moore)."""

from __future__ import annotations

from collections import deque

from .automata import DFA


def canonicalize(dfa: DFA) -> DFA:
    """Drop unreachable states and rename the rest 0..n-1 in BFS order.

    BFS visits symbols in sorted order, so two isomorphic DFAs get *identical*
    canonical forms -- equality of canonical forms == isomorphism.
    """
    syms = sorted(dfa.alphabet)
    order = {dfa.start: 0}
    queue = deque([dfa.start])
    while queue:
        s = queue.popleft()
        for a in syms:
            t = dfa.delta.get((s, a))
            if t is not None and t not in order:
                order[t] = len(order)
                queue.append(t)
    delta = {(order[s], a): order[t]
             for (s, a), t in dfa.delta.items() if s in order}
    return DFA(set(order.values()), dfa.alphabet, delta, 0,
               {order[s] for s in dfa.accepting if s in order})


def minimize(dfa: DFA) -> DFA:
    """Return the unique minimal complete DFA (canonically labelled)."""
    dfa = canonicalize(dfa.with_alphabet(dfa.alphabet))
    syms = sorted(dfa.alphabet)

    # Start with {accepting, non-accepting}; split blocks until stable.
    block = {s: int(s in dfa.accepting) for s in dfa.states}
    count = len(set(block.values()))
    while True:
        sigs = {s: (block[s], tuple(block[dfa.delta[(s, a)]] for a in syms))
                for s in sorted(dfa.states)}
        ids: dict = {}
        new = {s: ids.setdefault(sig, len(ids)) for s, sig in sigs.items()}
        block = new
        if len(ids) == count:
            break
        count = len(ids)

    delta = {(block[s], a): block[dfa.delta[(s, a)]]
             for s in dfa.states for a in syms}
    quotient = DFA(set(block.values()), dfa.alphabet, delta,
                   block[dfa.start], {block[s] for s in dfa.accepting})
    return canonicalize(quotient)
