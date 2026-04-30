# NEAR Validator Monitoring Guide

## Overview

Monitoring setup for NEAR validator node with Telegram alerts. Covers node health, sync status, and block lag detection.

## 1. Telegram Bot Setup

1. Create bot via [@BotFather](https://t.me/BotFather) — get `BOT_TOKEN`
2. Create a channel/group, add bot as admin — get `CHAT_ID`

Test:

```bash
curl -s -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=Test alert"
```

## 2. Monitor Script

Create `/home/ubuntu/near-monitor.sh`:

```bash
#!/bin/bash

# NEAR Validator Monitor - Minimal Alerts
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
RPC_URL="http://localhost:3030"
CHECK_INTERVAL=300
BLOCK_LAG_THRESHOLD=100
LAST_ALERT_FILE="/tmp/near-monitor-last-alert"

send_telegram() {
    local message="$1"
    local alert_key="$2"

    # Prevent duplicate alerts within 30 min
    if [ -f "$LAST_ALERT_FILE" ]; then
        local last=$(grep "$alert_key" "$LAST_ALERT_FILE" 2>/dev/null | cut -d: -f2)
        local now=$(date +%s)
        if [ -n "$last" ] && [ $((now - last)) -lt 1800 ]; then
            return
        fi
    fi

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=${message}" \
        -d "parse_mode=HTML" > /dev/null

    echo "${alert_key}:$(date +%s)" >> "$LAST_ALERT_FILE"
}

check_node() {
    local status=$(curl -s ${RPC_URL}/status 2>/dev/null)

    if [ -z "$status" ]; then
        send_telegram "🔴 <b>NEAR Node DOWN!</b>" "node_down"
        return 1
    fi

    local local_block=$(echo "$status" | jq -r '.sync_info.latest_block_height')
    local mainnet_block=$(curl -s https://rpc.mainnet.near.org/status 2>/dev/null | jq -r '.sync_info.latest_block_height')

    if [ -n "$mainnet_block" ] && [ -n "$local_block" ]; then
        local lag=$((mainnet_block - local_block))
        if [ "$lag" -gt "$BLOCK_LAG_THRESHOLD" ]; then
            send_telegram "⚠️ <b>Node behind!</b>%0ALag: ${lag} blocks" "block_lag"
        fi
    fi

    echo "$(date): Block: $local_block"
}

while true; do
    check_node
    sleep $CHECK_INTERVAL
done
```

```bash
chmod +x /home/ubuntu/near-monitor.sh
```

## 3. Systemd Service

```bash
sudo tee /etc/systemd/system/near-monitor.service > /dev/null << 'EOF'
[Unit]
Description=NEAR Validator Monitor
After=network-online.target neard.service
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
ExecStart=/home/ubuntu/near-monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable near-monitor
sudo systemctl start near-monitor
```

## 4. What It Monitors

| Check | Interval | Alert Condition |
|-------|----------|-----------------|
| Node health | 5 min | Node not responding on RPC |
| Block lag | 5 min | Local node >100 blocks behind mainnet |

Deduplication: same alert type not sent more than once per 30 minutes.

## 5. Management

```bash
# Status
sudo systemctl status near-monitor

# Logs
journalctl -u near-monitor -f --no-pager

# Restart
sudo systemctl restart near-monitor

# Test Telegram alert
curl -s -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=✅ NEAR Monitor test"
```

---

**Created by POSTHUMAN validators**

Website: https://posthuman.digital
