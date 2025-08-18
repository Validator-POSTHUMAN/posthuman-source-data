## Update system packages
After connecting to the server, you want to ensure that the system is up-to-date and secure. Run the following commands to update the system packages upgrade any existing packages, and remove those that are no longer needed:

````bash
apt -y update && apt -y upgrade
apt dist-upgrade && sudo apt autoremove
````

## Configure the firewall
To ensure your Ethereum node can communicate with the network while staying secure, you need to configure the firewall to allow specific ports. In this step, you'll open the ports needed by Geth and Prysm, and enable the firewall on your server:
````bash
sudo ufw allow 30303/tcp
sudo ufw allow 30303/udp
sudo ufw allow 12000/udp
sudo ufw allow 13000/tcp
sudo ufw allow 22/tcp
sudo ufw enable
````

## Generate authentication secret

For Geth (the execution client) and Prysm (the consensus client) to communicate securely, they need a shared secret, known as a JSON Web Token (JWT). This token ensures that only authorized clients can interact with each other.

Before generating the secret, it's a good practice to create dedicated users for each client. This minimizes the risk of one client affecting the other and isolates their files and processes.

#### Start by creating the users and assigning them to a common group:

````bash
sudo adduser --home /home/geth --disabled-password --gecos 'Geth Client' geth
sudo adduser --home /home/prysm-beacon --disabled-password --gecos 'Prysm Beacon Client' prysm-beacon
sudo groupadd eth
sudo usermod -a -G eth geth
sudo usermod -a -G eth prysm-beacon
````

#### Next, create a directory to store the JWT secret, set the necessary permissions, and generate the secret:

````bash
sudo mkdir -p /var/lib/secrets
sudo chgrp -R eth /var/lib/secrets 
sudo chmod 750 /var/lib/secrets
sudo openssl rand -hex 32 | tr -d '\n' | sudo tee /var/lib/secrets/jwt.hex > /dev/null
````

#### Then set permissions on the secret file so that only the root user and the clients' users have access to it:

````bash
sudo chown root:eth /var/lib/secrets/jwt.hex
sudo chmod 640 /var/lib/secrets/jwt.hex
````

## Create data directories

````bash
sudo -u geth mkdir /home/geth/geth
sudo -u prysm-beacon mkdir /home/prysm-beacon/beacon
````

## Install and configure execution client (Geth)

````bash
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install ethereum
````

#### Create a Systemd Service for Geth:

````bash
sudo nano /etc/systemd/system/geth.service
````

#### Add the following configuration to the file:

````bash
[Unit]

Description=Geth Full Node
After=network-online.target
Wants=network-online.target

[Service]

Type=simple
Restart=always
RestartSec=5s
User=geth
WorkingDirectory=/home/geth
ExecStart=/usr/bin/geth \
  --http \
  --http.api eth,net,engine,admin \
  --mainnet \
  --datadir /home/geth/geth \
  --authrpc.jwtsecret /var/lib/secrets/jwt.hex

[Install]
WantedBy=multi-user.target
````

#### Start and Enable the Geth Service:

After saving the service file, reload the systemd daemon to apply the changes, start the Geth service, and enable it to start on boot:

````bash
sudo systemctl daemon-reload
sudo systemctl start geth
sudo systemctl enable geth
````

#### Check the Status of the Geth Service:

Verify that Geth is active running correctly by checking its status:

````bash
sudo systemctl status geth
````

To view the logs, run the command:

````bash
sudo journalctl -fu geth
````

## Configure consensus client (Prysm)

Now that Geth is up and running, the next step is to set up the Prysm Beacon Chain client, which acts as the consensus client.

#### Download and Prepare the Prysm Script:

First, create a directory for the Prysm script, download it and make it executable:

````bash
sudo -u prysm-beacon mkdir /home/prysm-beacon/bin
sudo -u prysm-beacon curl https://raw.githubusercontent.com/prysmaticlabs/prysm/master/prysm.sh --output /home/prysm-beacon/bin/prysm.sh
sudo -u prysm-beacon chmod +x /home/prysm-beacon/bin/prysm.sh
````

#### Create a Systemd Service for Prysm:
Similar to how you configured Geth, you'll create a systemd service file for Prysm beacon client.

Open the service file in a text editor:

````bash
sudo nano /etc/systemd/system/prysm-beacon.service
````

Add the following configuration to the file:

````bash
[Unit]

Description=Prysm Beacon Chain
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5s
User=prysm-beacon
ExecStart=/home/prysm-beacon/bin/prysm.sh beacon-chain \
  --mainnet \
  --datadir /home/prysm-beacon/beacon \
  --execution-endpoint=http://127.0.0.1:8551 \
  --jwt-secret=/var/lib/secrets/jwt.hex \
  --suggested-fee-recipient=YourWalletAddress \
  --checkpoint-sync-url=https://beaconstate.info \
  --genesis-beacon-api-url=https://beaconstate.info \
  --accept-terms-of-use

[Install]
WantedBy=multi-user.target
````

##### The *--execution-endpoint=http://127.0.0.1:8551* flag points Prysm to the local Geth client.
##### The *--jwt-secret=/var/lib/secrets/jwt.hex* flag allows Prysm to authenticate its communication with Geth using the shared JWT secret.
##### The *--suggested-fee-recipient=YourWalletAddress* flag should be replaced with your Ethereum wallet address to receive potential rewards.

#### Start and Enable the Prysm Service:
After saving the service file, reload the systemd daemon to apply the changes, start the Prysm service, and enable it to start on boot:

````bash
sudo systemctl daemon-reload
sudo systemctl start prysm-beacon
sudo systemctl enable prysm-beacon
````

#### Check the Status of the Prysm Service:
Verify that Prysm is running correctly by checking its status:

````bash
sudo systemctl status prysm-beacon
````

You can check the logs using:

````bash
sudo journalctl -fu prysm-beacon
````







