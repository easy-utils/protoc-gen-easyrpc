#!/usr/bin/env python3
"""Shared core for every protoc-gen-easyrpc-<lang> plugin.

One implementation language (Python), one descriptor front-end, eight
renderers. Each language module exposes `render(file, params) ->
list[tuple[name, content]]`; this core owns the protoc plugin contract:

  * read a binary CodeGeneratorRequest from stdin
  * honor `file_to_generate`
  * parse configuration from `request.parameter` (buf `opt:` / protoc
    `--<lang>_opt=`) — NOT environment variables
  * write a CodeGeneratorResponse declaring FEATURE_PROTO3_OPTIONAL

Usage (installed console scripts): the eight entry points in `bin/` call
`easyrpc_gen.core.run(<module>)`.
"""
from __future__ import annotations

import sys
from typing import Callable

from google.protobuf.compiler import plugin_pb2 as plugin


def parse_params(parameter: str) -> dict[str, str]:
    """Parse a protoc/buf `parameter` string into a dict.

    Accepts the conventional comma-separated `k=v` form (e.g.
    `pkg=agentsdk,msg_pkg=agent.v1`). Bare tokens (no `=`) are ignored so a
    stray `paths=source_relative`-style flag never crashes a renderer.
    """
    out: dict[str, str] = {}
    for part in (parameter or "").split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def last_type(t: str) -> str:
    """`pkg.Message` -> `Message` (drops the package qualifier)."""
    return t.rsplit(".", 1)[-1] if t else ""


def camel(s: str) -> str:
    """`GetThing` -> `getThing`."""
    return s[:1].lower() + s[1:] if s else s


def pascal(s: str) -> str:
    """`java_package` / `agent.v1` segments -> `JavaPackage` / `Agent`."""
    return "".join(x[:1].upper() + x[1:] for x in s.replace("-", "_").split("_"))


class Method:
    __slots__ = ("service", "name", "path", "client_stream", "server_stream", "input", "output")

    def __init__(self, service: str, name: str, path: str, client_stream: bool,
                 server_stream: bool, input_type: str, output_type: str) -> None:
        self.service = service
        self.name = name
        self.path = path
        self.client_stream = client_stream
        self.server_stream = server_stream
        self.input = input_type
        self.output = output_type


def resolve(file: plugin.FileDescriptorProto) -> list[Method]:
    """Resolve every rpc in a file to a Method (gRPC-style path, POST-only)."""
    pkg = file.package or ""
    out: list[Method] = []
    for svc in file.service:
        for m in svc.method:
            out.append(Method(
                service=f"{pkg}.{svc.name}",
                name=m.name or "",
                path=f"/{pkg}.{svc.name}/{m.name}",
                client_stream=bool(m.client_streaming),
                server_stream=bool(m.server_streaming),
                input_type=last_type(m.input_type),
                output_type=last_type(m.output_type),
            ))
    return out


def service_names(methods: list[Method]) -> list[str]:
    """Distinct service names, sorted (stable multi-service emission)."""
    return sorted({m.service.rsplit(".", 1)[-1] for m in methods})


def methods_of(methods: list[Method], short_service: str) -> list[Method]:
    return [m for m in methods if m.service.rsplit(".", 1)[-1] == short_service]


def render_files(file: plugin.FileDescriptorProto, render_file: Callable) -> list:
    """Invoke a renderer for one file and return response File entries."""
    methods = resolve(file)
    if not methods:
        return []
    return render_file(file, methods)


def run(renderer) -> None:
    """Entry point for a language renderer module.

    `renderer` is a module exposing `render(file, methods, params) -> list of
    (output_name, content)`. The core handles request/response + params.
    """
    data = sys.stdin.buffer.read()
    req = plugin.CodeGeneratorRequest.FromString(data)
    params = parse_params(req.parameter)
    files = []
    for f in req.proto_file:
        if f.name not in req.file_to_generate:
            continue
        methods = resolve(f)
        if not methods:
            continue
        for name, content in renderer.render(f, methods, params):
            files.append(plugin.CodeGeneratorResponse.File(name=name, content=content))
    resp = plugin.CodeGeneratorResponse(file=files)
    resp.supported_features = plugin.CodeGeneratorResponse.FEATURE_PROTO3_OPTIONAL
    sys.stdout.buffer.write(resp.SerializeToString())
