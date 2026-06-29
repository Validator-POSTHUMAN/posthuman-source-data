#!/usr/bin/env bash
set -euo pipefail

REPO="/home/ubuntu/website-claw/nodes.posthuman.digital/posthuman-source-data"
DEPLOY_HOST="valoper@65.21.7.184"
DEPLOY_DIR="/srv/data/apps/posthuman-nodes-ui"
LOCK_FILE="/tmp/posthuman-celestia-decentralize-map-update.lock"
MAP_FILE="celestia/decentralize-map.json"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

exec 9>"$LOCK_FILE"
flock -n 9

cd "$REPO"

git pull --ff-only
python3 scripts/update-celestia-decentralize-map.py
python3 -m py_compile scripts/update-celestia-decentralize-map.py
python3 -m json.tool networks.json >/dev/null
python3 -m json.tool "$MAP_FILE" >/dev/null
rm -rf scripts/__pycache__

if git diff --quiet -- "$MAP_FILE"; then
  echo "No Celestia decentralize-map changes."
  exit 0
fi

git add "$MAP_FILE"
git commit -m "Update Celestia decentralization map"
git push

# GitHub raw/cache can lag immediately after push.
sleep 10

ssh -o BatchMode=yes "$DEPLOY_HOST" \
  "cd '$DEPLOY_DIR' && git pull --ff-only && sudo rm -rf .next && sudo yarn build && sudo pm2 restart nodes"
