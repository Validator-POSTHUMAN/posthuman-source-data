# Prerequisites
Before setting up your storage node:

Understand that 0G Storage interacts with on-chain contracts for blob root confirmation and PoRA mining.
Check here for deployed contract addresses.
Install Dependencies
Start by installing all the essential tools and libraries required to build the 0G storage node software.

*sudo apt-get update*
*sudo apt-get install clang cmake build-essential pkg-config libssl-dev*

Install rustup: rustup is the Rust toolchain installer, necessary as the 0G node software is written in Rust.

*curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh*

Download the Source Code:

*git clone -b <latest_tag> https://github.com/0glabs/0g-storage-node.git*

Build the Source Code

*cd 0g-storage-node*

**Build in release mode**

*cargo build --release*

This compiles the Rust code into an executable binary. The --release flag optimizes the build for performance.

**Configuration**
Navigate to the run directory and open config.toml for editing. Follow the steps below.

Edit the configuration file:
*cd run*
*nano config.toml*

Update configuration with your preferred settings:
Below is just an example configuration for illustration purposes. For official default values, copy over the config-testnet-turbo.toml file to your config.toml file.

# Peer nodes: A list of peer nodes to help your node join the network. Check inside 0g-storage/run directory for suggested configurations.
*network_boot_nodes = []*

# Contract addresses
*log_contract_address = "CONTRACT_ADDRESS"* #flow contract address, see testnet information*
*mine_contract_address = "CONTRACT_ADDRESS"* #Address of the smart contract on the host blockhain that manages mining.

# L1 host blockchain RPC endpoint URL. See testnet information page for RPC endpoints
*blockchain_rpc_endpoint = "RPC_ENDPOINT"*

# Start sync block number: The block number from which your node should start synchronizing the log data.
*log_sync_start_block_number = BLOCK_NUMBER*

# Your private key (64 chars, no '0x' prefix, include leading zeros): Your private key (without the `0x` prefix) if you want to participate in PoRA mining and earn rewards.
*miner_key = "YOUR_PRIVATE_KEY"*

# Max chunk entries in db (affects storage size): The maximum number of chunk entries (each 256 bytes) to store in the database. This effectively limits the database size.
*db_max_num_chunks = MAX_CHUNKS*

# ENR address: Your node's public IP address, essential for other nodes to discover and connect to you. Currently automatically set by the node.
*network_enr_address = ""*


Running the Storage Node
Check configuration options:
*../target/release/zgs_node -h*

Run the storage service:
*cd run*
*../target/release/zgs_node --config config.toml --miner-key <your_private_key>*
