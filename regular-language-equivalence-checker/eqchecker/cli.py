"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .automata import AutomatonError
from .equivalence import check_equivalence, format_word
from .loader import Compiled, compile_language
from .regex_parser import RegexSyntaxError
from .visualize import format_table, write_dot


def _pipeline_line(label: str, c: Compiled, minimal_states: int) -> str:
    parts = []
    if c.nfa is not None:
        parts.append(f"NFA {len(c.nfa.states)} state(s)")
    parts.append(f"DFA {len(c.dfa.states)} state(s)")
    parts.append(f"minimal DFA {minimal_states} state(s)")
    return f"  {label}: " + " -> ".join(parts)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="eqchecker",
        description="Decide whether two regular languages are equivalent. "
                    "Each argument is a regular expression or a .json "
                    "DFA/NFA file.")
    p.add_argument("first", help="regex or .json file (language A)")
    p.add_argument("second", help="regex or .json file (language B)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="print the transition tables of the minimal DFAs")
    p.add_argument("--dot-dir", metavar="DIR",
                   help="write Graphviz .dot files (and .png if `dot` is installed)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    try:  # make 'ε' printable on any console
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    args = build_parser().parse_args(argv)
    try:
        a = compile_language(args.first)
        b = compile_language(args.second)
    except (RegexSyntaxError, AutomatonError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    res = check_equivalence(a.dfa, b.dfa)

    print(f"Language A : {a.source}  [{a.kind}]")
    print(f"Language B : {b.source}  [{b.kind}]")
    print("\nPipeline")
    print(_pipeline_line("A", a, len(res.min_a.states)))
    print(_pipeline_line("B", b, len(res.min_b.states)))

    if args.verbose:
        print("\nMinimal DFA of A\n" + format_table(res.min_a))
        print("\nMinimal DFA of B\n" + format_table(res.min_b))

    if args.dot_dir:
        for tag, c, m in (("A", a, res.min_a), ("B", b, res.min_b)):
            write_dot(c.dfa, args.dot_dir, f"{tag}_dfa", f"{tag}: DFA ({c.source})")
            write_dot(m, args.dot_dir, f"{tag}_minimal", f"{tag}: minimal DFA")
        print(f"\nDiagrams written to {args.dot_dir}/")

    print()
    if res.equivalent:
        print("Verdict: EQUIVALENT")
        print(f"Justification: the minimal DFAs are isomorphic "
              f"({len(res.min_a.states)} state(s) each). By the Myhill-Nerode "
              f"theorem the minimal DFA is unique, so L(A) = L(B). The "
              f"symmetric-difference automaton explored {res.explored_pairs} "
              f"reachable state pair(s) and none was accepting.")
        return 0

    other = "B" if res.accepted_by == "A" else "A"
    print("Verdict: NOT EQUIVALENT")
    print(f"Shortest distinguishing string: '{format_word(res.counterexample)}'")
    print(f"Justification: it is accepted by {res.accepted_by} but rejected by "
          f"{other}, so it lies in the symmetric difference L(A) ⊕ L(B).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
