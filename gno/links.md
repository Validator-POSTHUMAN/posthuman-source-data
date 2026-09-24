# Gnoland Mainnet Links

## Network

- Website and realms: https://gno.land/
- Documentation: https://docs.gno.land/
- Official mainnet RPC: https://rpc.gno.land
- Validator candidate registry: https://gno.land/r/gnops/valopers
- GovDAO: https://gno.land/r/gov/dao

## Source and releases

- GitHub: https://github.com/gnolang/gno
- Tested release: https://github.com/gnolang/gno/releases/tag/v1.5.0
- Launch genesis assets (`genesis.json`, `genesis.json.gz`, `CHECKSUMS.txt`):
  https://github.com/gnolang/gno/releases/tag/chain%2Fmainnet
- Mainnet deployment notes:
  https://github.com/gnolang/gno/tree/master/misc/deployments/mainnet.gno.land

## POSTHUMAN public services

- RPC: https://rpc-gnoland.posthuman.digital
- Snapshots: https://snapshots-gnoland.posthuman.digital
- Block explorer: https://gnoland.app
- Persistent peer:
  `g17zx8uj0rqkkrsdkz3jvt8kp0k5ry30aw3qplww@peer-gnoland.posthuman.digital:38656`

The RPC and snapshot endpoints use TLS through Cloudflare. The peer record is
DNS-only for raw TCP P2P. Unsafe RPC methods are blocked at the reverse proxy.

Network identifier: `gnoland-1`.
