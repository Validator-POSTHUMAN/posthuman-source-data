# Celestia AI Operations Skill

This public skill helps an AI agent safely operate a Celestia consensus
validator and its Fibre data service. It is provider-neutral: every operator
supplies their own inventory, approved public host:port, service names, homes,
local endpoints, validator account reference, consensus address, and monitoring
path.

## Repository

- [Celestia skill](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/tree/main/celestia)
- [SKILL.md](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/SKILL.md)
- [Raw SKILL.md](https://raw.githubusercontent.com/Validator-POSTHUMAN/AI-skills-for-networks/main/celestia/SKILL.md)
- [Inventory schema](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/references/inventory.schema.json)
- [Example inventory](https://github.com/Validator-POSTHUMAN/AI-skills-for-networks/blob/main/celestia/examples/inventory.example.json)

## Fibre workflow

For Mocha-5, use the skill with your own chain ID, validator and Fibre service
names, dedicated Fibre home, loopback app/PrivValidator gRPC addresses, public
Fibre host:port, validator account reference, consensus address, trusted RPC,
and monitoring target. Do not reuse values from this guide or another
operator's infrastructure.

The skill requires a healthy bonded validator, the official CPU gate, a
dedicated Fibre home, loopback-only control links, independent public
data-plane verification, and fresh validator-signing evidence. It treats
`tx valaddr set-host` as an explicit-approval, account-key transaction and
requires both `code=0` and a matching `x/valaddr` provider record before
declaring registration complete.

It never accepts or stores keyring passphrases, private keys, mnemonics, or
private endpoints in chat, guide files, service units, or environment files.

See the [Fibre guide](fibre.md) for the Mocha-5 procedure and fill-in worksheet.
