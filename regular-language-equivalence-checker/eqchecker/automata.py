"""Core automata data structures: NFA and DFA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Hashable, Iterable, Optional, Set, Tuple

State = Hashable
DEAD = "__dead__"


class AutomatonError(ValueError):
    """Raised when an automaton definition is invalid."""


@dataclass
class NFA:
    """Nondeterministic finite automaton with epsilon moves.

    Epsilon transitions use ``None`` as the symbol.
    """

    states: Set[State]
    alphabet: Set[str]
    transitions: Dict[Tuple[State, Optional[str]], Set[State]]
    start: State
    accepting: Set[State]

    def epsilon_closure(self, states: Iterable[State]) -> FrozenSet[State]:
        stack = list(states)
        closure = set(stack)
        while stack:
            s = stack.pop()
            for t in self.transitions.get((s, None), ()):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return frozenset(closure)

    def move(self, states: Iterable[State], symbol: str) -> Set[State]:
        result: Set[State] = set()
        for s in states:
            result |= self.transitions.get((s, symbol), set())
        return result

    def accepts(self, word: str) -> bool:
        current = self.epsilon_closure({self.start})
        for ch in word:
            current = self.epsilon_closure(self.move(current, ch))
        return bool(current & self.accepting)


@dataclass
class DFA:
    """Deterministic finite automaton (total once ``with_alphabet`` is applied)."""

    states: Set[State]
    alphabet: FrozenSet[str]
    delta: Dict[Tuple[State, str], State]
    start: State
    accepting: Set[State]

    def accepts(self, word: str) -> bool:
        s = self.start
        for ch in word:
            if (s, ch) not in self.delta:
                return False
            s = self.delta[(s, ch)]
        return s in self.accepting

    def with_alphabet(self, alphabet: Iterable[str]) -> "DFA":
        """Return a *complete* DFA over ``alphabet`` (united with our own).

        Any missing transition is redirected to a fresh dead (sink) state.
        """
        alphabet = frozenset(alphabet) | self.alphabet
        states = set(self.states)
        delta = dict(self.delta)
        if any((s, a) not in delta for s in states for a in alphabet):
            dead: State = DEAD
            while dead in states:
                dead = str(dead) + "_"
            states.add(dead)
            for s in states:
                for a in alphabet:
                    delta.setdefault((s, a), dead)
        return DFA(states, alphabet, delta, self.start, set(self.accepting))
