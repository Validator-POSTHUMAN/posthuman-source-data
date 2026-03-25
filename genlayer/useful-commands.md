## Useful commands
### Follow logs

```bash
docker logs -f genlayer-node
```

### Show running containers

```bash
docker compose ps
```

### Restart node

```bash
docker compose restart genlayer-node
```

### Recreate stack

```bash
docker compose down
docker compose up -d --force-recreate
```

### Clean data and resync

```bash
docker compose down
rm -rf data/node
docker compose up -d --force-recreate
```
