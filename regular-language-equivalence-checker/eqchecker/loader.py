"""Turn a user-supplied spec (regex string or JSON file) into a DFA."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .automata import DFA, NFA, AutomatonError
from .subset import nfa_to_dfa
from .thompson import regex_to_nfa

_EPS_KEYS = {"eps", "epsilon", "ε", ""}


@dataclass
class Compiled:
    source: str
    kind: str                 # "regex" | "nfa" | "dfa"
    nfa: Optional[NFA]        # None when the input already was a DFA
    dfa: DFA


def compile_language(spec: str) -> Compiled:
    """``spec`` is a path ending in .json, or a regular expression."""
    if spec.lower().endswith(".json") and os.path.isfile(spec):
        return _load_json(spec)
    nfa = regex_to_nfa(spec)
    return Compiled(spec, "regex", nfa, nfa_to_dfa(nfa))


def _as_list(value):
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def _load_json(path: str) -> Compiled:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    try:
        kind = str(data.get("type", "dfa")).lower()
        alphabet = set(data["alphabet"])
        states = set(data["states"])
        start = data["start"]
        accepting = set(data["accepting"])
        raw = data.get("transitions", {})
    except KeyError as exc:
        raise AutomatonError(f"{path}: missing field {exc}") from None

    if start not in states:
        raise AutomatonError(f"{path}: start state {start!r} not in states")
    if not accepting <= states:
        raise AutomatonError(f"{path}: accepting states must be a subset of states")
    if kind not in ("dfa", "nfa"):
        raise AutomatonError(f"{path}: type must be 'dfa' or 'nfa'")

    def check(src, sym, targets):
        if src not in states or not set(targets) <= states:
            raise AutomatonError(f"{path}: unknown state in transition from {src!r}")
        if sym is not None and sym not in alphabet:
            raise AutomatonError(f"{path}: symbol {sym!r} not in alphabet")

    if kind == "dfa":
        delta = {}
        for src, row in raw.items():
            for sym, target in row.items():
                targets = _as_list(target)
                if len(targets) != 1:
                    raise AutomatonError(
                        f"{path}: DFA state {src!r} has several targets on {sym!r}")
                check(src, sym, targets)
                delta[(src, sym)] = targets[0]
        dfa = DFA(states, frozenset(alphabet), delta, start, accepting)
        return Compiled(path, "dfa", None, dfa.with_alphabet(alphabet))

    trans = defaultdict(set)
    for src, row in raw.items():
        for sym, targets in row.items():
            sym = None if sym in _EPS_KEYS else sym
            targets = _as_list(targets)
            check(src, sym, targets)
            trans[(src, sym)].update(targets)
    nfa = NFA(states, alphabet, dict(trans), start, accepting)
    return Compiled(path, "nfa", nfa, nfa_to_dfa(nfa))
