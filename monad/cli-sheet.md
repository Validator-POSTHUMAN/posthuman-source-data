# Monad Mainnet read-only CLI sheet

Use these observations only on the intended host after verifying `143` (`0x8f`). They do not change configuration, services, keys or chain state.

```bash
monad-node --version
systemctl show monad-bft monad-execution monad-rpc -p ActiveState -p SubState -p NRestarts --no-pager
journalctl -u monad-bft -n 100 -o cat --no-pager
```

A local JSON-RPC probe can check identity without wallet access:

```bash
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/ \
  -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

Expected chain ID: `143` (`0x8f`). Compare with an independent reviewed endpoint before an operational conclusion. Do not use this sheet for key work, registration, staking, reward claims, transfers, service control, reset, firewall or package actions.
