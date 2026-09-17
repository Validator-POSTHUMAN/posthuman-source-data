# Mina Mainnet Node Installation — Docker

This is the **container** path. For the Debian package and systemd path see the
**Installation guide**; both produce the same node. Read that guide's
"What is current" and "Requirements" sections first — the version, chain ID and
hardware facts are identical and are not repeated here.

Docker is the better choice when you want the daemon, a SNARK coordinator, a
worker pool and an archive node expressed as one file, or when the host OS is
not one of the supported Debian/Ubuntu releases.

## Images

Every image is published for each supported base. Replace `CODENAME` with
`bookworm`, `bullseye`, `noble`, `jammy` or `focal`:

| Component | Image |
|---|---|
| Daemon | `minaprotocol/mina-daemon:4.0.0-6850301-CODENAME-mainnet` |
| Archive | `minaprotocol/mina-archive:4.0.0-6850301-CODENAME-mainnet` |
| Rosetta | `minaprotocol/mina-rosetta:4.0.0-6850301-CODENAME-mainnet` |

**Pin the tag.** `latest` is not a network guarantee: an image pull between two
restarts can silently move the node to a build meant for a different fork. Record
the tag you run together with the chain ID the node reports — that pair is what
proves which network you are on.

## Prepare the host

````bash
sudo apt -y update && sudo apt -y install docker.io docker-compose-plugin jq
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
````

Log out and back in so the group membership applies. Running `docker` under
`sudo` works but leaves root-owned files in your config directory.

````bash
sudo ufw allow 22/tcp
sudo ufw allow 8302/tcp
sudo ufw enable
````

## Create the key

Generate it with the same image you will run, so the key format matches the
daemon:

````bash
mkdir -p ~/mina/keys && chmod 700 ~/mina/keys
docker run --rm -it \
  -v ~/mina/keys:/keys \
  minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet \
  mina advanced generate-keypair --privkey-path /keys/my-wallet
chmod 600 ~/mina/keys/my-wallet
````

Verify it before building anything on it:

````bash
docker run --rm -it -v ~/mina/keys:/keys \
  -e MINA_PRIVKEY_PASS="your-key-password" \
  minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet \
  mina advanced validate-keypair --privkey-path /keys/my-wallet
````

Full custody rules are in the **Keys** guide.

## Run a single container

````bash
mkdir -p ~/mina/.mina-config

docker run --name mina -d --restart=always \
  -p 8302:8302 \
  -p 127.0.0.1:3085:3085 \
  -v ~/mina/keys:/keys:ro \
  -v ~/mina/.mina-config:/root/.mina-config \
  -e MINA_PRIVKEY_PASS="your-key-password" \
  minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet \
  daemon \
    --peer-list-url https://bootnodes.minaprotocol.com/networks/mainnet.txt \
    --config-directory /root/.mina-config \
    --block-producer-key /keys/my-wallet \
    --external-port 8302 \
    --metrics-port 6060 \
    --log-level Info \
    --file-log-level Debug
````

Points that matter:

- `--restart=always` (or `unless-stopped`). Docker's default is `no`, which
  means a crash at 03:00 is a lost epoch of uptime. There is no supervision
  otherwise — the container path has no equivalent of the package's
  `Restart=always` unit.
- `/root/.mina-config` **must** be a persistent volume. It holds the on-disk
  chain cache; without it every restart is a full ~30-minute bootstrap instead
  of a few minutes.
- Mount the key directory read-only.
- `-p 127.0.0.1:3085:3085` binds GraphQL to loopback on the host. Never publish
  it on `0.0.0.0`.

### Exposing GraphQL safely

The daemon's REST/GraphQL server listens on localhost *inside the container*, so
a plain `-p` mapping reaches nothing. Two ways out, and only one of them is a
good idea:

- `--insecure-rest-server` opens the **full** GraphQL API — including mutations
  that send payments and change the SNARK worker key — on all interfaces.
  Avoid it on a block producer.
