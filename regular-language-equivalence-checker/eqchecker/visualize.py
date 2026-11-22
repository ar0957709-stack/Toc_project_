"""Text tables and Graphviz DOT output for automata."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections import defaultdict

from .automata import DFA
from .minimize import canonicalize


def format_table(dfa: DFA) -> str:
    """Transition table. '->' marks the start state, '*' accepting states."""
    d = canonicalize(dfa)
    syms = sorted(d.alphabet)
    rows = [["state"] + syms]
    for s in sorted(d.states):
        mark = ("->" if s == d.start else "  ") + ("*" if s in d.accepting else " ")
        rows.append([f"{mark}q{s}"] + [f"q{d.delta[(s, a)]}" for a in syms])
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines = [" | ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows]
    lines.insert(1, "-+-".join("-" * w for w in widths))
    return "\n".join(lines)


def to_dot(dfa: DFA, title: str = "DFA") -> str:
    d = canonicalize(dfa)
    safe = title.replace('"', "'")
    out = ["digraph G {", "  rankdir=LR;", f'  labelloc=t; label="{safe}";',
           "  __start [shape=point];"]
    for s in sorted(d.states):
        shape = "doublecircle" if s in d.accepting else "circle"
        out.append(f"  q{s} [shape={shape}];")
    out.append(f"  __start -> q{d.start};")
    edges = defaultdict(list)
    for (s, a), t in d.delta.items():
        edges[(s, t)].append(a)
    for (s, t), labels in sorted(edges.items()):
        lab = ",".join(sorted(labels)).replace('"', '\\"')
        out.append(f'  q{s} -> q{t} [label="{lab}"];')
    out.append("}")
    return "\n".join(out) + "\n"


def write_dot(dfa: DFA, directory: str, name: str, title: str) -> str:
    """Write ``name``.dot (and ``name``.png if Graphviz is installed)."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.dot")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(to_dot(dfa, title))
    exe = shutil.which("dot")
    if exe:
        subprocess.run([exe, "-Tpng", path, "-o", path[:-4] + ".png"], check=False)
    return path
