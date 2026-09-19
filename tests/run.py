#!/usr/bin/env python3
"""Golden tests: every plugin reproduces a committed reference byte-for-byte.

Fixtures live under `tests/golden/<lang>/` and were captured from the eight
historical generators (before they were unified). Regenerate with:

    python3 tests/run.py --update
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
FIXTURES = HERE / "golden"
PROTO_ROOT = Path(os.environ.get("EASYRPC_PROTO_ROOT", "/home/user/easy-utils/easy-rpc-spec/proto"))
PROTO_REL = "easyrpc/kitchensink/v1/kitchen.proto"
LANGS = ["ts", "go", "rust", "python", "csharp", "dart", "swift", "kotlin"]


def plugin(lang: str) -> Path:
    return REPO / "bin" / f"protoc-gen-easyrpc-{lang}"


def generate(lang: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "protoc", "-I", str(PROTO_ROOT),
        f"--plugin=protoc-gen-easyrpc-{lang}={plugin(lang)}",
        f"--easyrpc-{lang}_out={out}",
        PROTO_REL,
    ], check=True, capture_output=True)


def diff_tree(a: Path, b: Path) -> list[str]:
    problems = []
    files = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    files |= {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    for rel in sorted(files):
        pa, pb = a / rel, b / rel
        if not pa.exists():
            problems.append(f"missing {rel}")
        elif not pb.exists():
            problems.append(f"unexpected {rel}")
        elif pa.read_bytes() != pb.read_bytes():
            problems.append(f"differs {rel}")
    return problems


def main() -> int:
    update = "--update" in sys.argv
    rc = 0
    for lang in LANGS:
        out = Path(f"/tmp/easyrpc-golden-{lang}")
        subprocess.run(["rm", "-rf", str(out)])
        generate(lang, out)
        ref = FIXTURES / lang
        if update:
            subprocess.run(["rm", "-rf", str(ref)])
            subprocess.run(["cp", "-r", str(out), str(ref)], check=True)
            print(f"updated {ref}")
            continue
        if not ref.exists():
            print(f"SKIP {lang}: no fixture")
            continue
        problems = diff_tree(out, ref)
        if problems:
            rc = 1
            print(f"FAIL {lang}: {len(problems)} issue(s)")
            for p in problems[:10]:
                print(f"      {p}")
        else:
            print(f"ok   {lang}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
