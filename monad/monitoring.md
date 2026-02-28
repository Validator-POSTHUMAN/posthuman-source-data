# Monad Node Monitoring

## Overview

| Feature | Status |
|---------|--------|
| Telegram Alerts | ✅ Available |
| Grafana Dashboard | 🔧 Coming Soon |
| Prometheus Metrics | 🔧 Coming Soon |

## Telegram Alerts

Lightweight monitoring script running every 10 minutes via systemd timer. Fires **only on state changes** — no spam.

**What it monitors:**

| Check | Alert | Recovery |
|-------|-------|----------|
| `monad-bft` service | 🔴 Service down or core-dump | 🟢 Recovered |
| `monad-execution` service | 🔴 Service down | 🟢 Recovered |
| `monad-rpc` service | 🔴 Service down | 🟢 Recovered |
| Block progress | ⚠️ Stuck > 10 min | 🟢 Sync resumed |
| Critical log patterns | 💥 core-dump / 30000 blocks behind | auto-clears |
| Uptime 24h | 🔴 Below 90% | 🟢 Recovered above 95% |
| Disk usage | 💾 Above 90% | auto-clears at 85% |

### 1. Create Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → save **API token**
2. Open [@userinfobot](https://t.me/userinfobot) → save **Chat ID**

### 2. Install Monitor Script

```bash
sudo tee /home/ubuntu/monad-monitor.sh > /dev/null << 'EOF'
#!/bin/bash

# === Config ===
TG_API="YOUR_BOT_TOKEN"
TG_CHAT="YOUR_CHAT_ID"
STATE_FILE="/tmp/monad-monitor-state"
NODE_NAME="Monad | POSTHUMAN"
SERVICES=("monad-bft" "monad-execution" "monad-rpc")
UPTIME_FILE="/tmp/monad-uptime-log"
UPTIME_CRIT=90
UPTIME_OK=95

# === Helpers ===
send_tg() {
  curl -s -X POST "https://api.telegram.org/bot${TG_API}/sendMessage" \
    -d chat_id="${TG_CHAT}" -d parse_mode="HTML" \
    -d text="$1" > /dev/null 2>&1
}
get_prev() { grep "^$1=" "$STATE_FILE" 2>/dev/null | cut -d= -f2-; }
set_state() {
  touch "$STATE_FILE"
  if grep -q "^$1=" "$STATE_FILE" 2>/dev/null; then
    sed -i "s|^$1=.*|$1=$2|" "$STATE_FILE"
  else
    echo "$1=$2" >> "$STATE_FILE"
  fi
}

# === 1. Service checks ===
alerts=""
recoveries=""

for svc in "${SERVICES[@]}"; do
  active=$(systemctl is-active "$svc" 2>/dev/null)
  failed=$(systemctl is-failed "$svc" 2>/dev/null)
  prev=$(get_prev "svc_${svc}")
  if [ "$active" != "active" ] || [ "$failed" = "failed" ]; then
    if [ "$prev" != "down" ]; then
      alerts="${alerts}\n🔴 <b>${svc}</b> is <b>${active}</b>"
      set_state "svc_${svc}" "down"
    fi
  else
    if [ "$prev" = "down" ]; then
      recoveries="${recoveries}\n🟢 <b>${svc}</b> recovered"
    fi
    set_state "svc_${svc}" "ok"
  fi
done

# === 2. Block progress (10 min stuck) ===
latest_block=$(journalctl -u monad-execution --no-pager -o cat --since "3 min ago" 2>/dev/null \
  | grep -oP "Run to block= \K[0-9]+" | tail -1)
now=$(date +%s)

if [ -n "$latest_block" ]; then
  prev_block=$(get_prev "last_block")
  prev_block_time=$(get_prev "last_block_time")
  if [ "$latest_block" != "$prev_block" ]; then
    set_state "last_block" "$latest_block"
    set_state "last_block_time" "$now"
    if [ "$(get_prev stuck)" = "yes" ]; then
      recoveries="${recoveries}\n🟢 Sync resumed at block <b>${latest_block}</b>"
      set_state "stuck" "no"
    fi
  else
    if [ -n "$prev_block_time" ]; then
      diff=$(( now - prev_block_time ))
      if [ "$diff" -gt 600 ] && [ "$(get_prev stuck)" != "yes" ]; then
        alerts="${alerts}\n⚠️ Node stuck at block <b>${latest_block}</b> for $(( diff/60 )) min"
        set_state "stuck" "yes"
      fi
    fi
  fi
fi

# === 3. Critical log patterns ===
core_dump=$(journalctl -u monad-bft --no-pager -o cat --since "25 min ago" 2>/dev/null \
  | grep -c "core-dump\|channel never closed\|30000 blocks older" 2>/dev/null || echo 0)
if [ "$core_dump" -gt 0 ] && [ "$(get_prev coredump_alert)" != "yes" ]; then
  alerts="${alerts}\n💥 Critical error in monad-bft logs (core-dump or sync failure)"
  set_state "coredump_alert" "yes"
elif [ "$core_dump" -eq 0 ]; then
  set_state "coredump_alert" "no"
fi

# === 4. Uptime tracking ===
touch "$UPTIME_FILE"
all_ok=1
for svc in "${SERVICES[@]}"; do
  [ "$(get_prev "svc_${svc}")" = "down" ] && all_ok=0 && break
done
[ -n "$latest_block" ] || all_ok=0
echo "${now} ${all_ok}" >> "$UPTIME_FILE"

cutoff_7d=$(( now - 604800 ))
cutoff_24h=$(( now - 86400 ))
tmp=$(awk -v c="$cutoff_7d" '$1 >= c' "$UPTIME_FILE")
echo "$tmp" > "$UPTIME_FILE"

calc_uptime() {
  local since=$1 total ok
  total=$(awk -v c="$since" '$1 >= c {count++} END {print count+0}' "$UPTIME_FILE")
  ok=$(awk -v c="$since" '$1 >= c && $2==1 {count++} END {print count+0}' "$UPTIME_FILE")
  [ "$total" -eq 0 ] && echo 100 && return
  echo $(( ok * 100 / total ))
}

uptime_24h=$(calc_uptime "$cutoff_24h")
uptime_7d=$(calc_uptime "$cutoff_7d")
prev_uptime_alert=$(get_prev "uptime_alert")

if [ "$uptime_24h" -lt "$UPTIME_CRIT" ]; then
  if [ "$prev_uptime_alert" != "crit" ]; then
    alerts="${alerts}\n📉 Uptime 24h: <b>${uptime_24h}%</b> | 7d: <b>${uptime_7d}%</b>"
    set_state "uptime_alert" "crit"
  fi
elif [ "$uptime_24h" -ge "$UPTIME_OK" ]; then
  if [ "$prev_uptime_alert" = "crit" ]; then
    recoveries="${recoveries}\n📈 Uptime recovered: 24h <b>${uptime_24h}%</b> | 7d: <b>${uptime_7d}%</b>"
  fi
  set_state "uptime_alert" "ok"
fi

# === 5. Disk check ===
disk_pct=$(df / | awk 'NR==2{print int($5)}')
if [ "$disk_pct" -gt 90 ] && [ "$(get_prev disk_alert)" != "yes" ]; then
  alerts="${alerts}\n💾 Disk usage <b>${disk_pct}%</b>"
  set_state "disk_alert" "yes"
elif [ "$disk_pct" -le 85 ]; then
  set_state "disk_alert" "no"
fi

# === Send ===
[ -n "$alerts" ] && send_tg "🚨 <b>${NODE_NAME}</b>\n${alerts}"
[ -n "$recoveries" ] && send_tg "✅ <b>${NODE_NAME}</b>\n${recoveries}"
EOF

chmod +x /home/ubuntu/monad-monitor.sh
```

Replace `YOUR_BOT_TOKEN` and `YOUR_CHAT_ID` with your actual values.

### 3. Set Up Systemd Timer

```bash
sudo tee /etc/systemd/system/monad-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Monad Node Monitor

[Service]
Type=oneshot
ExecStart=/home/ubuntu/monad-monitor.sh
User=root
EOF

sudo tee /etc/systemd/system/monad-monitor.timer > /dev/null << 'EOF'
[Unit]
Description=Run Monad Monitor every 10 min

[Timer]
OnBootSec=60
OnUnitActiveSec=600
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now monad-monitor.timer
```

### 4. Test

```bash
# Run manually to verify
sudo bash /home/ubuntu/monad-monitor.sh

# Check timer
systemctl list-timers monad-monitor.timer
```
