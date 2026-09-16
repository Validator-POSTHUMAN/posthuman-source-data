# Starknet validator security hardening

Starknet validators have no consensus key and no double-sign risk, so the
threat model is different from a Cosmos or Ethereum validator. What you defend
here is: the **stake** (a cold onchain account), the **yield** (a hot signing
key), and the **node** (an RPC service with an L1 credential attached).

## Threat model

| Asset | Attack | Consequence | Control |
|---|---|---|---|
| Staking account | key theft | full stake drained after the 7-day lockup | hardware wallet or multisig, offline |
| Rewards account | key theft | accrued rewards stolen | cold, never on a server |
| Operational key | key theft on the node | attestations stopped, gas drained, yield lost for you and delegators | hot but disposable, rotatable, remote signer option |
| Ethereum WS credential | leak from config or logs | provider quota abuse, billing, endpoint revocation → node stalls | file-scoped env, `chmod 600`, never in git |
| Node RPC port | public exposure | resource exhaustion, targeted stalling | bind private, firewall, rate limit |
| Metrics port | public exposure | topology and validator identity disclosure | loopback or private network only |

There is no principal slashing in the current staking phase. The realistic loss
is **forfeited yield**, and the realistic catastrophic loss is **stake theft
via the staking key** — which is a custody problem, not an ops problem.

## Address hierarchy

The protocol gives you three addresses precisely so that the always-online key
is not the valuable one. Use all three.

```
staking address   → cold, hardware/multisig, used a handful of times ever
rewards address   → cold, receives payouts, never touched by any service
operational addr  → hot, on the validator host, holds gas only
```

Rules:

- The staking address **cannot be changed**. Treat its key like a treasury key.
- Never reuse one account for two roles, even on testnet — habits transfer.
- Keep only a few days of fees in the operational account. It is the account
  most likely to be compromised and the one whose loss must not matter.
- Rotate the operational key on any suspicion, on staff change, and after any
  host compromise: `declare_operational_address` from the new account, then
  `change_operational_address` from the staking account, then restart the
  service and verify a confirmed attestation.

### Local signing constraint

If the operational account signs locally, it must be deployed and
**unprotected** — no Ready Wallet Guardian, no Braavos hardware signer. Those
features block automated signing. If policy requires protected custody for the
operational role, use a **remote signer** instead of weakening the account:

- Equilibrium: `--remote-signer-url <url>` instead of `--local-signer`.
- Nethermind: `signer.url` instead of `signer.privateKey`.

A remote signer keeps the key on a separate hardened host or HSM, and the
attestation daemon only ever receives signatures.

## Key handling

Never:

- paste a private key into chat, a ticket, a commit, a log line, a shell
  command line (it lands in history) or a screenshot;
- store the operational key in the compose file, the systemd unit, or any file
  tracked by git;
- read a key back out of a running container (`docker inspect` exposes the
  environment) as a routine operation.

Always:

- keep secrets in a dedicated env file, `chmod 600`, owned by the service user;
- add `.env` to `.gitignore` before the first commit, not after;
- back up the staking and rewards key material offline, in more than one
  physical location, and test the restore path;
- treat any key that has ever been on a compromised host as compromised.

```bash
sudo install -o starknet -g starknet -m 600 /dev/null /etc/starknet/attestation.env
$EDITOR /etc/starknet/attestation.env
```

## Host hardening

```bash
# SSH: keys only, no root login
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload ssh

# Firewall: default deny inbound
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow <your-ssh-port>/tcp
sudo ufw enable
```

Review the firewall change on a console you will not lose — an SSH-locking
rule on a remote validator is its own incident.

Additional baseline:

- unattended security updates for the OS; deliberate, tested upgrades for the
  node and attestation binaries;
- `fail2ban` on SSH;
- a dedicated non-root service user, no docker group for interactive accounts
  that do not need it;
- the systemd hardening directives from
  [Validator attestation](/networks/starknet/guides/validator-attestation)
  (`NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`).

## Network exposure

| Port | Service | Exposure |
|---|---|---|
| 9545 | Pathfinder JSON-RPC | private / loopback, or reverse proxy with TLS and rate limiting |
| 6060 / 6061 | Juno HTTP / WS | same |
| 9000 / 9090 | metrics | loopback or private network only |
| L1 WebSocket | outbound | keep the credential server-side only |

If you publish a public RPC endpoint, put it behind a reverse proxy with rate
limiting, and run it on a **separate node** from the validator. A public
endpoint is a resource-exhaustion path straight into the node your attestations
depend on.

## Redundancy without duplication

Run a second node — ideally the **other client** — so a client bug or a host
failure does not end your epoch. But:

> Never run two attestation services with the same operational key at the same
> time. Duplicate `attest` transactions waste fees, race each other and make
> incident diagnosis ambiguous.

Keep the standby node synced and the standby attestation service **stopped**.
Failover is: stop the primary service, repoint or start the standby, verify a
confirmed attestation.

## Change discipline

- Upgrade the node and the attestation service as a pair, on testnet first.
- Pin exact image tags; `latest` turns a restart into an unplanned upgrade.
- After any change to node URL, RPC version, operational address or key,
  verify one confirmed attestation before considering the change complete.
- Keep the previous database directory until the new state has produced a
  confirmed attestation — see [Snapshots](/networks/starknet/guides/snapshots).

## Incident response

1. Establish whether stake or only yield is at risk. Stake risk means the
   staking key; everything else is yield.
2. If the operational key may be exposed: rotate it first, investigate second.
3. If the host may be compromised: isolate it, do not reuse any key that lived
   on it, rebuild rather than clean.
4. If the staking key may be exposed: this is a funds emergency. `unstake_intent`
   starts a 7-day lockup an attacker can also exploit — escalate to whoever
   holds custody authority immediately, do not improvise alone.
5. Record what happened, what was checked, and what changed. The next incident
   is cheaper if this one is written down.

## Reference

- Starknet docs — [Staking: addresses](https://docs.starknet.io/learn/protocol/staking#addresses)
- [Equilibrium attestation — signatures](https://github.com/eqlabs/starknet-validator-attestation)
- [Nethermind external signer](https://nethermindeth.github.io/starknet-staking-v2/external-signer)
