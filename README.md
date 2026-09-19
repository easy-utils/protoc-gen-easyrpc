# protoc-gen-easyrpc

The **eight easy-rpc code generators** as one standard protoc/buf plugin
package: `ts`, `go`, `rust`, `python`, `csharp`, `dart`, `swift`, `kotlin`.

They emit only the *client + server handler glue* (MethodSpecs, typed calls,
frame/codec handling); protobuf **messages** come from the usual generators
(`protoc-gen-es`, `protoc-gen-go`, prost, `protoc-gen-pbandk`, …).

## Why one package

Historically ts/go/rust were native binaries in separate repos and the other
five were Python scripts copied into each runtime repo (`tool/gen.py`). That
meant two layouts, duplicated descriptor boilerplate, a stale duplicate Python
plugin, and — worse — **non-standard configuration via `EASYRPC_*` env vars**
(`opt:` in `buf.gen.yaml` was silently ignored).

This packages all eight as plain Python protoc plugins sharing one core. The
protoc contract is honored properly:

* binary `CodeGeneratorRequest` on stdin → `CodeGeneratorResponse` on stdout;
* `file_to_generate` respected;
* `FEATURE_PROTO3_OPTIONAL` declared;
* configuration via **`request.parameter`** (buf `opt:` / `protoc --<lang>_opt=`),
  not environment variables.

## Install

```bash
pip install git+https://github.com/easy-utils/protoc-gen-easyrpc@v3.0.0
# or, from a checkout:
pip install -e .
```

This puts eight `protoc-gen-easyrpc-<lang>` console scripts on `PATH`.

## Use

`buf.gen.yaml` (buf v2). Because these are not published to the BSR, reference
them as `local:` plugins — either by name (installed) or as a **git array**
(no pre-install; buf fetches and runs via `uv`/`uvx`):

```yaml
version: v2
plugins:
  # installed entry point
  - local: protoc-gen-easyrpc-ts
    out: src/gen
  # or, self-contained from a git tag (array invocation):
  - local:
      - uvx
      - --from
      - git+https://github.com/easy-utils/protoc-gen-easyrpc@v3.0.0
      - protoc-gen-easyrpc-go
    out: gen/go
```

Plain `protoc`:

```bash
protoc -I proto \
  --plugin=protoc-gen-easyrpc-ts=/path/to/bin/protoc-gen-easyrpc-ts \
  --easyrpc-ts_out=gen/ts \
  pkg/v1/service.proto
```

## Options (`opt:` / `request.parameter`)

| lang | key | meaning | default |
|------|-----|---------|---------|
| python | `lib` | cross-package library root for the message import | `easyrpc` |
| kotlin | `pkg` | emitted `package` for the client | `easyrpc` |
| kotlin | `msg_pkg` | package of the pbandk messages | proto `java_package` / package |
| csharp | `ns` | emitted C# namespace | `EasyRpc` |
| csharp | `msg_ns` | namespace of the protobuf messages | proto `csharp_namespace` / package |
| dart | `pb_root` | import root of the generated `*_pb.dart` | `package:easy_rpc/src` |
| swift | `msg_prefix` | Swift protobuf type prefix | Pascal-joined package |
| ts / go / rust | — | no options (self-describing output) | |

Example: `--easyrpc-kotlin_opt=pkg=agentsdk,msg_pkg=agent.v1`.

## Layout

```
easyrpc_gen/
  core.py       # request/response, file_to_generate, parameter parsing, resolve()
  ts.py go.py rust.py python.py csharp.py dart.py swift.py kotlin.py
bin/            # the eight protoc-gen-easyrpc-<lang> entry scripts
tests/run.py    # golden: every lang must reproduce tests/golden/<lang>
```

## Tests

```bash
python3 tests/run.py            # generate + byte-diff against tests/golden
python3 tests/run.py --update   # refresh the fixtures
```

`EASYRPC_PROTO_ROOT` selects the proto root (defaults to the easy-rpc spec
checkout).
