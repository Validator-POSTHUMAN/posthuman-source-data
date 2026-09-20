# Solana Validator Governance (svmgov)

Solana governance runs through **Solana Governance Proposals (SGPs)** and the
`svmgov` validator CLI. A validator's stake is the voting weight, so
participation is an operator duty, and every action here is a **signed on-chain
transaction** — not a read-only query.

## The two distinct actions

Operators conflate these constantly. They are different transactions at
different stages with different consequences.

| | `support-proposal` | `cast-vote` |
|---|---|---|
| Stage | before activation | after activation, inside the voting window |
| What it does | adds your active stake to the proposal's support total | records your For / Against / Abstain allocation |
| Threshold | voting activates at **15%** of total cluster stake supporting | none; the window decides |
| Repeatable | no — once per identity per proposal | no |
| Is it a vote? | **no** | yes |

Supporting a proposal is sponsorship: it says "this deserves a vote". It does
not say how you will vote, and it cannot be taken back.

## Before signing anything

1. **Install a reviewed, commit-pinned official CLI.** Do not use a binary from
   a chat message or an unattributed mirror. Record the tag, the commit and the
   binary hash the way you would for the validator client.
2. **Read the proposal text from the authoritative repository**, not from a
   summary — <https://github.com/solana-foundation/solana-governance-proposals>.
3. **Use the mainnet identity**, never a testnet identity and never the vote
   account's withdraw authority.
4. **Get an explicit decision per proposal ID** from whoever owns that decision.
   An operator should not be inventing governance positions at the keyboard.

## Listing proposals

````bash
svmgov list-proposals --rpc-url https://api.mainnet-beta.solana.com
svmgov list-proposals --status support --rpc-url https://api.mainnet-beta.solana.com
svmgov proposal <proposal-id> --rpc-url https://api.mainnet-beta.solana.com
````

**Do not trust `--status support` alone in a transitional state.** The CLI
labels proposals from epoch arithmetic *before* it checks the on-chain `voting`
flag, so a proposal that has already crossed the 15% threshold can still be
listed as needing support. Always read the individual proposal and check whether
`voting` is true before deciding to sponsor it. Sponsoring an already-activated
proposal is a wasted signed transaction.

## Supporting a proposal

````bash
svmgov support-proposal \
  --proposal <proposal-id> \
  --keypair /path/to/validator-keypair.json \
  --rpc-url https://api.mainnet-beta.solana.com
````

Retain the transaction signature and confirm it. A completion you cannot
reconcile on-chain is an operator report, not a fact:

````bash
solana confirm -v <signature> --url https://api.mainnet-beta.solana.com
svmgov proposal <proposal-id> --rpc-url https://api.mainnet-beta.solana.com
````

## Casting a formal vote

Voting opens only after activation, in a defined epoch window, and depends on
the consensus snapshot being finalised — activation alone does not imply the
window is open. The allocation is in basis points and **must total 10,000**:

````bash
svmgov cast-vote \
  --proposal <proposal-id> \
  --for 10000 --against 0 --abstain 0 \
  --keypair /path/to/validator-keypair.json \
  --rpc-url https://api.mainnet-beta.solana.com
````

Split votes are allowed — e.g. `--for 7000 --against 3000` — which is how a pool
or a DAO-governed validator reflects a divided constituency.

Confirm on-chain and retain the signature.

## Operational rules

- Treat every `svmgov` call that signs as a change with a written decision,
  a recorded signature, and an on-chain confirmation.
- Keep a register: proposal ID, decision, who decided, transaction signature,
  confirmation slot.
- Check the proposal's state again at the start of the voting window; between
  support and vote, thresholds move and windows shift.
- Never sign from an automation without a human approval step. Governance is
  exactly the class of action that should not be unattended.

## References

- Support a proposal — <https://docs.governance.solana.com/svmgov/validators/support-proposal/>
- List proposals — <https://docs.governance.solana.com/svmgov/validators/list-proposals/>
- Cast a vote — <https://docs.governance.solana.com/svmgov/validators/cast-vote/>
- Proposal texts — <https://github.com/solana-foundation/solana-governance-proposals>
- SIMD index — <https://simd.mixy.one/>

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
