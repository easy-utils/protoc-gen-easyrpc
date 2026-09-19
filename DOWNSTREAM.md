# Regenerating the agent SDK clients

The eight `agent-sdk-*` repos consume easy-rpc via these plugins. Messages come
from the usual generators; only the **client + handler glue** comes from
`protoc-gen-easyrpc-<lang>`. Most SDKs apply a small downstream rewrite to the
plugin output (import root / crate path), captured below so a regen is
reproducible.

Proto source of truth: `github.com/abcp-sdk/agent-proto` → `proto/agent/v1/agent.proto`.

## Recipes (`-I` = the proto root)

| SDK | plugin | `opt:` | downstream rewrite |
|-----|--------|--------|--------------------|
| agent-sdk-typescript | ts | — | none (the emitted `../../../protocol.js` resolves to the repo's `src/protocol.ts` shim, which re-exports `@easy-utils/easy-rpc`) |
| agent-sdk-go | go | — | none |
| agent-sdk-rust | rust | — | `s#crate::protocol::MethodSpec#easy_rpc::protocol::MethodSpec#g` |
| agent-sdk-python | python | `lib=agentsdk` | `s#^import agentsdk.agent.v1.agent_pb2 as m$#from . import agent_pb2 as m#` |
| agent-sdk-csharp | csharp | — | messages: prepend `Easyrpc.` to the `Agent.V1` namespace (`global::Agent.V1` → `global::Easyrpc.Agent.V1`) |
| agent-sdk-dart | dart | `pb_root=package:agent_client_sdk/src/gen` | none |
| agent-sdk-swift | swift | `msg_prefix=Agent_V1` | none |
| agent-sdk-kotlin | kotlin | `pkg=agentsdk,msg_pkg=agent.v1` | none |

## Message regen

| SDK | command |
|-----|---------|
| typescript | `protoc-gen-es` (`target=ts`) |
| go | `protoc-gen-go` (`paths=source_relative`) |
| rust | prost-build (+ pbjson for JSON serde) |
| python | `protoc --python_out` |
| csharp | `protoc --csharp_out` |
| dart | `protoc-gen-dart` |
| swift | `protoc-gen-swift` (`Visibility=Public`) |
| kotlin | `protoc-gen-pbandk` |

## Verification

Every client must reproduce byte-for-byte from the unified plugin. The
`agent-tools/check.sh --full` guard plus the recipes above are the check; a
quick re-derive is:

```bash
protoc -I <proto-root> \
  --plugin=protoc-gen-easyrpc-<lang>=$(command -v protoc-gen-easyrpc-<lang>) \
  [--easyrpc-<lang>_opt=<opts>] --easyrpc-<lang>_out=<tmp> \
  agent/v1/agent.proto
# then apply the downstream rewrite (if any) and diff against the SDK file
```
