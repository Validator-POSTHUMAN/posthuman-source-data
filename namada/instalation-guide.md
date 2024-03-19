# Hardware Requirements

This section covers the recommended hardware requirements for engaging with Namada for validators, full nodes and light nodes. 

## Resource Requirements

| Node Type  | RAM      | SSD        | Number of Cores |
| ---------- | -------- | ---------- | --------------- |
| Validator  | 16GB      | 1TB*     | 4               |
| Full Node  | 8GB      | 1TB      | 2               |
| Light Node | TBD      | TBD        | TBD             |

**Note that storage size will be dependent on level of pruning.*

## Instalation 

```
sudo apt update && sudo apt upgrade -y
sudo apt-get install -y make git-core libssl-dev pkg-config libclang-12-dev build-essential protobuf-compiler
```
