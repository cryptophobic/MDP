"""Hand the extracted blocks to pyRDDLGym and see whether they compile."""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import warnings
from dataclasses import dataclass

from .extract import Blocks


@dataclass
class ParseResult:
    env: object | None
    error: str | None
    #: Where the two files were written, kept for the run log.
    domain_path: str | None = None
    instance_path: str | None = None

    @property
    def ok(self) -> bool:
        return self.env is not None


@contextlib.contextmanager
def _quiet():
    """pyRDDLGym chatters on stdout and warns about lexer tables; we only
    want the exception."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield buffer


def write_files(blocks: Blocks, directory: str) -> tuple[str, str]:
    domain_path = os.path.join(directory, "domain.rddl")
    instance_path = os.path.join(directory, "instance.rddl")
    with open(domain_path, "w", encoding="utf-8") as handle:
        handle.write(blocks.domain_file())
    with open(instance_path, "w", encoding="utf-8") as handle:
        handle.write(blocks.instance_file())
    return domain_path, instance_path


def parse_blocks(blocks: Blocks, keep_dir: str | None = None) -> ParseResult:
    """Compile *blocks* into an environment.

    The two ``.rddl`` files are written to *keep_dir* when given (handy when a
    run needs to be reproduced by hand), otherwise to a temporary directory.
    pyRDDLGym reads both files eagerly inside ``make``, so the directory can go
    away afterwards.
    """
    import pyRDDLGym

    with contextlib.ExitStack() as stack:
        if keep_dir is None:
            directory = stack.enter_context(tempfile.TemporaryDirectory(prefix="rddl-eval-"))
        else:
            os.makedirs(keep_dir, exist_ok=True)
            directory = keep_dir
        domain_path, instance_path = write_files(blocks, directory)
        try:
            with _quiet():
                env = pyRDDLGym.make(domain=domain_path, instance=instance_path)
        except Exception as exc:  # noqa: BLE001 - any compiler failure is a result
            return ParseResult(
                env=None,
                error=f"{type(exc).__name__}: {exc}",
                domain_path=domain_path,
                instance_path=instance_path,
            )
        return ParseResult(
            env=env, error=None, domain_path=domain_path, instance_path=instance_path
        )
