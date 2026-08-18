"""Command line entry point: run a task N times and report the three numbers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime

from .llm import DEFAULT_MODEL, DEFAULT_TIMEOUT, LLMError, LMStudioClient, default_endpoint
from .pipeline import LEVELS, RunResult, run_once
from .simulate import DEFAULT_STEPS

DEFAULT_PROMPT = "system_prompt.txt"


def build_system_prompt(prompt_path: str, spec_path: str) -> str:
    """Substitute the RDDL specification into the prompt template.

    ``str.replace``, never ``format``/f-strings: the prompt is full of RDDL
    braces and any formatting call would choke on them.
    """
    with open(prompt_path, encoding="utf-8") as handle:
        template = handle.read()
    with open(spec_path, encoding="utf-8") as handle:
        spec = handle.read()
    if "{spec}" not in template:
        raise SystemExit(
            f"{prompt_path} has no {{spec}} placeholder -- the specification would "
            f"never reach the model."
        )
    return template.replace("{spec}", spec)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m rddl_eval",
        description="Measure how well a local LLM generates valid RDDL.",
    )
    parser.add_argument("--task", required=True, help="path to a task description")
    parser.add_argument("--spec", default="spec/rddl.rst", help="path to the RDDL specification")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="system prompt template")
    parser.add_argument("--runs", type=int, default=5, help="independent generations")
    parser.add_argument("--repairs", type=int, default=1, help="repair rounds per run")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--endpoint", default=None, help="LM Studio chat completions URL")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="simulation steps")
    parser.add_argument("--out", default="results", help="directory for per-run JSON logs")
    return parser.parse_args(argv)


def _save(result: RunResult, out_dir: str, task: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    path = os.path.join(out_dir, f"{stamp}_{task}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, ensure_ascii=False, indent=2)
    return path


def _summarise(results: list[RunResult]) -> str:
    total = len(results)
    if not total:
        return "no runs"
    first_pass = sum(r.passed_first_try for r in results)
    after_repair = sum(r.passed for r in results)
    failures = Counter(r.first_failure_level for r in results if r.first_failure_level)

    lines = [
        "",
        "summary",
        "-------",
        f"runs                  {total}",
        f"first-pass valid      {first_pass}/{total} ({first_pass / total:.0%})",
        f"valid after repair    {after_repair}/{total} ({after_repair / total:.0%})",
        "first failure by level:",
    ]
    for level in LEVELS:
        count = failures.get(level, 0)
        lines.append(f"  {level:<10} {count}/{total} ({count / total:.0%})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    task_name = os.path.splitext(os.path.basename(args.task))[0]

    try:
        system_prompt = build_system_prompt(args.prompt, args.spec)
        with open(args.task, encoding="utf-8") as handle:
            task_text = handle.read()
    except FileNotFoundError as exc:
        print(f"error: {exc.filename} not found", file=sys.stderr)
        if exc.filename and "rddl.rst" in str(exc.filename):
            print(
                "the RDDL specification is not in the repository; see README.md for "
                "the download command",
                file=sys.stderr,
            )
        return 2

    client = LMStudioClient(
        endpoint=args.endpoint or default_endpoint(),
        model=args.model,
        timeout=args.timeout,
        temperature=args.temperature,
    )

    print(
        f"task {task_name}  model {args.model}  endpoint {client.endpoint}  "
        f"runs {args.runs}  repairs {args.repairs}  temperature {args.temperature}"
    )

    results: list[RunResult] = []
    for run in range(1, args.runs + 1):
        try:
            result = run_once(
                client=client,
                system_prompt=system_prompt,
                task_text=task_text,
                task=task_name,
                repairs=args.repairs,
                temperature=args.temperature,
                steps=args.steps,
            )
        except LLMError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        results.append(result)
        path = _save(result, args.out, task_name)
        verdict = "PASS" if result.passed else f"FAIL at {result.final_level}"
        first = result.first_failure_level or "pass"
        detail = "" if result.passed else f"  {result.attempts[-1].problems[0][:110]}"
        print(
            f"run {run}/{args.runs}  {verdict:<16} first attempt: {first:<9} "
            f"attempts: {len(result.attempts)}  -> {path}{detail}"
        )

    print(_summarise(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
