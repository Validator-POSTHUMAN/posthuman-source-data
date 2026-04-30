# 1. Install Rust

Pathfinder is written in Rust and requires the stable version.
If Rust is not installed, run:

````sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
````

Restart your terminal or run:

````sh
source $HOME/.cargo/env
````
Verify the installation:

````sh
rustc --version
cargo --version
````

# 2. Clone the Pathfinder Repository

````sh
git clone https://github.com/eqlabs/pathfinder.git
cd pathfinder
````

# 3. Build Pathfinder

````sh
cargo build --release
````
After successful compilation, the binary will be located at: *./target/release/pathfinder*

# 4. Run Pathfinder

Pathfinder requires you to specify an Ethereum RPC URL (for example, Infura or Alchemy) and a database path.

Example command:

````sh
./target/release/pathfinder \
  --eth.api="your Ethereum RPC URL" \
  --db.path="path to your Pathfinder database"
````
# 5. (Optional) Docker Installation

If you prefer Docker:

````sh
docker pull eqlabs/pathfinder
````
````sh
docker run -it \
  -v $(pwd)/db:/usr/share/pathfinder/data \
  eqlabs/pathfinder \
  --eth.api=https://mainnet.infura.io/v3/YOUR_TOKEN \
  --db.path=/usr/share/pathfinder/data
````
# 6. Additional Launch Parameters

*--http-rpc=127.0.0.1:9545* — to open the RPC interface.

*--network=mainnet* or *--network=goerli* — to select the network.
