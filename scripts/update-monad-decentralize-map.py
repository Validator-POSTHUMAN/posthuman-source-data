#!/usr/bin/env python3
"""Update Monad decentralization map data files.

The map intentionally includes only public infrastructure:
- official Monad bootstrap peers from the public node.toml;
- public JSON-RPC endpoints and their current DNS edge IPs.

Private validator, sentry, and internal topology addresses must not be added.
Observed peers are imported only from public Monad peer-discovery records and
filtered to globally routable addresses.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
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
        "observed_peer_sources": [
            {
                "label": "POSTHUMAN mainnet node public peer-discovery cache",
                "ssh_host": "ubuntu@5.61.208.27",
                "path": "/home/monad/monad-bft/config/peers.toml",
            },
        ],
        "rpc_endpoints": [
            {
                "name": "Monad official public RPC",
                "url": "https://rpc.monad.xyz",
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
        "rpc_endpoints": [
            {
                "name": "Monad official testnet public RPC",
                "url": "https://testnet-rpc.monad.xyz",
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


def source_entries(config_url: str, rpc_endpoints: list[dict[str, Any]]) -> list[dict[str, str]]:
    entries = [{"label": "Official Monad node config", "url": config_url}]
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

    countries = {p.get("country_code") for p in points if p.get("country_code")}
    providers = {p.get("provider") for p in points if p.get("provider")}
    return {
        "schema": "posthuman-decentralization-map/v1",
        "network": cfg["network"],
        "network_id": cfg["network_id"],
        "chain_id": cfg["chain_id"],
        "updated_at": now,
        "privacy": {
            "raw_validator_ips": "not published",
            "sentry_topology": "not published",
            "public_endpoints": "RPC and official bootstrap peers",
            "observed_public_peers": "globally routable peers from Monad peer-discovery cache",
            "note": "The map uses public RPC DNS, official Monad bootstrap peers, and globally routable observed peer-discovery records. Private validator/sentry IPs from logs are intentionally excluded.",
        },
        "sources": source_entries(cfg["config_url"], cfg["rpc_endpoints"]),
        "summary": {
            "points": len(points),
            "bootstrap_peers": len(bootstrap_peers),
            "observed_peers": observed_count,
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
        rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            print(
                f"{name}: points={data['summary']['points']} "
                f"bootstrap={data['summary']['bootstrap_peers']} "
                f"observed={data['summary']['observed_peers']} "
                f"rpc={data['summary']['rpc_endpoints']}"
            )
            continue
        path.write_text(rendered)
        print(f"updated {path.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
