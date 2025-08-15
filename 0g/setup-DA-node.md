Step 1: Clone and Build the Repository
Install dependencies:

sudo apt-get update && sudo apt-get install clang cmake build-essential pkg-config libssl-dev protobuf-compiler llvm llvm-dev


Clone the repository and checkout the specific version:

git clone https://github.com/0glabs/0g-da-node.git
cd 0g-da-node

Build the project:

cargo build --release

Download necessary parameters:

./dev_support/download_params.sh

Step 2: Generate BLS Private Key (if needed)
If you don't have a BLS private key, generate one:

cargo run --bin key-gen

Keep the generated BLS private key secure.

Step 3: Configure the Node
Create a configuration file named config.toml in the project root directory.

Add the following content to the file, adjusting values as needed:

log_level = "info"

data_path = "./db/"

# path to downloaded params folder
encoder_params_dir = "params/" 

# grpc server listen address
grpc_listen_address = "0.0.0.0:34000"
# chain eth rpc endpoint
eth_rpc_endpoint = "https://evmrpc-testnet.0g.ai"
# public grpc service socket address to register in DA contract
# ip:34000 (keep same port as the grpc listen address)
# or if you have dns, fill your dns
socket_address = "<public_ip/dns>:34000"

# data availability contract to interact with
da_entrance_address = "0x857C0A28A8634614BB2C96039Cf4a20AFF709Aa9" # testnet config and see testnet page for the latest info

# deployed block number of da entrance contract
start_block_number = 940000 # testnet config

# signer BLS private key
signer_bls_private_key = ""
# signer eth account private key
signer_eth_private_key = ""
# miner eth account private key, (could be the same as `signer_eth_private_key`, but not recommended)
miner_eth_private_key = ""

# whether to enable data availability sampling
enable_das = "true"


Make sure to fill in the signer_bls_private_key, signer_eth_private_key, and miner_eth_private_key fields with your actual private keys.

Step 4: Run the Node
Start the 0g DA node using the following command:

./target/release/server --config config.toml

This will start the node using the configuration file you created.

Step 5: Verify the Node is Running
On the first run, the DA node will register the signer information in the DA contract. You can monitor the console output to ensure the node is running correctly and has successfully registered.
