# Logos Blockchain Testnet — Security Hardening

Logos has no slashing and no consensus key in the Cosmos sense, so the usual
double-sign discipline does not apply. What replaces it is a single file.

`user_config.yaml` **is** the key material. `logos-blockchain-node init` writes
fresh cryptographic keys into it along with the peer list and the detected public
IP. There is no separate keystore to back up, no mnemonic printed for you to
write down, and no way to recover the wallet if the file is gone. Everything
below follows from that one fact.

Verified against the published Logos testnet release flow and POSTHUMAN's own
node operation.

---

## 1. Treat the config as a secret

```bash
chmod 600 ~/logos-blockchain/user_config.yaml
chmod 700 ~/logos-blockchain
```

Rules that matter more than the permissions:

- **Back it up off the host before you fund anything.** The faucet balance is
  the consensus stake; losing the config loses the stake with it.
- **Never copy it to a second node.** Two nodes on one identity is not a
  slashing event here, but it is two nodes competing for the same UTXO and a
  reliable way to make both behave oddly. Run one node per config.
- **Never paste it into an issue, a Discord message or a support channel.** It
  is not a log file, even though it sits beside one.
- **Do not re-run `init` on a funded node.** It writes *new* keys, and the node
  then reports a zero balance while the funded UTXO sits on a key you no longer
  have. Re-initialise only as part of a documented breaking-release upgrade, and
  take the backup first.

If you keep the config in configuration management, keep it encrypted at rest —
plain text in a private repository is still plain text.

---

## 2. Network exposure

| Port | Protocol | Direction | Exposure |
|---|---|---|---|
| `3000` | UDP (QUIC) | inbound | **public** — required for consensus gossip |
| `8080` | TCP | inbound | loopback only |

Consensus needs exactly one open port and it is UDP. Everything else stays in.

```bash
sudo ufw allow 3000/udp comment 'Logos P2P'
sudo ufw deny 8080/tcp
```

The HTTP API on `8080` answers `/cryptarchia/info`, `/network/info` and
`/wallet/<public-key>/balance`. That last one is the reason it must never be
public: it is an unauthenticated endpoint that reads balances by key, and
exposing it publishes exactly the association — node address to wallet key to
balance — that Cryptarchia's zero-knowledge design exists to keep private.

If you need the API from elsewhere, use an SSH local-forward rather than a
firewall rule:

```bash
ssh -N -L 8080:127.0.0.1:8080 <user>@<node-host>
```

Verify the result against listeners, not against firewall rules:

```bash
sudo ss -lntup | grep -E ':(3000|8080)'
```

---

## 3. The node binary and its circuits are one artifact

Logos ships the node and its ZK circuits as two archives, and they are version
matched. A node running a binary against circuits from another release does not
fail loudly — it runs, syncs and never proposes, which is the worst failure mode
on a probabilistic chain because it looks like bad luck.

- Download both from the official
  [releases page](https://github.com/logos-blockchain/logos-blockchain/releases)
  only, over HTTPS, and record the release tag you installed.
- Verify what you got before you install it, and keep the previous pair until
  the new one is proven:

```bash
sha256sum logos-blockchain-node-linux-x86_64-*.tar.gz \
          logos-blockchain-circuits-*-linux-x86_64.tar.gz
```

- Upgrade both together, always. If the release notes call for deleting state,
  config and circuits, the config deletion is the one that costs you the
  wallet — back it up first even though you are about to replace it.

Do not install from a third-party mirror or a one-line pipe-to-shell script.
There is no signature to check here, which makes the source of the bytes the
whole of the provenance.

---

## 4. Run it as an unprivileged service

The installation guide's unit runs the node as an ordinary user with
`Restart=on-failure`. Keep it that way and tighten the rest:

```ini
[Service]
User=logos
Group=logos
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths=/home/logos/logos-blockchain /home/logos/.logos-blockchain-circuits
LimitNOFILE=65535
```

The node needs no root, no capabilities and no write access outside its own
working directory and its circuits. A dedicated user is worth the five minutes:
it is what makes `ProtectHome=read-only` a real boundary rather than a comment.

---

## 5. Host baseline

Nothing Logos-specific, and still the part most often skipped:

- key-only SSH, no password authentication, no root login
- `fail2ban` or equivalent on the SSH port
- unattended security updates, and a reboot policy you actually follow
- no public management interface — no VNC, no remote desktop, no unauthenticated
  metrics port. If a GUI is needed for recovery, bind it to loopback and reach
  it through an SSH forward.

---

## 6. What a testnet does and does not excuse

The Logos testnet has no economic value and a faucet that replaces lost funds,
so the cost of a mistake is low. Two habits are still worth keeping exactly as
if it were mainnet, because they are the ones that transfer:

- the config-is-key-material discipline, since the mainnet equivalent will not
  have a faucet behind it, and
- one identity, one node, proven before any migration — check that the old node
  is really stopped and its port really answers nothing before starting a
  replacement:

```bash
systemctl is-active logos.service          # on the old host: expect inactive
sudo ss -lntup | grep ':3000' || echo 'no listener'
```

Everything else about a testnet — throwaway hosts, aggressive upgrades, deleting
state to test a release — is fine and is what a testnet is for.
