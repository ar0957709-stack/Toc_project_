# Toc_project_
# Equivalence Checker for Regular Languages

[![CI](https://github.com/<your-username>/regular-language-equivalence-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/regular-language-equivalence-checker/actions)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A tool that decides whether two regular languages, given as **regular expressions, NFAs or DFAs**, are equivalent. When they differ, it prints the **shortest distinguishing string** as a counter-example.



## How it works

```
regex ──Thompson──▶ NFA ──subset construction──▶ DFA ──partition refinement──▶ minimal DFA
                                                                                   │
        A and B (minimal, same alphabet) ──product automaton + BFS──▶ verdict ◀────┘
```

1. **Parse** the regex into an AST (`|`, concatenation, `*`, `+`, `?`, `( )`, `ε`).
2. **Thompson's construction** turns the AST into an ε-NFA. NFA JSON files are loaded directly.
3. **Subset construction** gives a complete DFA (the empty subset is the dead state).
4. **Minimization** by partition refinement (Myhill–Nerode) gives the unique minimal DFA, relabelled canonically.
5. **Product automaton / symmetric difference**: BFS over pairs `(p, q)`. A reachable pair where exactly one side accepts lies in `L(A) ⊕ L(B)`.
   - Found: **NOT EQUIVALENT**, and the BFS path is the shortest counter-example.
   - Not found: **EQUIVALENT**, and the minimal DFAs are isomorphic.

| Step | Complexity |
| --- | --- |
| Thompson's construction | O(m) states for a regex of length m |
| Subset construction | O(2ⁿ) worst case |
| Minimization (partition refinement) | O(n² · \|Σ\|) |
| Product BFS | O(n_A · n_B · \|Σ\|) |

## Project structure

```
.
├── eqchecker/
│   ├── regex_parser.py   # regex -> AST
│   ├── thompson.py       # AST -> NFA
│   ├── subset.py         # NFA -> DFA
│   ├── minimize.py       # DFA minimization + canonical form
│   ├── equivalence.py    # product automaton + counter-example
│   ├── loader.py         # regex / JSON input
│   ├── visualize.py      # transition tables + Graphviz DOT
│   ├── automata.py       # NFA / DFA classes
│   └── cli.py            # command-line interface
├── examples/             # sample DFA / NFA JSON files
├── tests/                # unit tests
└── .github/workflows/    # CI
```

## Installation

No third-party dependencies are needed (Python 3.9+).

```bash
git clone https://github.com/<your-username>/regular-language-equivalence-checker.git
cd regular-language-equivalence-checker
pip install -e .        # optional: installs the `eqchecker` command
```

Optional: install [Graphviz](https://graphviz.org) to render diagrams to PNG.

## Usage

```bash
python -m eqchecker "<language A>" "<language B>" [-v] [--dot-dir DIR]
```

Each language is a regex or a path to a `.json` automaton. Exit code: `0` equivalent, `1` not equivalent, `2` input error.

### Equivalent regexes

```console
$ python -m eqchecker "(a|b)*" "(a*b*)*"
Language A : (a|b)*  [regex]
Language B : (a*b*)*  [regex]

Pipeline
  A: NFA 8 state(s) -> DFA 3 state(s) -> minimal DFA 1 state(s)
  B: NFA 10 state(s) -> DFA 3 state(s) -> minimal DFA 1 state(s)

Verdict: EQUIVALENT
Justification: the minimal DFAs are isomorphic (1 state(s) each). By the Myhill-Nerode theorem the minimal DFA is unique, so L(A) = L(B). The symmetric-difference automaton explored 1 reachable state pair(s) and none was accepting.
```

### Different regexes (with counter-example)

```console
$ python -m eqchecker "(a|b)*abb" "(a|b)*aab"
...
Verdict: NOT EQUIVALENT
Shortest distinguishing string: 'aab'
Justification: it is accepted by B but rejected by A, so it lies in the symmetric difference L(A) ⊕ L(B).
```

### DFA / NFA files, tables and diagrams

```console
$ python -m eqchecker examples/even_a.json examples/even_a_redundant.json -v --dot-dir out
```

`-v` prints the minimal DFA transition tables (`->` start, `*` accepting). `--dot-dir` writes `.dot` files for the input and minimal DFAs of both languages, plus `.png` if Graphviz is installed.

### Regex syntax

| Syntax | Meaning |
| --- | --- |
| `ab` | concatenation |
| `a\|b` | union |
| `a*`, `a+`, `a?` | Kleene star, one-or-more, optional |
| `( )` | grouping |
| `ε` | empty string |
| `\*` | escape a special character |

Whitespace is ignored. The alphabet is every symbol appearing in the regexes.

### JSON automaton format

```json
{
  "type": "nfa",
  "alphabet": ["a", "b"],
  "states": ["q0", "q1", "q2"],
  "start": "q0",
  "accepting": ["q2"],
  "transitions": {
    "q0": {"a": ["q0", "q1"], "b": ["q0"]},
    "q1": {"b": ["q2"]}
  }
}
```

- `"type"` is `"dfa"` or `"nfa"` (default `"dfa"`).
- For NFAs, ε-moves use the key `"eps"`.
- Missing DFA transitions go to an implicit dead state.

### Use as a library

```python
from eqchecker import compile_language, check_equivalence

a = compile_language("(ab)*a").dfa
b = compile_language("a(ba)*").dfa
print(check_equivalence(a, b).equivalent)   # True
```

## Testing

```bash
python -m unittest discover -s tests -t . -v
```

The suite covers:
- Thompson/subset correctness, cross-checked against Python's `re` on every string up to length 6.
- Minimization, e.g. `(a|b)*abb` gives the classic 4-state DFA.
- Equivalent and non-equivalent regex pairs, checking that counter-examples are valid **and** shortest.
- JSON DFA/NFA inputs and syntax-error handling.

## Scope

Handles DFAs, NFAs and regular expressions over finite alphabets. Context-free and context-sensitive languages are out of scope.

## License

MIT, see [LICENSE](LICENSE).