- `--open-limited-graphql-port --limited-graphql-port 3086` opens a **read-only
  limited** GraphQL server instead. Publish that one, still bound to host
  loopback:

````bash
  -p 127.0.0.1:3085:3086 \
  ...
    --open-limited-graphql-port --limited-graphql-port 3086
````

The "INSECURE" warning in the flag's help text is about listening on all
addresses inside the container; the host-side `127.0.0.1` binding plus the
firewall is what actually bounds it. This is the pattern POSTHUMAN runs on its
own producers.

## Run with Docker Compose

`~/mina/docker-compose.yml`:

````yaml
services:
  mina:
    image: minaprotocol/mina-daemon:4.0.0-6850301-bookworm-mainnet
    container_name: mina
    restart: always
    entrypoint: []
    environment:
      MINA_PRIVKEY_PASS: ${MINA_PRIVKEY_PASS}
    ports:
      - '8302:8302'
      - '127.0.0.1:3085:3086'
    volumes:
      - './keys:/keys:ro'
      - './mina-config:/root/.mina-config'
    healthcheck:
      test: ["CMD-SHELL", "mina client status"]
      interval: 60s
      timeout: 10s
      retries: 100
    command: >
      bash -c '
        mina daemon
          --peer-list-url https://bootnodes.minaprotocol.com/networks/mainnet.txt
          --config-directory /root/.mina-config
          --block-producer-key /keys/my-wallet
          --open-limited-graphql-port --limited-graphql-port 3086
          --metrics-port 6060
          --log-level Info --file-log-level Debug
      '
````

Keep the password out of the compose file — put it in `~/mina/.env` with mode
`600`:

````bash
printf 'MINA_PRIVKEY_PASS=%s\n' 'your-key-password' > ~/mina/.env
chmod 600 ~/mina/.env
docker compose -f ~/mina/docker-compose.yml up -d
````

To add SNARK work or an archive node to this file, see the **SNARK worker** and
**Archive node** guides — both are written as additional services in the same
compose project.

## Verify

````bash
docker exec -it mina mina client status
docker exec -it mina mina accounts list
````

Check `Sync status: Synced`, the `Chain id`, `Block height` equal to
`Max observed block length`, a non-trivial peer count, and
`Block producers running: 1`.

````bash
docker logs --follow mina
docker ps --format '{{.Names}}\t{{.Status}}'
````

Restart count is a signal, not noise. A container that is "Up 2 minutes" every
time you look is crash-looping — the last lines of `docker logs` will normally
show a key-permission or password problem.

## Automode images

Mina publishes a second daemon line, `minaprotocol/mina-daemon-auto-hardfork`,
used to cross a hard fork without a manual binary swap: the node carries both
the pre-fork and post-fork logic and switches itself at the fork slot. It is an
upgrade mechanism, not a different node. Which line you should be on depends on
where the network is in its upgrade cycle — see the **Upgrades** guide before
choosing.

## Next steps

- **Keys** — hot/cold split, libp2p key, backups
- **Block producer** — coinbase receiver, stake latency, proving production
- **SNARK worker** — coordinator and worker services in the same compose file
- **Archive node** — `mina-archive` plus PostgreSQL
- **Monitoring**, **Security hardening**, **Upgrades**

## Sources

- [docs.minaprotocol.com — connect to Mainnet or Devnet](https://docs.minaprotocol.com/node-operators/validator-node/connecting-to-the-network)
- [docs.minaprotocol.com — generating a key pair](https://docs.minaprotocol.com/node-operators/validator-node/generating-a-keypair)
- [docs.minaprotocol.com — Mina CLI reference](https://docs.minaprotocol.com/node-operators/reference/mina-cli-reference)
- [Mina 4.0.0 Mesa mainnet release notes](https://github.com/MinaProtocol/mina/releases/tag/4.0.0-mainnet-mesa)
