# rddl-eval

Measures how well a local LLM (Gemma 4 12B QAT, served by LM Studio) turns a
plain-English task description into a working RDDL model.

Every generation is pushed through five levels of validation:

```
extract -> lint -> parse -> simulate -> semantic
```

The run stops at the first level that reports problems, and *which* level
stopped it is the measurement. Three numbers come out: how often the model is
right first time, how often it is right after one round of being told what was
wrong, and where the first attempt tends to break.

This is a research instrument. It is meant to be read and edited, not
configured.

## Setup

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

The RDDL specification is not in the repository -- it goes into the system
prompt at runtime and is fetched separately:

```bash
mkdir -p spec
curl -o spec/rddl.rst \
  https://raw.githubusercontent.com/pyrddlgym-project/pyRDDLGym/main/docs/rddl.rst
```

Then start LM Studio, load the model, and make sure the server tab shows
`Status: Running`.

## Running

```bash
python -m rddl_eval \
    --task tasks/shelves.txt \
    --spec spec/rddl.rst \
    --runs 5 \
    --repairs 1 \
    --temperature 0.7
```

Other flags: `--endpoint` (default `http://localhost:1234/v1/chat/completions`,
also read from `$LMSTUDIO_URL`), `--model` (default `google/gemma-4-12b-qat`),
`--timeout` (default 900s -- a 12B model over a long prompt is slow),
`--steps` (rollout length), `--prompt` (prompt template), `--out` (default
`results/`).

Output is one line per run plus a summary:

```
run 1/3  PASS             first attempt: lint      attempts: 2  -> results/...json
run 2/3  PASS             first attempt: pass      attempts: 1  -> results/...json
run 3/3  FAIL at extract  first attempt: extract   attempts: 2  -> results/...json

summary
-------
runs                  3
first-pass valid      1/3 (33%)
valid after repair    2/3 (67%)
first failure by level:
  extract    1/3 (33%)
  lint       1/3 (33%)
  ...
```

Each run is also written to `results/<timestamp>_<task>.json`: the whole
dialogue, every intermediate answer, and the problems found at each level.
Without that file a failed run cannot be reconstructed afterwards.

## The system prompt

`system_prompt.txt` is a template with a single `{spec}` placeholder, filled in
by `str.replace` (never `format` -- the prompt is full of RDDL braces). It
covers the output format and the block structure only. It deliberately does
*not* list the lint rules: telling the model in advance about the mistakes we
are counting would measure the prompt rather than the model.

## Tests

```bash
pytest                      # everything; no network, no LM Studio needed
pytest -m "not rddlgym"     # lint and extraction only, no compiler
pytest tests/test_lint.py   # one fixture per lint rule
```

`fixtures/valid/shelves.rddl` is a model that compiles, simulates and passes the
semantic checks. Every file in `fixtures/invalid/` is that same model with
exactly one defect introduced, named after the rule that should catch it. The
lint tests assert both directions: the rule fires on its own fixture, and no
*other* rule fires with it -- a noisy rule would put misleading instructions
into the repair message.

## Lint rules

The rule numbers match `instructions.md`. The last column is what pyRDDLGym 2.7
does with the same defect, measured rather than assumed:

| # | Catches | Severity | pyRDDLGym 2.7 |
|---|---------|----------|---------------|
| 1 | `non-fluents` block without `domain = ...;` | error | accepts |
| 2 | `instance` block without `domain = ...;` / `non-fluents = ...;` | error | accepts |
| 3 | non-fluents block named after the domain | error | accepts |
| 4 | section closing with `}` instead of `};` (and `};` after a top-level block) | error | `RDDLParseError` |
| 5 | domain sections out of canonical order | error | `RDDLParseError` |
| 6 | aggregation that swallows the operand after it | error | accepts, wrong result |
| 7 | primed variable on the right-hand side of a CPF | error | `RDDLInvalidDependencyInCPFError` |
| 8 | `f(?x)'` instead of `f'(?x)` | error | `RDDLMissingCPFDefinitionError` |
| 9 | state-fluent with no CPF | error | `RDDLMissingCPFDefinitionError` |
| 10 | `if <cond> then` without parentheses | error | `RDDLParseError` |
| 11 | state-fluent assigned in the `non-fluents { }` section | error | `RDDLUndefinedVariableError` |
| 12 | malformed `objects` entry, or an object declared as its own type | error | `RDDLInvalidObjectError` |
| 13 | empty `termination { };` | error | accepts |
| 14 | no `state-invariants` section | warning | accepts, see below |

