# Monad Testnet Node Monitoring

## Overview

| Feature | Status |
|---------|--------|
| Telegram Alerts | ✅ Available |
| Grafana Dashboard | 🔧 Coming Soon |
| Prometheus Metrics | 🔧 Coming Soon |

## Telegram Alerts

Lightweight monitoring script that sends alerts to your Telegram when something goes wrong. Runs every 15 minutes via systemd timer, fires **only on state changes** — no spam.

**What it monitors:**

| Check | Alert Trigger | Recovery |
|-------|---------------|----------|
| `monad-bft` service | 🔴 Service down | 🟢 Service recovered |
| `monad-execution` service | 🔴 Service down | 🟢 Service recovered |
| `monad-rpc` service | 🔴 Service down | 🟢 Service recovered |
| Consensus tip | ⚠️ Stuck > 30 min | 🟢 Sync resumed |
| Disk usage | 💾 Above 90% | Auto-clears at 85% |
| RAM usage | 🧠 Above 95% | Auto-clears at 85% |

### 1. Create Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot`, follow prompts — save the **API token**
3. Open [@userinfobot](https://t.me/userinfobot) — save your **Chat ID**

### 2. Install Monitor Script

````bash
cat > /home/monad/monitor.sh << 'EOF'
#!/bin/bash
TG_API="YOUR_BOT_TOKEN"
TG_CHAT="YOUR_CHAT_ID"
STATE_FILE="/tmp/monad-monitor-state"
SERVICES=("monad-bft" "monad-execution" "monad-rpc")

send_tg() {
  curl -s -X POST "https://api.telegram.org/bot${TG_API}/sendMessage" \
    -d chat_id="${TG_CHAT}" -d parse_mode="HTML" -d text="$1" > /dev/null 2>&1
}
get_prev() { grep "^$1=" "$STATE_FILE" 2>/dev/null | cut -d= -f2-; }
set_state() {
  touch "$STATE_FILE"
  grep -q "^$1=" "$STATE_FILE" 2>/dev/null \
    && sed -i "s|^$1=.*|$1=$2|" "$STATE_FILE" \
    || echo "$1=$2" >> "$STATE_FILE"
}

alerts="" recoveries=""
for svc in "${SERVICES[@]}"; do
  status=$(systemctl is-active "$svc" 2>/dev/null)
  prev=$(get_prev "svc_${svc}")
  if [ "$status" != "active" ] && [ "$prev" != "down" ]; then
    alerts="${alerts}\n🔴 <b>${svc}</b> is <b>${status}</b>"
    set_state "svc_${svc}" "down"
  elif [ "$status" = "active" ] && [ "$prev" = "down" ]; then
    recoveries="${recoveries}\n🟢 <b>${svc}</b> recovered"
    set_state "svc_${svc}" "ok"
  else set_state "svc_${svc}" "ok"; fi
done

consensus_tip=$(journalctl -u monad-bft --no-pager -o cat --since "3 min ago" 2>/dev/null \
  | grep -oP '"consensus_tip":"?\K[0-9]+' | tail -1)
if [ -n "$consensus_tip" ]; then
  prev_tip=$(get_prev "last_tip"); now=$(date +%s)
  if [ "$consensus_tip" != "$prev_tip" ]; then
    set_state "last_tip" "$consensus_tip"; set_state "last_tip_time" "$now"
    [ "$(get_prev stuck)" = "yes" ] && recoveries="${recoveries}\n🟢 Sync resumed, tip: <b>${consensus_tip}</b>"
    set_state "stuck" "no"
  else
    prev_time=$(get_prev "last_tip_time")
    [ -n "$prev_time" ] && diff=$((now - prev_time)) \
      && [ "$diff" -gt 1800 ] && [ "$(get_prev stuck)" != "yes" ] \
      && alerts="${alerts}\n⚠️ Stuck at block <b>${consensus_tip}</b> for ${diff}s" \
      && set_state "stuck" "yes"
  fi
fi

disk_pct=$(df / | awk 'NR==2{print int($5)}')
[ "$disk_pct" -gt 90 ] && [ "$(get_prev disk_alert)" != "yes" ] \
  && alerts="${alerts}\n💾 Disk usage <b>${disk_pct}%</b>" && set_state "disk_alert" "yes"
[ "$disk_pct" -le 85 ] && set_state "disk_alert" "no"

ram_pct=$(free | awk '/Mem:/{printf "%d", $3/$2*100}')
[ "$ram_pct" -gt 95 ] && [ "$(get_prev ram_alert)" != "yes" ] \
  && alerts="${alerts}\n🧠 RAM usage <b>${ram_pct}%</b>" && set_state "ram_alert" "yes"
[ "$ram_pct" -le 85 ] && set_state "ram_alert" "no"

[ -n "$alerts" ] && send_tg "⚠️ <b>Monad Node</b>${alerts}"
[ -n "$recoveries" ] && send_tg "✅ <b>Monad Node</b>${recoveries}"
EOF
chmod +x /home/monad/monitor.sh
````

Replace `YOUR_BOT_TOKEN` and `YOUR_CHAT_ID` with your actual values.

### 3. Set Up Systemd Timer

````bash
sudo tee /etc/systemd/system/monad-monitor.service > /dev/null <<EOF
[Unit]
Description=Monad Node Monitor
[Service]
Type=oneshot
ExecStart=/home/monad/monitor.sh
User=root
EOF

sudo tee /etc/systemd/system/monad-monitor.timer > /dev/null <<EOF
[Unit]
Description=Run Monad Monitor every 15 min
[Timer]
OnBootSec=60
OnUnitActiveSec=900
Persistent=true
[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now monad-monitor.timer
````

### 4. Test

````bash
# Run manually to verify
sudo /home/monad/monitor.sh

# Check timer status
systemctl list-timers monad-monitor.timer
````

---

## Grafana Dashboard

> 🔧 **In Development** — Posthuman is building a dedicated Grafana dashboard for Monad nodes with real-time metrics:
>
> - Consensus tip & sync progress
> - Block production rate
> - Peer count & network health
> - System resources (CPU, RAM, Disk I/O, Network)
> - TrieDB performance
>
> Stay tuned — will be available as a one-click import for Grafana.
