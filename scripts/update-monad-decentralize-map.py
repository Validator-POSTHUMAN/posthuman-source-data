#!/usr/bin/env python3
"""Update Monad decentralization map data files.

The map intentionally includes only public infrastructure:
- official Monad bootstrap peers from the public node.toml;
- approximate validator locations and ASN data from a public registry;
- public JSON-RPC endpoints and their current DNS edge IPs.

Registry-derived validator points must not include validator IPs, P2P endpoints,
auth addresses, or secp keys. Explicit operator-approved public validator
endpoints may be configured separately. Private sentry and internal topology
addresses must not be added.
Observed peers are imported only from public Monad peer-discovery records and
filtered to globally routable addresses.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import math
import socket
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

NETWORKS: dict[str, dict[str, Any]] = {
    "monad": {
        "title": "Monad Mainnet",
        "network": "Monad Mainnet",
        "network_id": "monad-mainnet",
        "chain_id": "143",
        "config_url": "https://bucket.monadinfra.com/config/mainnet/latest/node.toml",
        "validator_registry_url": "https://mon.stake-manager.net/monad-validators.json",
        "validator_registry_min_count": 196,
        "observed_peer_sources": [
            {
                "label": "POSTHUMAN mainnet node public peer-discovery cache",
                "ssh_host": "root@46.166.169.82",
                "path": "/home/monad/monad-bft/config/peers.toml",
            },
        ],
        "log_peer_sources": [
            {
                "label": "POSTHUMAN mainnet monad-bft live log remote_addr endpoints",
                "ssh_host": "root@46.166.169.82",
                "unit": "monad-bft",
                "lines": 50000,
            },
        ],
        "rpc_endpoints": [
            {
                "name": "Monad official public RPC",
                "url": "https://rpc.monad.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Monad official public RPC 1",
                "url": "https://rpc1.monad.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Monad official public RPC 2",
                "url": "https://rpc2.monad.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Monad official public RPC 3",
                "url": "https://rpc3.monad.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Monad official public RPC 4",
                "url": "https://rpc4.monad.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "MonadInfra public RPC",
                "url": "https://rpc-mainnet.monadinfra.com",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "POSTHUMAN Monad RPC Gateway edge",
                "url": "https://rpc-monad.posthuman.digital",
                "expected_chain_id": "0x8f",
                "cloudflare_anycast": True,
            },
            {
                "name": "PublicEndpoints Monad RPC edge",
                "url": "https://publicendpoints.com/evm/evm-143/rpc",
                "expected_chain_id": "0x8f",
                "cloudflare_anycast": True,
            },
            {
                "name": "dRPC Monad Mainnet",
                "url": "https://monad-mainnet.drpc.org",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "OnFinality Monad Mainnet public RPC",
                "url": "https://monad-mainnet.api.onfinality.io/public",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Tatum Monad Mainnet gateway",
                "url": "https://monad-mainnet.gateway.tatum.io",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Huginn Monad Mainnet RPC",
                "url": "https://monad-rpc.huginn.tech",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "BloXroute Monad Mainnet RPC",
                "url": "https://monad.rpc.blxrbdn.com",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "SpiderNode Monad Mainnet RPC",
                "url": "https://monad-mainnet-rpc.spidernode.net",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "OriginStake Monad Mainnet RPC",
                "url": "https://infra.originstake.com/monad/evm",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "Sentio Monad Mainnet RPC",
                "url": "https://monad-mainnet.rpc.sentio.xyz",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "SwiftNodes Monad Mainnet RPC",
                "url": "https://rpc.swiftnodes.io/rpc/monad",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "SynergyNodes Monad Mainnet RPC",
                "url": "https://monad-rpc.synergynodes.com",
                "expected_chain_id": "0x8f",
            },
            {
                "name": "HTW Monad Mainnet RPC",
                "url": "https://gm.monad.at.htw.tech",
                "expected_chain_id": "0x8f",
            },
        ],
    },
    "monad-testnet": {
        "title": "Monad Testnet",
        "network": "Monad Testnet",
        "network_id": "monad-testnet",
        "chain_id": "10143",
        "config_url": "https://bucket.monadinfra.com/config/testnet/latest/node.toml",
        "observed_peer_sources": [
            {
                "label": "POSTHUMAN testnet node public peer-discovery cache",
                "ssh_host": "ubuntu@149.86.227.103",
                "path": "/home/monad/monad-bft/config/peers.toml",
            },
        ],
        "log_peer_sources": [
            {
                "label": "POSTHUMAN testnet monad-bft live log remote_addr endpoints",
                "ssh_host": "ubuntu@149.86.227.103",
                "unit": "monad-bft",
                "lines": 50000,
            },
        ],
        "validator_endpoints": [
            {
                "name": "POSTHUMAN Monad testnet validator",
                "endpoint": "149.86.227.103:8000",
                "source": "POSTHUMAN public validator host",
            },
        ],
        "rpc_endpoints": [
            {
                "name": "Monad official testnet public RPC",
                "url": "https://testnet-rpc.monad.xyz",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "MonadInfra testnet public RPC",
                "url": "https://rpc-testnet.monadinfra.com",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "POSTHUMAN Monad Testnet RPC Gateway edge",
                "url": "https://rpc-monad-testnet.posthuman.digital:443",
                "expected_chain_id": "0x279f",
                "cloudflare_anycast": True,
            },
            {
                "name": "PublicEndpoints Monad Testnet RPC edge",
                "url": "https://publicendpoints.com/evm/evm-10143/rpc",
                "expected_chain_id": "0x279f",
                "cloudflare_anycast": True,
            },
            {
                "name": "dRPC Monad Testnet",
                "url": "https://monad-testnet.drpc.org",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "OnFinality Monad Testnet public RPC",
                "url": "https://monad-testnet.api.onfinality.io/public",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "Tatum Monad Testnet gateway",
                "url": "https://monad-testnet.gateway.tatum.io",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "Huginn Monad Testnet RPC",
                "url": "https://monad-testnet-rpc.huginn.tech",
                "expected_chain_id": "0x279f",
            },
            {
                "name": "Ankr Monad Testnet RPC",
                "url": "https://rpc.ankr.com/monad_testnet",
                "expected_chain_id": "0x279f",
            },
        ],
    },
}


GEO_FIELDS = (
    "status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,as,query"
)

EXCLUDED_PUBLIC_IPS = {
    # POSTHUMAN validator hosts. The map should not publish our validator
    # machine IPs as discovered peer topology.
    "5.61.208.27",
    "46.166.169.82",
    "149.86.227.103",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "POSTHUMAN-monad-map-updater/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_bootstrap_peers(toml_text: str) -> list[dict[str, str]]:
    peers: list[dict[str, str]] = []
    pending_comment = ""
    current: dict[str, str] | None = None

    for raw_line in toml_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comment = line[1:].strip()
            if comment:
                pending_comment = comment
            continue
        if line == "[[bootstrap.peers]]":
            if current and current.get("address"):
                peers.append(current)
            current = {"name": pending_comment}
            pending_comment = ""
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        value = value.split("#", 1)[0].strip().strip('"')
        if key in {"address", "auth_port", "record_seq_num", "secp256k1_pubkey"}:
            current[key] = value

    if current and current.get("address"):
        peers.append(current)

    for idx, peer in enumerate(peers, start=1):
        if not peer.get("name"):
            peer["name"] = f"bootstrap-{idx}"
    return peers


def parse_peer_blocks(toml_text: str) -> list[dict[str, str]]:
    peers: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw_line in toml_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line in {"[[peers]]", "[[bootstrap.peers]]"}:
            if current and current.get("address"):
                peers.append(current)
            current = {}
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        value = value.split("#", 1)[0].strip().strip('"')
        if key in {"address", "auth_port", "record_seq_num", "secp256k1_pubkey"}:
            current[key] = value

    if current and current.get("address"):
        peers.append(current)
    return peers


def parse_validator_registry(
    payload: str,
    source_url: str,
    minimum_count: int,
) -> tuple[list[dict[str, Any]], str]:
    try:
        document = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid validator registry JSON from {source_url}") from exc

    if not isinstance(document, dict) or not isinstance(document.get("validators"), list):
        raise ValueError(f"validator registry from {source_url} has no validators array")

    rows = document["validators"]
    if len(rows) < minimum_count:
        raise ValueError(
            f"validator registry from {source_url} has {len(rows)} rows; "
            f"minimum expected is {minimum_count}"
        )

    source_updated = document.get("updated")
    if not isinstance(source_updated, str) or not source_updated.strip():
        raise ValueError(f"validator registry from {source_url} has no update timestamp")

    validators: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"validator registry row {index} is not an object")

        validator_id = row.get("id")
        if isinstance(validator_id, bool) or not isinstance(validator_id, int) or validator_id <= 0:
            raise ValueError(f"validator registry row {index} has invalid id")
        if validator_id in seen_ids:
            raise ValueError(f"validator registry has duplicate validator id {validator_id}")
        seen_ids.add(validator_id)

        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"validator {validator_id} has no name")

        raw_lat = row.get("lat")
        raw_lon = row.get("lon")
        if isinstance(raw_lat, bool) or isinstance(raw_lon, bool):
            raise ValueError(f"validator {validator_id} has invalid coordinates")
        try:
            lat = float(raw_lat)
            lon = float(raw_lon)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"validator {validator_id} has invalid coordinates") from exc
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"validator {validator_id} has out-of-range coordinates")

        country_code = row.get("geo_country")
        if not isinstance(country_code, str) or not country_code.strip():
            raise ValueError(f"validator {validator_id} has no country code")

        provider = row.get("asn_org")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError(f"validator {validator_id} has no ASN provider")
        asn_number = row.get("asn")
        if isinstance(asn_number, bool) or not isinstance(asn_number, int) or asn_number <= 0:
            raise ValueError(f"validator {validator_id} has invalid ASN")

        if not isinstance(row.get("active"), bool) or not isinstance(row.get("decommissioned"), bool):
            raise ValueError(f"validator {validator_id} has invalid lifecycle flags")

        validators.append(
            {
                **row,
                "id": validator_id,
                "name": name.strip(),
                "lat": lat,
                "lon": lon,
                "geo_country": country_code.strip().upper(),
                "asn_org": provider.strip(),
                "asn": asn_number,
            }
        )

    return sorted(validators, key=lambda row: row["id"]), source_updated


def build_validator_registry_points(
    cfg: dict[str, Any],
    now: str,
) -> list[dict[str, Any]]:
    source_url = cfg.get("validator_registry_url")
    if not source_url:
        return []

    rows, source_updated = parse_validator_registry(
        fetch_text(source_url),
        source_url,
        int(cfg.get("validator_registry_min_count", 1)),
    )
    points: list[dict[str, Any]] = []
    for row in rows:
        active = row.get("active") is True and row.get("decommissioned") is not True
        provider = row.get("asn_org") if isinstance(row.get("asn_org"), str) else ""
        asn_number = row.get("asn")
        asn = f"AS{asn_number} {provider}" if isinstance(asn_number, int) else provider
        website = row.get("website") if isinstance(row.get("website"), str) else ""

        metadata: dict[str, str | int | float | bool | None] = {
            "validator_id": row["id"],
            "rank": row.get("rank") if isinstance(row.get("rank"), int) else None,
            "active": active,
            "commission_percent": row.get("commission")
            if isinstance(row.get("commission"), (int, float)) and not isinstance(row.get("commission"), bool)
            else None,
            "stake_mon": row.get("stake")
            if isinstance(row.get("stake"), (int, float)) and not isinstance(row.get("stake"), bool)
            else None,
            "website": website or None,
            "registry_updated_at": source_updated,
        }
        points.append(
            {
                "id": f"{cfg['network_id']}-validator-{row['id']}",
                "network_id": cfg["network_id"],
                "type": "validator",
                "name": row["name"],
                "status": "active" if active else "inactive",
                "city": row.get("geo_city") or "",
                "country": row["geo_country"],
                "country_code": row["geo_country"],
                "lat": row["lat"],
                "lon": row["lon"],
                "provider": provider,
                "asn": asn,
                "source": source_url,
                "last_checked_at": now,
                "description": (
                    "Monad validator from the public stake-manager registry. "
                    "Location and ASN are registry-provided and may be approximate."
                ),
                "metadata": metadata,
            }
        )
    return points


def fetch_observed_peer_source(source: dict[str, str]) -> str:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        source["ssh_host"],
        f"sudo -n cat {source['path']}",
    ]
    return subprocess.check_output(cmd, text=True, timeout=30)


def fetch_log_peer_source(source: dict[str, Any]) -> list[str]:
    unit = source.get("unit", "monad-bft")
    lines = int(source.get("lines", 50000))
    remote_cmd = (
        f"sudo -n journalctl -u {unit} -n {lines} --no-pager 2>/dev/null "
        r"| grep -Eo '([0-9]{1,3}.){3}[0-9]{1,3}:[0-9]{2,5}' "
        "| sort -u"
    )
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        source["ssh_host"],
        remote_cmd,
    ]
    output = subprocess.check_output(cmd, text=True, timeout=60)
    return [line.strip() for line in output.splitlines() if line.strip()]


def split_endpoint(endpoint: str) -> tuple[str, int]:
    host, port = endpoint.rsplit(":", 1)
    return host.strip("[]"), int(port)


def tcp_latency_ms(host: str, port: int, timeout: float = 2.5) -> int | None:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return int((time.perf_counter() - start) * 1000)
    except OSError:
        return None


def is_publishable_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_global and host not in EXCLUDED_PUBLIC_IPS


def resolve_host(host: str) -> list[str]:
    ips: set[str] = set()
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            infos = socket.getaddrinfo(host, None, family, socket.SOCK_STREAM)
        except socket.gaierror:
            continue
        for info in infos:
            ips.add(info[4][0])
    return sorted(ips, key=lambda ip: (ipaddress.ip_address(ip).version, ip))


def rpc_health(url: str, expected_chain_id: str) -> tuple[str, int | None, str | None]:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "POSTHUMAN-monad-map-updater/1.0",
        },
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            body = json.loads(response.read().decode("utf-8"))
        latency = int((time.perf_counter() - start) * 1000)
        result = body.get("result")
        status = "online" if result == expected_chain_id else "degraded"
        return status, latency, result
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return "offline", None, None


def fetch_geo_batch(ips: list[str]) -> dict[str, dict[str, Any]]:
    if not ips:
        return {}
    url = f"http://ip-api.com/batch?fields={GEO_FIELDS}"
    req = urllib.request.Request(
        url,
        data=json.dumps(ips).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "POSTHUMAN-monad-map-updater/1.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return {}
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if isinstance(row, dict) and row.get("status") == "success" and row.get("query"):
            result[str(row["query"])] = row
    return result


def prime_geo_cache(ips: list[str], cache: dict[str, dict[str, Any]]) -> None:
    missing = [ip for ip in dict.fromkeys(ips) if ip not in cache]
    for start in range(0, len(missing), 100):
        chunk = missing[start : start + 100]
        cache.update(fetch_geo_batch(chunk))
        if start + 100 < len(missing):
            time.sleep(1)


def geo_lookup(ip: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if ip in cache:
        return cache[ip]
    url = f"http://ip-api.com/json/{ip}?fields={GEO_FIELDS}"
    try:
        data = json.loads(fetch_text(url, timeout=10))
        if data.get("status") != "success":
            result: dict[str, Any] = {}
        else:
            result = data
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        result = {}
    cache[ip] = result
    time.sleep(0.25)
    return result


def apply_geo(point: dict[str, Any], ip: str, geo_cache: dict[str, dict[str, Any]]) -> None:
    geo = geo_lookup(ip, geo_cache)
    if not geo:
        return
    point.update(
        {
            "city": geo.get("city") or "",
            "region": geo.get("regionName") or "",
            "country": geo.get("country") or "",
            "country_code": geo.get("countryCode") or "",
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "provider": geo.get("isp") or "",
            "asn": geo.get("as") or "",
            "timezone": geo.get("timezone") or "",
        }
    )


def source_entries(
    config_url: str,
    rpc_endpoints: list[dict[str, Any]],
    validator_registry_url: str | None = None,
) -> list[dict[str, str]]:
    entries = [{"label": "Official Monad node config", "url": config_url}]
    if validator_registry_url:
        entries.append({"label": "Monad validator registry", "url": validator_registry_url})
    for endpoint in rpc_endpoints:
        entries.append({"label": endpoint["name"].replace(" edge", ""), "url": endpoint["url"]})
    entries.append({"label": "GeoIP lookup", "url": "http://ip-api.com/"})
    return entries


def check_peer_latencies(peers: list[dict[str, Any]]) -> dict[str, int | None]:
    result: dict[str, int | None] = {}
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {
            executor.submit(tcp_latency_ms, peer["host"], peer["port"], 1.5): peer["endpoint"]
            for peer in peers
        }
        for future in as_completed(futures):
            endpoint = futures[future]
            try:
                result[endpoint] = future.result()
            except Exception:
                result[endpoint] = None
    return result


def validator_registry_ids(data: dict[str, Any], source_url: str) -> set[int]:
    validator_ids: set[int] = set()
    for point in data.get("points", []):
        if not isinstance(point, dict) or point.get("type") != "validator":
            continue
        if point.get("source") != source_url:
            continue
        metadata = point.get("metadata")
        validator_id = metadata.get("validator_id") if isinstance(metadata, dict) else None
        if isinstance(validator_id, bool) or not isinstance(validator_id, int):
            raise ValueError("existing registry validator point has invalid validator_id")
        if validator_id in validator_ids:
            raise ValueError(f"existing map has duplicate registry validator id {validator_id}")
        validator_ids.add(validator_id)
    return validator_ids


def validate_validator_registry_continuity(
    path: Path,
    data: dict[str, Any],
    cfg: dict[str, Any],
) -> None:
    source_url = cfg.get("validator_registry_url")
    if not source_url or not path.exists():
        return

    try:
        previous = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot validate existing validator registry continuity in {path}") from exc
    if not isinstance(previous, dict):
        raise ValueError(f"existing map {path} is not a JSON object")

    previous_ids = validator_registry_ids(previous, source_url)
    if not previous_ids:
        return
    current_ids = validator_registry_ids(data, source_url)
    missing_ids = sorted(previous_ids - current_ids)
    if missing_ids:
        preview = ", ".join(str(validator_id) for validator_id in missing_ids[:10])
        suffix = "..." if len(missing_ids) > 10 else ""
        raise ValueError(
            f"validator registry continuity check rejected {len(missing_ids)} omitted ids: "
            f"{preview}{suffix}"
        )


def validator_privacy_description(cfg: dict[str, Any]) -> str:
    if cfg.get("validator_registry_url") and not cfg.get("validator_endpoints"):
        return (
            "registry markers use approximate locations and ASN data; "
            "validator IPs and P2P endpoints are not published"
        )
    if cfg.get("validator_endpoints"):
        return "operator-approved public validator P2P endpoints are published"
    return "no validator markers are published"


def build_network_map(name: str, cfg: dict[str, Any], geo_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    now = utc_now()
    config_text = fetch_text(cfg["config_url"])
    bootstrap_peers = parse_bootstrap_peers(config_text)
    points: list[dict[str, Any]] = []
    geo_ips: list[str] = []

    for idx, peer in enumerate(bootstrap_peers, start=1):
        host, port = split_endpoint(peer["address"])
        latency = tcp_latency_ms(host, port)
        geo_ips.append(host)
        point = {
            "id": f"{cfg['network_id']}-bootstrap-{idx}",
            "network_id": cfg["network_id"],
            "type": "bootstrap",
            "name": peer["name"],
            "status": "online" if latency is not None else "unknown",
            "endpoint": peer["address"],
            "ip": host,
            "port": str(port),
            "latency_ms": latency,
            "source": cfg["config_url"],
            "last_checked_at": now,
            "description": "Public bootstrap peer from official Monad node configuration.",
            "metadata": {
                "auth_port": peer.get("auth_port", ""),
                "record_seq_num": peer.get("record_seq_num", ""),
            },
        }
        apply_geo(point, host, geo_cache)
        points.append(point)

    validator_registry_points = build_validator_registry_points(cfg, now)
    points.extend(validator_registry_points)

    rpc_count = 0
    for endpoint in cfg["rpc_endpoints"]:
        status, latency, chain_id_response = rpc_health(endpoint["url"], endpoint["expected_chain_id"])
        host = urllib.parse.urlparse(endpoint["url"]).hostname
        if not host:
            continue
        ips = resolve_host(host)
        geo_ips.extend(ips)
        for ip in ips:
            rpc_count += 1
            point = {
                "id": f"{cfg['network_id']}-rpc-{rpc_count}",
                "network_id": cfg["network_id"],
                "type": "rpc",
                "name": endpoint["name"],
                "status": status,
                "endpoint": endpoint["url"],
                "ip": ip,
                "latency_ms": latency,
                "source": "DNS + eth_chainId health check",
                "last_checked_at": now,
                "description": "Public JSON-RPC endpoint. Cloudflare anycast points represent edge IPs, not validator/sentry topology.",
                "metadata": {
                    "chain_id_response": chain_id_response,
                    "cloudflare_anycast": bool(endpoint.get("cloudflare_anycast", False)),
                    "dns_host": host,
                    "ip_family": f"IPv{ipaddress.ip_address(ip).version}",
                },
            }
            apply_geo(point, ip, geo_cache)
            points.append(point)

    validator_count = len(validator_registry_points)
    for validator in cfg.get("validator_endpoints", []):
        try:
            host, port = split_endpoint(validator["endpoint"])
        except (ValueError, TypeError):
            continue
        try:
            validator_ip = ipaddress.ip_address(host)
        except ValueError:
            continue
        if not validator_ip.is_global:
            continue
        validator_count += 1
        latency = tcp_latency_ms(host, port)
        geo_ips.append(host)
        point = {
            "id": f"{cfg['network_id']}-validator-{validator_count}",
            "network_id": cfg["network_id"],
            "type": "validator",
            "name": validator["name"],
            "status": "online" if latency is not None else "unknown",
            "endpoint": validator["endpoint"],
            "ip": host,
            "port": str(port),
            "latency_ms": latency,
            "source": validator.get("source", "public validator endpoint"),
            "last_checked_at": now,
            "description": "Public validator p2p endpoint added by operator request.",
            "metadata": {
                "collection": "public validator endpoint",
            },
        }
        apply_geo(point, host, geo_cache)
        points.append(point)

    observed_candidates: dict[str, dict[str, Any]] = {}
    for source in cfg.get("observed_peer_sources", []):
        try:
            source_text = fetch_observed_peer_source(source)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        for peer in parse_peer_blocks(source_text):
            try:
                host, port = split_endpoint(peer["address"])
            except (ValueError, TypeError):
                continue
            if not is_publishable_ip(host):
                continue
            observed_candidates[peer["address"]] = {
                "endpoint": peer["address"],
                "host": host,
                "port": port,
                "auth_port": peer.get("auth_port", ""),
                "record_seq_num": peer.get("record_seq_num", ""),
                "source_label": source["label"],
            }

    observed_peers = sorted(observed_candidates.values(), key=lambda item: item["endpoint"])
    geo_ips.extend(peer["host"] for peer in observed_peers)
    prime_geo_cache(geo_ips, geo_cache)
    peer_latencies = check_peer_latencies(observed_peers)

    observed_count = 0
    for peer in observed_peers:
        observed_count += 1
        latency = peer_latencies.get(peer["endpoint"])
        point = {
            "id": f"{cfg['network_id']}-observed-peer-{observed_count}",
            "network_id": cfg["network_id"],
            "type": "observed_peer",
            "name": f"Observed public peer {observed_count}",
            "status": "online" if latency is not None else "observed",
            "endpoint": peer["endpoint"],
            "ip": peer["host"],
            "port": str(peer["port"]),
            "latency_ms": latency,
            "source": peer["source_label"],
            "last_checked_at": now,
            "description": "Publicly advertised Monad peer discovered through peer discovery. POSTHUMAN validator host IPs and non-global addresses are excluded.",
            "metadata": {
                "auth_port": peer["auth_port"],
                "record_seq_num": peer["record_seq_num"],
                "collection": "public peer-discovery cache",
            },
        }
        apply_geo(point, peer["host"], geo_cache)
        points.append(point)

    existing_endpoints = {point.get("endpoint") for point in points}
    log_candidates: dict[str, dict[str, Any]] = {}
    for source in cfg.get("log_peer_sources", []):
        try:
            endpoints = fetch_log_peer_source(source)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        for endpoint in endpoints:
            if endpoint in existing_endpoints:
                continue
            try:
                host, port = split_endpoint(endpoint)
            except (ValueError, TypeError):
                continue
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                continue
            if not ip.is_global:
                continue
            log_candidates[endpoint] = {
                "endpoint": endpoint,
                "host": host,
                "port": port,
                "source_label": source["label"],
            }

    log_peers = sorted(log_candidates.values(), key=lambda item: item["endpoint"])
    geo_ips.extend(peer["host"] for peer in log_peers)
    prime_geo_cache(geo_ips, geo_cache)
    log_latencies = check_peer_latencies(log_peers)

    log_observed_count = 0
    for peer in log_peers:
        log_observed_count += 1
        latency = log_latencies.get(peer["endpoint"])
        point = {
            "id": f"{cfg['network_id']}-log-observed-peer-{log_observed_count}",
            "network_id": cfg["network_id"],
            "type": "log_observed_peer",
            "name": f"Log observed public peer {log_observed_count}",
            "status": "online" if latency is not None else "observed",
            "endpoint": peer["endpoint"],
            "ip": peer["host"],
            "port": str(peer["port"]),
            "latency_ms": latency,
            "source": peer["source_label"],
            "last_checked_at": now,
            "description": "Public endpoint observed in live Monad wireauth logs. Non-global addresses are excluded.",
            "metadata": {
                "collection": "public live log remote_addr endpoint",
            },
        }
        apply_geo(point, peer["host"], geo_cache)
        points.append(point)

    countries = {p.get("country_code") for p in points if p.get("country_code")}
    providers = {p.get("provider") for p in points if p.get("provider")}
    return {
        "schema": "posthuman-decentralization-map/v1",
        "network": cfg["network"],
        "network_id": cfg["network_id"],
        "chain_id": cfg["chain_id"],
        "updated_at": now,
        "privacy": {
            "sentry_topology": "not published",
            "public_endpoints": "RPC and official bootstrap peers",
            "validator_points": validator_privacy_description(cfg),
            "validator_registry": "public stake-manager registry when configured",
            "validator_endpoints": "operator-approved public validator p2p endpoints when configured",
            "observed_public_peers": "globally routable peers from Monad peer-discovery cache",
            "log_observed_public_peers": "globally routable endpoints extracted from live Monad logs",
            "note": "The map uses only the public sources configured for this network. Private sentry topology and non-global peer addresses are excluded.",
        },
        "sources": source_entries(
            cfg["config_url"],
            cfg["rpc_endpoints"],
            cfg.get("validator_registry_url"),
        ),
        "summary": {
            "points": len(points),
            "bootstrap_peers": len(bootstrap_peers),
            "validators": validator_count,
            "observed_peers": observed_count,
            "log_observed_peers": log_observed_count,
            "rpc_endpoints": rpc_count,
            "countries": len(countries),
            "providers": len(providers),
        },
        "points": points,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", choices=sorted(NETWORKS), action="append")
    parser.add_argument("--check", action="store_true", help="Build data without writing files")
    args = parser.parse_args()

    names = args.network or sorted(NETWORKS)
    geo_cache: dict[str, dict[str, Any]] = {}
    for name in names:
        data = build_network_map(name, NETWORKS[name], geo_cache)
        path = ROOT / name / "decentralize-map.json"
        validate_validator_registry_continuity(path, data, NETWORKS[name])
        rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            print(
                f"{name}: points={data['summary']['points']} "
                f"bootstrap={data['summary']['bootstrap_peers']} "
                f"validators={data['summary']['validators']} "
                f"observed={data['summary']['observed_peers']} "
                f"log_observed={data['summary']['log_observed_peers']} "
                f"rpc={data['summary']['rpc_endpoints']}"
            )
            continue
        path.write_text(rendered)
        print(f"updated {path.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
