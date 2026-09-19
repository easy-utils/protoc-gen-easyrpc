"""Console-script wrappers for the eight easy-rpc plugins.

Each `<lang>` function is the entry point installed as
`protoc-gen-easyrpc-<lang>` (see pyproject.toml `[project.scripts]`).
"""
from __future__ import annotations

from . import core


def _run(module):
    core.run(module)


def ts() -> None:
    from . import ts as m
    _run(m)


def go() -> None:
    from . import go as m
    _run(m)


def rust() -> None:
    from . import rust as m
    _run(m)


def python() -> None:
    from . import python as m
    _run(m)


def csharp() -> None:
    from . import csharp as m
    _run(m)


def dart() -> None:
    from . import dart as m
    _run(m)


def swift() -> None:
    from . import swift as m
    _run(m)


def kotlin() -> None:
    from . import kotlin as m
    _run(m)
