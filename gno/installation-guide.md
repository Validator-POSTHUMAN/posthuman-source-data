# set vars
```bash
export WALLET="wallet"          <-- Change
export MONIKER="test"           <-- Change
export GNOLAND_CHAIN_ID="test11"
export GNOLAND_PORT="54"        <-- Change
```
```bash
cd $HOME
rm -rf gno
git clone https://github.com/gnolang/gno.git
cd gno
git checkout chain/test11
make install_gnokey
make -C gno.land install.gnoland && make -C contribs/gnogenesis install
```
```bash
cd $HOME
gnoland secrets init
gnoland config init
gnoland config set rpc.laddr tcp://0.0.0.0:${GNOLAND_PORT}657
gnoland config set p2p.laddr tcp://0.0.0.0:${GNOLAND_PORT}656
gnoland config set proxy_app tcp://127.0.0.1:${GNOLAND_PORT}658
gnoland config set moniker $MONIKER
gnoland config set p2p.persistent_peers g1vgvqg94xy8qj23dc8zpw6wns7q0hj9g8mx03ha@gno-core-sen-01.test11.testnets.gno.land:26656
gnoland config set p2p.seeds g1vgvqg94xy8qj23dc8zpw6wns7q0hj9g8mx03ha@gno-core-sen-01.test11.testnets.gno.land:26656
cd ~/gnoland-data/config
wget -O genesis.json https://gno-testnets-genesis.s3.eu-central-1.amazonaws.com/test11/genesis.json
```
## Create service file
```bash
sudo tee /etc/systemd/system/gnoland.service > /dev/null <<EOF
[Unit]
Description=Gnoland node
After=network-online.target
[Service]
User=$USER
WorkingDirectory=$HOME
ExecStart=$(which gnoland) start --genesis  $HOME/gnoland-data/config/genesis.json --data-dir $HOME/gnoland-data/ --skip-genesis-sig-verification
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
[Install]
WantedBy=multi-user.target
EOF
```
```bash
sudo systemctl daemon-reload
sudo systemctl restart gnoland && sudo journalctl -u gnoland -f
```

## Create wallet
```bash
gnokey add $WALLET -home /home/gnoland/gnoland-data/
```
## Get validator address and public key:
```bash
VAL_ADDRESS=$(gnoland secrets get validator_key | jq -r '.address')
VAL_PUB_KEY=$(gnoland secrets get validator_key | jq -r '.pub_key')
```
## Create validator
```bash
gnokey maketx call \
    -pkgpath "gno.land/r/gnops/valopers" \
    -func "Register" \
    -gas-fee 20000ugnot \
    -gas-wanted 20_000_000 \
    -broadcast \
    -chainid "test11" \
    -args "$MONIKER" \
    -args "<description>" \
    -args "<server_type>" \
    -args "$VAL_ADDRESS" \
    -args "$VAL_PUB_KEY" \
    -remote "https://rpc.test11.testnets.gno.land:443" \
    $WALLET
```
