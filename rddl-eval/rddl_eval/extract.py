"""Pull the three RDDL blocks out of a model response.

pyRDDLGym wants two files, not three: the ``domain`` block goes into
``domain.rddl``, while ``non-fluents`` and ``instance`` have to share
``instance.rddl``.  This module is what turns a chat reply into that pair.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BLOCK_KINDS = ("domain", "non-fluents", "instance")

#: ``domain foo {``, ``non-fluents foo_nf {``, ``instance foo_inst {``.
#: The name is mandatory here, which is what keeps the inner, unnamed
#: ``non-fluents { ... };`` section of a non-fluents block from matching.
_BLOCK_HEADER = re.compile(
    r"(?<![\w\-])(domain|non-fluents|instance)\s+([\w\-.]+)\s*\{",
    re.IGNORECASE,
)

_FENCE = re.compile(r"```[ \t]*[\w+-]*[ \t]*\n(.*?)(?:```|\Z)", re.DOTALL)


class ExtractError(Exception):
    """Raised when the response does not contain the three blocks."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Block:
    """One top-level RDDL block, verbatim, plus what came right after it."""

    kind: str
    name: str
    text: str
    #: ``true`` when a ``;`` follows the closing brace.  pyRDDLGym rejects
    #: that for top-level blocks, so lint rule 4 needs to know.
    trailing_semicolon: bool

    @property
    def body(self) -> str:
        """Everything between the outermost braces."""
        open_at = self.text.index("{")
        return self.text[open_at + 1 : self.text.rindex("}")]


@dataclass(frozen=True)
class Blocks:
    domain: Block
    non_fluents: Block
    instance: Block

    def domain_file(self) -> str:
        return self.domain.text + "\n"

    def instance_file(self) -> str:
        """``non-fluents`` and ``instance`` concatenated, as pyRDDLGym expects."""
        return self.non_fluents.text + "\n\n" + self.instance.text + "\n"

    def __iter__(self):
        return iter((self.domain, self.non_fluents, self.instance))


def strip_comments(text: str) -> str:
    """Blank out ``//`` comments, preserving offsets so positions stay valid."""
    out = []
    for line in text.splitlines(keepends=True):
        head, sep, tail = line.partition("//")
        if sep:
            newlines = tail.count("\n")
            out.append(head + " " * (len(sep) + len(tail) - newlines) + "\n" * newlines)
        else:
            out.append(line)
    return "".join(out)


def _match_brace(text: str, open_at: int) -> int:
    """Index of the ``}`` closing the ``{`` at *open_at*, or -1."""
    depth = 0
    for i in range(open_at, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _candidate_text(response: str) -> str:
    """Prefer fenced code, fall back to the raw reply.

    The model is asked for ```` ```rddl ```` fences and usually complies, but
    not always, and it sometimes fences only part of the answer.  Fenced
    content wins when it holds all three blocks; otherwise take the whole
    reply, which costs nothing because block extraction is keyword-driven.
    """
    fenced = "\n".join(m.group(1) for m in _FENCE.finditer(response))
    if fenced.strip() and _found_kinds(fenced) == set(BLOCK_KINDS):
        return fenced
    return response


def _found_kinds(text: str) -> set[str]:
    stripped = strip_comments(text)
    return {m.group(1).lower() for m in _BLOCK_HEADER.finditer(stripped)}


def extract_blocks(response: str) -> Blocks:
    """Split a model reply into its ``domain`` / ``non-fluents`` / ``instance``.

    Blocks are recognised by their leading keyword, not by their order in the
    reply, and a duplicate block keeps the first occurrence.
    """
    text = _candidate_text(response)
    scan = strip_comments(text)

    found: dict[str, Block] = {}
    duplicates: list[str] = []
    pos = 0
    while (match := _BLOCK_HEADER.search(scan, pos)) is not None:
        kind = match.group(1).lower()
        open_at = scan.index("{", match.start())
        close_at = _match_brace(scan, open_at)
        if close_at < 0:
            raise ExtractError(
                [
                    f"The `{kind}` block is not closed: a `{{` is never matched by a "
                    f"`}}`. Emit every block in full."
                ]
            )
        rest = scan[close_at + 1 :]
        block = Block(
            kind=kind,
            name=match.group(2),
            text=text[match.start() : close_at + 1],
            trailing_semicolon=rest.lstrip(" \t\r\n").startswith(";"),
        )
        if kind in found:
            duplicates.append(kind)
        else:
            found[kind] = block
        pos = close_at + 1

    problems = [
        f"The response contains no `{kind}` block. Emit all three blocks: "
        f"`domain`, `non-fluents` and `instance`."
        for kind in BLOCK_KINDS
        if kind not in found
    ]
    problems += [
        f"The response contains more than one `{kind}` block. Emit exactly one of each."
        for kind in dict.fromkeys(duplicates)
    ]
    if problems:
        raise ExtractError(problems)

    return Blocks(
        domain=found["domain"],
        non_fluents=found["non-fluents"],
        instance=found["instance"],
    )
