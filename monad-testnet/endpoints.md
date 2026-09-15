# Monad Testnet EVM endpoints and event streams

| Interface | Published POSTHUMAN value |
| --- | --- |
| HTTP JSON-RPC | `https://rpc-monad-testnet.posthuman.digital` |
| WebSocket | `wss://rpc-monad-testnet.posthuman.digital` |
| Chain ID | `10143` (`0x279f`) |

HTTP JSON-RPC, WebSocket transport and gRPC are separate capabilities. A successful HTTP request does not prove WebSocket subscription support, history, traces, latency, or an uptime SLA.

Monad also has a custom gRPC/event-stream ecosystem. It is not Cosmos SDK gRPC and must not be hidden because of its name. Integration needs an exact proto/client version, authentication policy, replay/retention behavior, filter limits, reconnect and deduplication design.

Bound each probe by identity, timeout, method, response shape and rate-limit classification. Record measured time separately from publication time. Use independent sources before treating an endpoint as a fallback. Do not expose validator RPC, private listeners or credentials.