Rules 1, 2, 3 and 13 are conventions this harness enforces, not things the
compiler rejects: they are counted as `lint` failures even though such a model
would have compiled. That is a deliberate choice inherited from the brief, and
it does shift the numbers -- if you would rather measure only what pyRDDLGym
itself rejects, demote them in `RULE_SEVERITY` at the top of `rddl_eval/lint.py`
and they become warnings without any other change.

Rule 14 is a warning because the domain still runs; it just loses its box
constraints. Measured on the shelves fixture: with the invariants,
`stock` has space `Discrete(11)`; without them, `Discrete(4294967296, start=-2147483648)`.

## Where this deviates from the brief

**Rule 6 is tested differently than specified.** The brief says to look at the
character immediately *before* the aggregator. Measured against pyRDDLGym 2.7
on a three-shelf instance, that heuristic is wrong in both directions:

| expression | value | note |
|---|---|---|
| `sum_{?s : shelf} [ 1 ] - 10` | -27 | the `- 10` is pulled inside the sum |
| `(sum_{?s : shelf} [ 1 ] - 10)` | -27 | still wrong, though a `(` precedes the aggregator |
| `(sum_{?s : shelf} [ 1 ]) - 10` | -7 | correct |
| `reward = sum_{?s : shelf} [ 1 ];` | 3 | correct, though no bracket precedes it |

An aggregation binds everything to its right, so what matters is what *follows*
its body, not what precedes it. Rule 6 therefore fires when a binary operator
follows the aggregation's closing bracket, or when the body is not bracketed at
all. Checking the preceding character instead would have flagged correct code
and missed the second line above -- and pyRDDLGym never complains about any of
these, so lint is the only place they can be caught.

**pyRDDLGym API.** Verified against the installed version (2.7, Python 3.14)
rather than assumed; the brief turned out to be right on every point:

- `pyRDDLGym.make(domain=..., instance=...) -> RDDLEnv`
- `RandomAgent(action_space, num_actions=1, seed=None)` -- takes `seed`
- `RandomAgent.sample_action(state=None)` -- takes the state, optionally
- `env.step(action) -> (obs, reward, terminated, truncated, info)`, the
  five-value Gymnasium signature
- `env.reset(seed=None) -> (obs, info)`; `env.horizon` and
  `env.max_allowed_actions` are the horizon and the action budget from the
  instance

`num_actions=env.max_allowed_actions` matters: with the instance's
`max-nondef-actions = 1`, a random agent that ignored it would violate the
action count on the first step.

## Layout

```
rddl_eval/
  extract.py    three RDDL blocks out of a chat reply -> two files
  lint.py       the rules above, as regexes over the block text
  parse.py      pyRDDLGym.make in a try/except
  simulate.py   random rollout; crashes, NaN, constant reward
  semantic.py   per-task checks, keyed by task file name
  llm.py        LM Studio client (no retries: fail loudly)
  pipeline.py   the cascade and the repair loop
  cli.py        arguments, per-run JSON, summary
tasks/          task descriptions sent to the model
fixtures/       valid and deliberately broken models for the tests
spec/rddl.rst   downloaded separately, see Setup
results/        per-run JSON logs (gitignored)
```

Adding a task means dropping a `.txt` into `tasks/` and, if it needs semantic
checks, registering them in `SEMANTIC_CHECKS` under the same file name. Because
the checks look for specific fluent names, the task text states those names
explicitly. `duel` is registered as a no-op stub.


python -m rddl_eval \
    --task tasks/shelves.txt \
    --spec spec/rddl.rst \
    --runs 5 \
    --repairs 1 \
    --temperature 0.7 \
    --endpoint http://192.168.1.212:1234/v1/chat/completions