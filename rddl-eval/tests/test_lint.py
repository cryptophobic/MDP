"""Lint rules against one fixture per rule.

Nothing here touches the network or pyRDDLGym -- these are regexes over text
and the whole file should run in about a second.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rddl_eval.extract import ExtractError, extract_blocks
from rddl_eval.lint import ERROR, WARNING, RULE_SEVERITY, lint

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"


def _fired(text: str) -> tuple[set[int], set[int]]:
    report = lint(extract_blocks(text))
    return {p.rule for p in report.errors}, {p.rule for p in report.warnings}


def _invalid_fixtures() -> list[Path]:
    return sorted(INVALID.glob("*.rddl"))


def _rule_number(path: Path) -> int:
    return int(re.match(r"(\d+)_", path.name).group(1))


def test_every_rule_has_a_fixture():
    covered = {_rule_number(path) for path in _invalid_fixtures()}
    assert covered == set(RULE_SEVERITY), "each lint rule needs its own fixture"


@pytest.mark.parametrize("path", sorted(VALID.glob("*.rddl")), ids=lambda p: p.name)
def test_valid_fixture_is_silent(path: Path):
    errors, warnings = _fired(path.read_text())
    assert errors == set()
    assert warnings == set()


@pytest.mark.parametrize("path", _invalid_fixtures(), ids=lambda p: p.stem)
def test_fixture_is_caught_by_its_own_rule(path: Path):
    """A broken fixture fires its rule -- and only its rule.

    Exclusivity matters as much as detection: a rule that also trips its
    neighbours would put noise into the repair message sent to the model.
    """
    rule = _rule_number(path)
    errors, warnings = _fired(path.read_text())
    fired = errors if RULE_SEVERITY[rule] == ERROR else warnings
    other = warnings if RULE_SEVERITY[rule] == ERROR else errors

    assert rule in fired, f"rule {rule} did not fire on its own fixture"
    assert fired == {rule}, f"fixture for rule {rule} also fired {fired - {rule}}"
    assert other == set(), f"fixture for rule {rule} fired {other} at the other severity"


def test_rule_14_is_the_only_warning():
    assert [n for n, s in RULE_SEVERITY.items() if s == WARNING] == [14]


def test_lint_report_ok_only_without_errors():
    report = lint(extract_blocks((INVALID / "14_missing_state_invariants.rddl").read_text()))
    assert report.ok
    assert len(report.warnings) == 1


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------

VALID_TEXT = (VALID / "shelves.rddl").read_text()


def _blocks_of(text: str):
    parts = {}
    for kind, header in (
        ("domain", "domain shelves {"),
        ("non-fluents", "non-fluents shelves_nf {"),
        ("instance", "instance shelves_inst {"),
    ):
        start = VALID_TEXT.index(header)
        end = VALID_TEXT.index("\n}", start) + 2
        parts[kind] = VALID_TEXT[start:end]
    return parts


PARTS = _blocks_of(VALID_TEXT)


def test_extract_from_code_fences():
    fenced = "Here you go:\n\n" + "\n\n".join(
        f"```rddl\n{PARTS[kind]}\n```" for kind in ("domain", "non-fluents", "instance")
    )
    blocks = extract_blocks(fenced)
    assert blocks.domain.name == "shelves"
    assert blocks.non_fluents.name == "shelves_nf"
    assert blocks.instance.name == "shelves_inst"
    assert lint(blocks).ok


def test_extract_from_bare_text():
    blocks = extract_blocks("Sure. " + VALID_TEXT)
    assert blocks.domain.name == "shelves"
    assert lint(blocks).ok


def test_extract_ignores_block_order():
    reordered = "\n\n".join(PARTS[kind] for kind in ("instance", "non-fluents", "domain"))
    blocks = extract_blocks(reordered)
    assert blocks.domain.name == "shelves"
    assert blocks.instance.name == "shelves_inst"


def test_instance_file_joins_non_fluents_and_instance():
    blocks = extract_blocks(VALID_TEXT)
    instance_file = blocks.instance_file()
    assert "non-fluents shelves_nf" in instance_file
    assert "instance shelves_inst" in instance_file
    assert "domain shelves {" not in instance_file
    assert "domain shelves {" in blocks.domain_file()


@pytest.mark.parametrize("missing", ["domain", "non-fluents", "instance"])
def test_missing_block_is_an_extract_error(missing: str):
    text = "\n\n".join(part for kind, part in PARTS.items() if kind != missing)
    with pytest.raises(ExtractError) as excinfo:
        extract_blocks(text)
    assert missing in excinfo.value.problems[0]


def test_inner_non_fluents_section_is_not_mistaken_for_a_block():
    blocks = extract_blocks(VALID_TEXT)
    assert blocks.non_fluents.name == "shelves_nf"
    assert "objects {" in blocks.non_fluents.text


def test_comments_do_not_hide_or_create_findings():
    commented = VALID_TEXT.replace(
        "    types {", "    // domain foo { if x then\n    types {"
    )
    errors, warnings = _fired(commented)
    assert errors == set()
    assert warnings == set()


# --------------------------------------------------------------------------
# targeted rule behaviour that the fixtures cannot express on their own
# --------------------------------------------------------------------------


def _domain_with_reward(reward: str) -> str:
    return VALID_TEXT.replace(
        "    reward = -(sum_{?s : shelf} [ PENALTY * (if (stock(?s) == 0) then 1 else 0) ]);",
        f"    reward = {reward};",
    )


@pytest.mark.parametrize(
    "reward",
    [
        "-(sum_{?s : shelf} [ PENALTY ])",
        "sum_{?s : shelf} [ PENALTY ]",
        "(sum_{?s : shelf} [ PENALTY ]) - 10",
        "10 - (sum_{?s : shelf} [ PENALTY ])",
        "(if (exists_{?s : shelf} [ stock(?s) == 0 ]) then -1 else 0)",
    ],
)
def test_rule_6_accepts_closed_off_aggregations(reward: str):
    """An aggregation nothing follows is fine; only a trailing operand is not."""
    errors, _ = _fired(_domain_with_reward(reward))
    assert 6 not in errors


@pytest.mark.parametrize(
    "reward",
    [
        "sum_{?s : shelf} [ PENALTY ] - 10",
        "(sum_{?s : shelf} [ PENALTY ] - 10)",
        "2 * (sum_{?s : shelf} [ PENALTY ] + 1)",
        "sum_{?s : shelf} PENALTY",
    ],
)
def test_rule_6_catches_swallowed_operands(reward: str):
    errors, _ = _fired(_domain_with_reward(reward))
    assert 6 in errors


def test_rule_4_catches_semicolon_after_a_top_level_block():
    errors, _ = _fired(VALID_TEXT.replace("};\n}\n\nnon-fluents", "};\n};\n\nnon-fluents"))
    assert errors == {4}


def test_rule_5_reports_the_order_it_found():
    text = (INVALID / "05_section_order.rddl").read_text()
    report = lint(extract_blocks(text))
    message = report.errors[0].message
    assert "reward, cpfs" in message


def test_rule_9_names_the_fluent_without_a_cpf():
    text = (INVALID / "09_state_fluent_without_cpf.rddl").read_text()
    report = lint(extract_blocks(text))
    assert "spoilage" in report.errors[0].message
    assert "stock" not in report.errors[0].message.replace("restock", "")


def test_messages_are_non_empty_and_actionable():
    for path in _invalid_fixtures():
        report = lint(extract_blocks(path.read_text()))
        for problem in report.errors + report.warnings:
            assert len(problem.message) > 40, path.name
            assert problem.message.endswith((".", "`.")), path.name
