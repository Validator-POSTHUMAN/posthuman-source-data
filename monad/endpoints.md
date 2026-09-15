# Monad Mainnet EVM endpoints and event streams

| Interface | Published POSTHUMAN value |
| --- | --- |
| HTTP JSON-RPC | `https://rpc-monad.posthuman.digital` |
| WebSocket | No POSTHUMAN public WebSocket endpoint is published for mainnet. |
| Chain ID | `143` (`0x8f`) |

HTTP JSON-RPC, WebSocket transport and gRPC are separate capabilities. A successful HTTP request does not prove WebSocket subscription support, history, traces, latency, or an uptime SLA.

Monad also has a custom gRPC/event-stream ecosystem. It is not Cosmos SDK gRPC and must not be hidden because of its name. Integration needs an exact proto/client version, authentication policy, replay/retention behavior, filter limits, reconnect and deduplication design.

Bound each probe by identity, timeout, method, response shape and rate-limit classification. Record measured time separately from publication time. Use independent sources before treating an endpoint as a fallback. Do not expose validator RPC, private listeners or credentials.
