"""Static checks that run before pyRDDLGym ever sees the blocks.

The parser reports failures as token positions ("Syntax error on line 18"),
which tells a language model almost nothing about what to change.  Every rule
here phrases its finding as an instruction that can be pasted straight into a
repair turn.

Each rule number matches the numbering in ``instructions.md``.  Severity lives
in :data:`RULE_SEVERITY` so a rule can be demoted without touching its logic --
see the rule table in the README for which rules pyRDDLGym 2.7 also rejects and
which are lint-only conventions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .extract import Blocks, strip_comments

ERROR = "error"
WARNING = "warning"

#: Canonical section order inside a ``domain`` block.  pyRDDLGym's grammar is
#: strict about this; any other order is a syntax error.
DOMAIN_SECTION_ORDER = (
    "requirements",
    "types",
    "pvariables",
    "cpfs",
    "reward",
    "state-invariants",
    "action-preconditions",
    "termination",
)

#: Braced sections recognised at the top level of a block.  Restricting the
#: scan to known names keeps ``sum_{...}`` from being mistaken for a section.
_DOMAIN_SECTIONS = frozenset(DOMAIN_SECTION_ORDER) | {"cdfs", "observ"}
_INSTANCE_SECTIONS = frozenset({"objects", "non-fluents", "init-state"})

_FLUENT_TYPES = (
    "non-fluent",
    "state-fluent",
    "action-fluent",
    "interm-fluent",
    "derived-fluent",
    "observ-fluent",
)

RULE_SEVERITY: dict[int, str] = {
    1: ERROR,
    2: ERROR,
    3: ERROR,
    4: ERROR,
    5: ERROR,
    6: ERROR,
    7: ERROR,
    8: ERROR,
    9: ERROR,
    10: ERROR,
    11: ERROR,
    12: ERROR,
    13: ERROR,
    14: WARNING,
}


@dataclass(frozen=True)
class Problem:
    rule: int
    severity: str
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class LintReport:
    errors: list[Problem] = field(default_factory=list)
    warnings: list[Problem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def rules_fired(self) -> set[int]:
        return {p.rule for p in self.errors + self.warnings}


# --------------------------------------------------------------------------
# text helpers
# --------------------------------------------------------------------------

_ASSIGN = re.compile(r"(?<![=<>~])=(?!=|>)")


def _depth_map(text: str) -> list[int]:
    """Brace depth *outside* each character (so a ``{`` sits at its own depth)."""
    depths: list[int] = []
    depth = 0
    for char in text:
        if char == "}":
            depth -= 1
        depths.append(depth)
        if char == "{":
            depth += 1
    return depths


def _match_brace(text: str, open_at: int) -> int:
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _match_bracket(text: str, open_at: int) -> int:
    """Matching close for ``(`` or ``[`` at *open_at*, or -1."""
    pairs = {"(": ")", "[": "]"}
    opener = text[open_at]
    closer = pairs[opener]
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
            if depth == 0:
                return i
    return -1


@dataclass(frozen=True)
class Section:
    name: str
    body: str
    #: index just past the section's closing brace
    end: int
    followed_by_semicolon: bool


def _sections(body: str, known: frozenset[str]) -> list[Section]:
    """Braced sections sitting at depth 0 of *body*, in source order."""
    depths = _depth_map(body)
    out: list[Section] = []
    for match in re.finditer(r"(?<![\w\-?])([\w\-]+)\s*=?\s*\{", body):
        if match.group(1).lower() not in known:
            continue
        open_at = match.end() - 1
        if depths[open_at] != 0:
            continue
        close_at = _match_brace(body, open_at)
        if close_at < 0:
            continue
        rest = body[close_at + 1 :].lstrip(" \t\r\n")
        out.append(
            Section(
                name=match.group(1).lower(),
                body=body[open_at + 1 : close_at],
                end=close_at + 1,
                followed_by_semicolon=rest.startswith(";"),
            )
        )
    return out


def _section(sections: list[Section], name: str) -> Section | None:
    for section in sections:
        if section.name == name:
            return section
    return None


def _statements(body: str) -> list[str]:
    """Split on top-level ``;``, dropping empties."""
    depths = _depth_map(body)
    out, start = [], 0
    for i, char in enumerate(body):
        if char == ";" and depths[i] == 0 and not _inside_brackets(body, i):
            piece = body[start:i].strip()
            if piece:
                out.append(piece)
            start = i + 1
    tail = body[start:].strip()
    if tail:
        out.append(tail)
    return out


def _inside_brackets(text: str, index: int) -> bool:
    depth = 0
    for i in range(index):
        if text[i] in "([":
            depth += 1
        elif text[i] in ")]":
            depth -= 1
    return depth > 0


def _split_assignment(statement: str) -> tuple[str, str] | None:
    """Split ``lhs = rhs`` at the first top-level assignment ``=``."""
    depth = 0
    for i, char in enumerate(statement):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif depth == 0 and _ASSIGN.match(statement, i):
            return statement[:i].strip(), statement[i + 1 :].strip()
    return None


@dataclass(frozen=True)
class Pvariable:
    name: str
    fluent_type: str
    params: str


def _pvariables(domain_sections: list[Section]) -> list[Pvariable]:
    section = _section(domain_sections, "pvariables")
    if section is None:
        return []
    pattern = re.compile(
        r"(?<![\w\-])([\w\-]+)\s*(\([^)]*\))?\s*:\s*\{\s*(" + "|".join(_FLUENT_TYPES) + r")\b"
    )
    return [
        Pvariable(name=m.group(1), fluent_type=m.group(3), params=(m.group(2) or ""))
        for m in pattern.finditer(section.body)
    ]


def _assigned_names(body: str) -> list[str]:
    """Names on the left of ``=`` in an assignment section (objects aside)."""
    names = []
    for statement in _statements(body):
        split = _split_assignment(statement)
        if split is None:
            continue
        match = re.match(r"([\w\-]+)", split[0].strip())
        if match:
            names.append(match.group(1))
    return names


# --------------------------------------------------------------------------
# rule context
# --------------------------------------------------------------------------


@dataclass
class _Context:
    blocks: Blocks
    domain_body: str
    non_fluents_body: str
    instance_body: str
    domain_sections: list[Section]
    non_fluents_sections: list[Section]
    instance_sections: list[Section]
    pvariables: list[Pvariable]

    @classmethod
    def build(cls, blocks: Blocks) -> "_Context":
        domain_body = strip_comments(blocks.domain.body)
        non_fluents_body = strip_comments(blocks.non_fluents.body)
        instance_body = strip_comments(blocks.instance.body)
        domain_sections = _sections(domain_body, _DOMAIN_SECTIONS)
        return cls(
            blocks=blocks,
            domain_body=domain_body,
            non_fluents_body=non_fluents_body,
            instance_body=instance_body,
            domain_sections=domain_sections,
            non_fluents_sections=_sections(non_fluents_body, _INSTANCE_SECTIONS),
            instance_sections=_sections(instance_body, _INSTANCE_SECTIONS),
            pvariables=_pvariables(domain_sections),
        )

    def state_fluents(self) -> list[Pvariable]:
        return [p for p in self.pvariables if p.fluent_type == "state-fluent"]


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------


def _rule_01_non_fluents_declares_domain(ctx: _Context) -> list[str]:
    if not re.search(r"(?<![\w\-])domain\s*=\s*[\w\-.]+\s*;", ctx.non_fluents_body):
        return [
            f"The `non-fluents {ctx.blocks.non_fluents.name}` block does not say which "
            f"domain it belongs to. Add `domain = {ctx.blocks.domain.name};` as the "
            f"first statement inside it."
        ]
    return []


def _rule_02_instance_declares_links(ctx: _Context) -> list[str]:
    problems = []
    if not re.search(r"(?<![\w\-])domain\s*=\s*[\w\-.]+\s*;", ctx.instance_body):
        problems.append(
            f"The `instance {ctx.blocks.instance.name}` block does not declare its "
            f"domain. Add `domain = {ctx.blocks.domain.name};` inside it."
        )
    if not re.search(r"(?<![\w\-])non-fluents\s*=\s*[\w\-.]+\s*;", ctx.instance_body):
        problems.append(
            f"The `instance {ctx.blocks.instance.name}` block does not reference the "
            f"non-fluents block. Add `non-fluents = {ctx.blocks.non_fluents.name};` "
            f"inside it."
        )
    return problems


def _rule_03_distinct_non_fluents_name(ctx: _Context) -> list[str]:
    if ctx.blocks.non_fluents.name == ctx.blocks.domain.name:
        return [
            f"The non-fluents block is named `{ctx.blocks.non_fluents.name}`, the same "
            f"name as the domain. Give it a distinct name, for example "
            f"`{ctx.blocks.domain.name}_nf`, and reference that name from the instance "
            f"block."
        ]
    return []


def _rule_04_section_semicolons(ctx: _Context) -> list[str]:
    problems = []
    groups = (
        ("domain", ctx.blocks.domain.name, ctx.domain_sections),
        ("non-fluents", ctx.blocks.non_fluents.name, ctx.non_fluents_sections),
        ("instance", ctx.blocks.instance.name, ctx.instance_sections),
    )
    for kind, name, sections in groups:
        for section in sections:
            if not section.followed_by_semicolon:
                problems.append(
                    f"The `{section.name} {{ ... }}` section of `{kind} {name}` is not "
                    f"terminated by a semicolon. Every braced section inside a block "
                    f"must close with `}};`, not `}}`."
                )
    for block in ctx.blocks:
        if block.trailing_semicolon:
            problems.append(
                f"The top-level `{block.kind} {block.name} {{ ... }}` block is followed "
                f"by a semicolon. Top-level blocks close with `}}` and no semicolon; "
                f"only the sections inside them end with `}};`."
            )
    return problems


def _rule_05_domain_section_order(ctx: _Context) -> list[str]:
    depths = _depth_map(ctx.domain_body)
    found: list[tuple[int, str]] = [
        (start, name) for name, start in _domain_section_starts(ctx)
    ]
    for match in re.finditer(r"(?<![\w\-])reward\s*=", ctx.domain_body):
        if depths[match.start()] == 0:
            found.append((match.start(), "reward"))
            break
    found.sort()
    order = [name for _, name in found if name in DOMAIN_SECTION_ORDER]
    ranks = [DOMAIN_SECTION_ORDER.index(name) for name in order]
    if ranks != sorted(ranks):
        return [
            "The sections of the `domain` block are in the wrong order. RDDL requires "
            "them in exactly this order: "
            + ", ".join(DOMAIN_SECTION_ORDER)
            + ". Found: "
            + ", ".join(order)
            + "."
        ]
    return []


def _domain_section_starts(ctx: _Context) -> list[tuple[str, int]]:
    depths = _depth_map(ctx.domain_body)
    out = []
    for match in re.finditer(r"(?<![\w\-?])([\w\-]+)\s*=?\s*\{", ctx.domain_body):
        name = match.group(1).lower()
        if name not in _DOMAIN_SECTIONS:
            continue
        open_at = match.end() - 1
        if depths[open_at] == 0:
            out.append((name, match.start()))
    return out


_AGGREGATORS = ("sum", "prod", "avg", "min", "max", "forall", "exists")
_AGG_HEAD = re.compile(r"(?<![\w\-])(" + "|".join(_AGGREGATORS) + r")_\s*\{")
#: An operator right after an aggregation is silently pulled *into* it.
_BINARY_AFTER = re.compile(r"(<=>|=>|==|~=|<=|>=|\+|-|\*|/|\^|\||<|>)")


def _rule_06_aggregation_wrapping(ctx: _Context) -> list[str]:
    """Aggregations bind everything to their right, so they must be closed off.

    ``sum_{?s : shelf} [ 1 ] - 10`` over three objects evaluates to -27, not
    -7: the ``- 10`` is absorbed into the summand.  pyRDDLGym accepts it
    silently, so lint is the only place this can be caught.
    """
    problems = []
    for match in _AGG_HEAD.finditer(ctx.domain_body):
        name = match.group(1)
        brace_at = ctx.domain_body.index("{", match.end() - 1)
        var_end = _match_brace(ctx.domain_body, brace_at)
        if var_end < 0:
            continue
        rest = ctx.domain_body[var_end + 1 :]
        stripped = rest.lstrip()
        if not stripped or stripped[0] not in "[(":
            problems.append(
                f"The body of the `{name}_` aggregation is not bracketed. Write "
                f"`{name}_{{?x : type}} [ <expression> ]` -- without the brackets the "
                f"aggregation extends over everything that follows it."
            )
            continue
        body_open = var_end + 1 + (len(rest) - len(stripped))
        body_close = _match_bracket(ctx.domain_body, body_open)
        if body_close < 0:
            continue
        after = ctx.domain_body[body_close + 1 :].lstrip()
        if _BINARY_AFTER.match(after):
            operator = _BINARY_AFTER.match(after).group(1)
            problems.append(
                f"The `{name}_` aggregation is followed by `{operator}` at the same "
                f"level, so that operand is silently absorbed into the aggregation: "
                f"`{name}_{{...}} [ x ] {operator} y` means "
                f"`{name}_{{...}} [ x {operator} y ]`. Wrap the whole aggregation in "
                f"its own brackets: `({name}_{{...}} [ x ]) {operator} y`."
            )
    return problems


def _cpf_statements(ctx: _Context) -> list[tuple[str, str]]:
    section = _section(ctx.domain_sections, "cpfs")
    if section is None:
        return []
    out = []
    for statement in _statements(section.body):
        split = _split_assignment(statement)
        if split is not None:
            out.append(split)
    return out


def _rule_07_no_prime_on_rhs(ctx: _Context) -> list[str]:
    problems = []
    for lhs, rhs in _cpf_statements(ctx):
        primed = re.findall(r"(?<![\w\-])([\w\-]+)\s*(?:\([^)]*\))?\s*'", rhs)
        for name in dict.fromkeys(primed):
            problems.append(
                f"The CPF for `{lhs.strip()}` uses `{name}'` on the right-hand side. A "
                f"CPF may only read current-state values, so drop the prime and write "
                f"`{name}`; referring to the next state creates a cyclic dependency."
            )
    return problems


def _rule_08_prime_placement(ctx: _Context) -> list[str]:
    problems = []
    for match in re.finditer(r"(?<![\w\-])([\w\-]+)\s*(\([^)]*\))\s*'", ctx.domain_body):
        problems.append(
            f"`{match.group(1)}{match.group(2)}'` puts the prime after the parameter "
            f"list. The prime belongs on the name itself: "
            f"`{match.group(1)}'{match.group(2)}`."
        )
    return list(dict.fromkeys(problems))


def _rule_09_state_fluent_has_cpf(ctx: _Context) -> list[str]:
    if _section(ctx.domain_sections, "cpfs") is None:
        return []
    defined = set()
    for lhs, _ in _cpf_statements(ctx):
        # A misplaced prime -- ``f(?x)'`` -- still counts as a definition here,
        # so that rule 8 alone reports it.
        match = re.match(r"([\w\-]+)\s*(?:\([^)]*\))?\s*'", lhs.strip())
        if match:
            defined.add(match.group(1))
    problems = []
    for pvar in ctx.state_fluents():
        if pvar.name not in defined:
            params = pvar.params or ""
            signature = re.sub(r"\b([\w\-]+)\b", r"?\1", params) if params else ""
            problems.append(
                f"The state-fluent `{pvar.name}` has no CPF. Every state-fluent needs "
                f"an entry `{pvar.name}'{signature} = <expression>;` in the `cpfs` "
                f"section, even if it never changes (`{pvar.name}'{signature} = "
                f"{pvar.name}{signature};`)."
            )
    return problems


def _rule_10_if_parentheses(ctx: _Context) -> list[str]:
    problems = []
    for match in re.finditer(r"(?<![\w\-])if\b(?!\s*\()", ctx.domain_body):
        tail = ctx.domain_body[match.end() : match.end() + 40].strip().split("\n")[0]
        problems.append(
            f"The condition of `if {tail[:30]}...` is not parenthesised. RDDL requires "
            f"`if (<condition>) then <a> else <b>`, with the condition in round "
            f"brackets."
        )
    return problems[:3]


def _rule_11_state_fluent_in_non_fluents(ctx: _Context) -> list[str]:
    section = _section(ctx.non_fluents_sections, "non-fluents")
    if section is None:
        return []
    state_names = {p.name for p in ctx.state_fluents()}
    problems = []
    for name in dict.fromkeys(_assigned_names(section.body)):
        if name in state_names:
            problems.append(
                f"`{name}` is declared as a state-fluent but is assigned inside the "
                f"`non-fluents {{ ... }}` section. Initial values of state-fluents "
                f"belong in the `init-state {{ ... }}` section of the instance block."
            )
    return problems


def _rule_12_objects_form(ctx: _Context) -> list[str]:
    declared_types = _declared_types(ctx)
    entry = re.compile(r"^\s*([\w\-]+)\s*:\s*\{[^{}]*\}\s*$")
    problems = []
    for kind, sections in (
        ("non-fluents", ctx.non_fluents_sections),
        ("instance", ctx.instance_sections),
    ):
        section = _section(sections, "objects")
        if section is None:
            continue
        for statement in _statements(section.body):
            match = entry.match(statement)
            if match is None:
                problems.append(
                    f"The `objects` section of the {kind} block contains "
                    f"`{statement.strip()[:60]}`, which is not a valid object "
                    f"declaration. Each entry must have the form "
                    f"`<type> : {{ object1, object2 }};`, where `<type>` is a type "
                    f"declared in the domain's `types` section."
                )
            elif declared_types and match.group(1) not in declared_types:
                problems.append(
                    f"The `objects` section of the {kind} block declares objects for "
                    f"`{match.group(1)}`, which is not a type declared in the domain's "
                    f"`types` section (declared types: "
                    f"{', '.join(sorted(declared_types))}). List every object under its "
                    f"type: `<type> : {{ object1, object2 }};` -- objects are not types."
                )
    return problems


def _declared_types(ctx: _Context) -> set[str]:
    section = _section(ctx.domain_sections, "types")
    if section is None:
        return set()
    names = set()
    for statement in _statements(section.body):
        match = re.match(r"([\w\-]+)\s*:", statement.strip())
        if match:
            names.add(match.group(1))
    return names


def _rule_13_empty_termination(ctx: _Context) -> list[str]:
    section = _section(ctx.domain_sections, "termination")
    if section is not None and not section.body.strip():
        return [
            "The `termination { };` section is empty. Either give it a real "
            "termination condition, or remove the section entirely -- an empty one "
            "says nothing about when an episode ends."
        ]
    return []


def _rule_14_state_invariants_present(ctx: _Context) -> list[str]:
    if _section(ctx.domain_sections, "state-invariants") is None:
        return [
            "The domain has no `state-invariants` section. Without bounds such as "
            "`forall_{?x : type} [ f(?x) >= 0 ];` pyRDDLGym cannot derive box "
            "constraints and every state variable gets the range (-inf, +inf)."
        ]
    return []


RULES: dict[int, Callable[[_Context], list[str]]] = {
    1: _rule_01_non_fluents_declares_domain,
    2: _rule_02_instance_declares_links,
    3: _rule_03_distinct_non_fluents_name,
    4: _rule_04_section_semicolons,
    5: _rule_05_domain_section_order,
    6: _rule_06_aggregation_wrapping,
    7: _rule_07_no_prime_on_rhs,
    8: _rule_08_prime_placement,
    9: _rule_09_state_fluent_has_cpf,
    10: _rule_10_if_parentheses,
    11: _rule_11_state_fluent_in_non_fluents,
    12: _rule_12_objects_form,
    13: _rule_13_empty_termination,
    14: _rule_14_state_invariants_present,
}


def lint(blocks: Blocks) -> LintReport:
    ctx = _Context.build(blocks)
    report = LintReport()
    for number, rule in RULES.items():
        severity = RULE_SEVERITY[number]
        for message in rule(ctx):
            problem = Problem(rule=number, severity=severity, message=message)
            if severity == ERROR:
                report.errors.append(problem)
            else:
                report.warnings.append(problem)
    return report
