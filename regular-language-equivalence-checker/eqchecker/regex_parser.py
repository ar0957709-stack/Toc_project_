"""Recursive-descent parser: regular expression -> abstract syntax tree.

Grammar (lowest to highest precedence)::

    alt     := cat ('|' cat)*
    cat     := postfix*                 (empty -> epsilon)
    postfix := atom ('*' | '+' | '?')*
    atom    := '(' alt ')' | 'ε' | '\\' char | char

AST nodes are tuples: ('eps',) ('sym', c) ('cat', l, r) ('alt', l, r)
('star', x) ('plus', x) ('opt', x).
"""

from __future__ import annotations

from typing import Tuple

Node = Tuple

_POSTFIX = {"*": "star", "+": "plus", "?": "opt"}


class RegexSyntaxError(ValueError):
    """Raised for malformed regular expressions."""


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = "".join(text.split())  # ignore whitespace
        self.pos = 0

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def parse(self) -> Node:
        node = self.alt()
        if self.peek() is not None:
            raise RegexSyntaxError(
                f"unexpected {self.peek()!r} at position {self.pos}")
        return node

    def alt(self) -> Node:
        node = self.cat()
        while self.peek() == "|":
            self.pos += 1
            node = ("alt", node, self.cat())
        return node

    def cat(self) -> Node:
        parts = []
        while self.peek() is not None and self.peek() not in "|)":
            parts.append(self.postfix())
        if not parts:
            return ("eps",)
        node = parts[0]
        for p in parts[1:]:
            node = ("cat", node, p)
        return node

    def postfix(self) -> Node:
        node = self.atom()
        while self.peek() in _POSTFIX:
            node = (_POSTFIX[self.peek()], node)
            self.pos += 1
        return node

    def atom(self) -> Node:
        c = self.peek()
        if c == "(":
            self.pos += 1
            node = self.alt()
            if self.peek() != ")":
                raise RegexSyntaxError("missing ')'")
            self.pos += 1
            return node
        if c in _POSTFIX:
            raise RegexSyntaxError(
                f"nothing to repeat before {c!r} at position {self.pos}")
        if c == "\\":
            self.pos += 1
            c = self.peek()
            if c is None:
                raise RegexSyntaxError("dangling '\\' at end of expression")
            self.pos += 1
            return ("sym", c)
        self.pos += 1
        return ("eps",) if c == "ε" else ("sym", c)


def parse_regex(text: str) -> Node:
    """Parse ``text`` into an AST."""
    return _Parser(text).parse()
