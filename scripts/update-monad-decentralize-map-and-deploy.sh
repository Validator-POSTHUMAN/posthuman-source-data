#!/usr/bin/env bash
set -euo pipefail

REPO="/home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data"
DEPLOY_HOST="valoper@65.21.7.184"
DEPLOY_DIR="/srv/data/apps/posthuman-nodes-ui"
LOCK_FILE="/tmp/posthuman-monad-decentralize-map-update.lock"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

exec 9>"$LOCK_FILE"
flock -n 9

cd "$REPO"

git pull --ff-only
python3 scripts/update-monad-decentralize-map.py

if git diff --quiet -- monad/decentralize-map.json monad-testnet/decentralize-map.json; then
  echo "No Monad decentralize-map changes."
  exit 0
fi

git add monad/decentralize-map.json monad-testnet/decentralize-map.json
git commit -m "Update Monad decentralization map"
git push

# GitHub raw/cache can lag immediately after push.
sleep 10

ssh -o BatchMode=yes "$DEPLOY_HOST" \
  "cd '$DEPLOY_DIR' && sudo rm -rf .next && sudo yarn build && sudo pm2 restart nodes"
