# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A research harness that measures how well a local LLM (Gemma 4 12B QAT via LM
Studio) turns a plain-English task description into a working RDDL model. It is
an instrument, not a product — transparency and ease of modification beat
generality.

`instructions.md` is the original brief (in Ukrainian). `README.md` documents
the built system, including a rule-by-rule table of what pyRDDLGym actually does
with each defect and where the implementation deviates from the brief.

## Commands

```bash
.venv-win/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; see Environment

pytest                      # 68 tests pass on Windows, ~0.5s, no network and no LM Studio needed
pytest -m "not rddlgym"     # skip everything that needs the compiler
pytest tests/test_lint.py::test_fixture_is_caught_by_its_own_rule -k 06   # single rule

python -m rddl_eval --task tasks/shelves.txt --spec spec/rddl.rst \
    --runs 5 --repairs 1 --temperature 0.7 \
    [--endpoint URL] [--model NAME] [--steps N] [--out results/]
```

`spec/rddl.rst` is gitignored and fetched separately (curl command in the
README); without it the CLI exits with a pointer to that section.

## Environment (verified on this machine, 2026-08-18)

The project root is the nested `rddl-eval/` directory, not its parent. This is
not a git checkout — it was unpacked from a macOS zip (`__MACOSX/` sibling), so
there is no history to consult and `.gitignore` is advisory only.

**The checked-in `.venv/` is a macOS virtualenv** (`bin/` layout, `pyvenv.cfg`
points at `/Library/Frameworks/...`, Python 3.14). It cannot run on Windows —
`.venv/bin/pip` from the README does not exist here. A working Windows
environment is `.venv-win/`, created with the system launcher:

```bash
py -m venv .venv-win                                # py is Python 3.13.1
.venv-win/Scripts/python.exe -m pip install -e ".[dev]"
```

Confirmed: pyRDDLGym 2.7 installs cleanly on 3.13 and all 68 tests pass in
~3s. Nothing in `rddl_eval/` is POSIX-specific — every `open()` passes
`encoding="utf-8"`, paths go through `os.path.join`/`tempfile`, and the one
locale-sensitive spot (tests calling `Path.read_text()` with no encoding, under
a cp1252 default) is safe because the fixtures and tasks are pure ASCII. Keep
them that way, and keep every file LF: `extract._FENCE` requires `\n`
immediately after the fence, so CRLF fixtures would silently fall back to
raw-reply extraction.

`main.py` is leftover PyCharm boilerplate with no relation to the package.

## LM Studio context length

The system prompt inlines the whole of `spec/rddl.rst`: ~42k characters, which
LM Studio counts as **~11.3k tokens before the task text is added**. A model
loaded at the 8192 default fails the very first call with
`exceed_context_size_error` — not a bug in the harness, and the run aborts with
exit 1 rather than being recorded as a failed generation.

Check the loaded context before blaming anything else:

```bash
lms ps      # the CONTEXT column must be >= 32768, not 8192
lms load google/gemma-4-12b-qat --context-length 32768
```

32k is the figure the README assumes. `--repairs 1` re-sends the whole dialogue
plus two full RDDL models, so the ceiling is roughly double the first turn.

## Architecture

The core is a staged cascade in `pipeline.py`:

```
extract → lint → parse → simulate → semantic
```

It stops at the first level that reports problems, and the level that stopped it
*is* the measurement — so levels must not absorb each other's failures. Adding a
check means deciding which level owns it.

- **extract** — three blocks out of a chat reply, recognised by leading keyword
  rather than position, fenced or bare. pyRDDLGym wants *two* files, so
  `non-fluents` + `instance` are concatenated into `instance.rddl`.
- **lint** — regexes over the block text, before the compiler. It exists because
  pyRDDLGym reports token positions, which are useless as repair feedback; every
  message is written in English to be pasted verbatim into the repair turn.
  Errors stop the cascade, warnings ride along and surface in the run log.
- **parse / simulate / semantic** — `pyRDDLGym.make` in a try/except; a random
  rollout that catches crashes, NaN and constant reward; then per-task checks
  from the `SEMANTIC_CHECKS` registry keyed by task file stem.

On failure `run_once` appends `(assistant: previous answer, user: feedback)` and
re-prompts, up to `--repairs` rounds. Every run is written to
`results/<timestamp>_<task>.json` with the full dialogue.

## Things that will bite

- **The system prompt is assembled with `str.replace`, never `format` or an
  f-string** — the template and the spec are full of RDDL braces. There is a
  test for this.
- **Aggregations swallow whatever follows them.** `sum_{?s : shelf} [ 1 ] - 10`
  over three objects is -27, not -7, and pyRDDLGym compiles it silently. Lint
  rule 6 is the only thing that catches it, which is why it tests what *follows*
  the aggregation body rather than what precedes it (the brief said otherwise;
  the README table shows the measurements).
- **Lint rules 1, 2, 3 and 13 are conventions, not compiler errors** —
  pyRDDLGym 2.7 accepts those defects. They still count as `lint` failures,
  which shifts the numbers; flip them in `RULE_SEVERITY` in `lint.py` to measure
  only what the compiler rejects.
- **Semantic checks depend on fluent names**, so the task files in `tasks/` state
  the required names explicitly. A renamed fluent is a semantic failure by
  design.
- `semantic.steps_for` can raise the rollout length above `--steps`: the shelves
  checks need 300 steps to be meaningful.
- Never invent RDDL syntax to add a rule. Verify against the installed compiler
  first — a wrong rule poisons the repair loop, which is worse than no rule.
- The client never retries on network errors, on purpose: a flaky connection
  should fail loudly rather than become a failed generation in the statistics.

## Fixtures are the test contract

`fixtures/valid/shelves.rddl` compiles, simulates and passes the semantic
checks. Each file in `fixtures/invalid/` is that same model with exactly one
defect, named after the rule that must catch it. The parametrised test asserts
both that the rule fires *and* that no other rule fires with it — keep that
property when adding rules, since a noisy rule sends misleading instructions to
the model.
