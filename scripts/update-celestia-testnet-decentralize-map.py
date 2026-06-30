#!/usr/bin/env python3
"""Update Celestia Mocha testnet decentralization map data.

The map intentionally includes only public infrastructure:
- POSTHUMAN and chain-registry public RPC DNS endpoints;
- chain-registry public seeds and persistent peers;
- globally routable peers reported by public Mocha testnet RPC `/net_info`.

Do not add private validator, sentry, or local non-Mocha addrbook data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHAIN = "celestia-testnet"
NETWORK = "Celestia Mocha Testnet"
NETWORK_ID = "celestia-testnet-mocha-4"
CHAIN_ID = "mocha-4"
CHAIN_REGISTRY_URL = "https://raw.githubusercontent.com/cosmos/chain-registry/master/testnets/celestiatestnet3/chain.json"
GEO_FIELDS = (
    "status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,as,query"
)
USER_AGENT = "POSTHUMAN-celestia-testnet-map-updater/1.0"

POSTHUMAN_RPC_ENDPOINTS = [
    {
        "address": "https://rpc-celestia-testnet.posthuman.digital",
        "provider": "POSTHUMAN",
    },
]

NET_INFO_RPC_URLS = [
    "https://rpc-celestia-testnet.posthuman.digital",
    "https://rpc-mocha.pops.one",
    "https://celestia-testnet-rpc.publicnode.com:443",
    "https://rpc-mocha-full.avril14th.org",
    "https://celestia-testnet-rpc.itrocket.net",
    "https://rpc-celestia-testnet.cryptech.com.ua",
    "https://rpc.celestia.testnet.dteam.tech:443",
    "https://celestia-testnet-rpc.stakeandrelax.net",
]


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def status_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/status"


def net_info_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/net_info"


def split_host_port(
    endpoint: str, default_port: int | None = None
) -> tuple[str, int | None]:
    endpoint = endpoint.strip()
    if not endpoint:
        return "", default_port
    if endpoint.startswith("tcp://"):
        endpoint = endpoint[6:]
    if endpoint.startswith("["):
        host, _, rest = endpoint[1:].partition("]")
        port = rest[1:] if rest.startswith(":") else ""
        return host, int(port) if port else default_port
    if ":" not in endpoint:
        return endpoint, default_port
    host, port = endpoint.rsplit(":", 1)
    try:
        return host.strip("[]"), int(port)
    except ValueError:
        return host.strip("[]"), default_port


def is_global_ip(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_global
    except ValueError:
        return False


def resolve_host(host: str) -> list[str]:
    host = host.strip("[]")
    if is_global_ip(host):
        return [host]
    ips: set[str] = set()
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            infos = socket.getaddrinfo(host, None, family, socket.SOCK_STREAM)
        except socket.gaierror:
            continue
        for info in infos:
            ip = info[4][0]
            if is_global_ip(ip):
                ips.add(ip)
    return sorted(ips, key=lambda value: (ipaddress.ip_address(value).version, value))


def tcp_latency_ms(host: str, port: int | None, timeout: float = 2.5) -> int | None:
    if port is None:
        return None
    started = time.perf_counter()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return int((time.perf_counter() - started) * 1000)
    except OSError:
        return None


def rpc_status(base_url: str) -> tuple[str, int | None, str | None, str | None]:
    started = time.perf_counter()
    try:
        data = fetch_json(status_url(base_url), timeout=12)
        latency = int((time.perf_counter() - started) * 1000)
        result = data.get("result", {}) if isinstance(data, dict) else {}
        chain_id = result.get("node_info", {}).get("network")
        moniker = result.get("node_info", {}).get("moniker")
        if chain_id == CHAIN_ID:
            return "online", latency, chain_id, moniker
        if chain_id:
            return "degraded", latency, chain_id, moniker
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        pass
    return "unknown", None, None, None


def fetch_net_info(base_url: str) -> list[dict[str, Any]]:
    try:
        data = fetch_json(net_info_url(base_url), timeout=15)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return []
    result = data.get("result", {}) if isinstance(data, dict) else {}
    peers = result.get("peers", [])
    return peers if isinstance(peers, list) else []


def fetch_geo_batch(ips: list[str]) -> dict[str, dict[str, Any]]:
    if not ips:
        return {}
    req = urllib.request.Request(
        f"http://ip-api.com/batch?fields={GEO_FIELDS}",
        data=json.dumps(ips).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return {}
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if (
            isinstance(row, dict)
            and row.get("status") == "success"
            and row.get("query")
        ):
            result[str(row["query"])] = row
    return result


def prime_geo_cache(ips: list[str]) -> dict[str, dict[str, Any]]:
    unique_ips = list(dict.fromkeys(ip for ip in ips if is_global_ip(ip)))
    cache: dict[str, dict[str, Any]] = {}
    for start in range(0, len(unique_ips), 100):
        chunk = unique_ips[start : start + 100]
        cache.update(fetch_geo_batch(chunk))
        if start + 100 < len(unique_ips):
            time.sleep(1)
    return cache


def location_fields(ip: str, geo_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    geo = geo_cache.get(ip, {})
    return {
        "city": geo.get("city") or "Unknown",
        "region": geo.get("regionName") or "",
        "country": geo.get("country") or "Unknown",
        "country_code": geo.get("countryCode") or "",
        "lat": geo.get("lat") or 0,
        "lon": geo.get("lon") or 0,
        "provider": geo.get("isp") or "Unknown",
        "asn": geo.get("as") or "",
        "timezone": geo.get("timezone") or "",
    }


def chain_registry_rpc_endpoints(chain_data: dict[str, Any]) -> list[dict[str, str]]:
    endpoints: list[dict[str, str]] = []
    seen: set[str] = set()
    for endpoint in POSTHUMAN_RPC_ENDPOINTS:
        address = endpoint["address"].rstrip("/")
        seen.add(address)
        endpoints.append({"address": address, "provider": endpoint["provider"]})
    for endpoint in chain_data.get("apis", {}).get("rpc", []):
        if not isinstance(endpoint, dict):
            continue
        address = str(endpoint.get("address") or "").rstrip("/")
        if not address or address in seen:
            continue
        seen.add(address)
        endpoints.append(
            {"address": address, "provider": str(endpoint.get("provider") or "Unknown")}
        )
    return endpoints


def add_registry_peer_candidates(
    candidates: dict[tuple[str, str, int | None], dict[str, Any]],
    chain_data: dict[str, Any],
) -> None:
    peers = chain_data.get("peers", {})
    layer_map = {
        "seeds": ("bootstrap", "Public seed from cosmos chain-registry."),
        "persistent_peers": (
            "node",
            "Public persistent peer from cosmos chain-registry.",
        ),
    }
    for registry_key, (point_type, description) in layer_map.items():
        for peer in peers.get(registry_key, []):
            if not isinstance(peer, dict):
                continue
            address = str(peer.get("address") or "")
            host, port = split_host_port(address)
            if not host:
                continue
            resolved_ips = resolve_host(host)
            for ip in resolved_ips:
                key = (point_type, ip, port)
                existing = candidates.get(key)
                peer_id = str(peer.get("id") or "")
                provider = str(peer.get("provider") or "Unknown")
                if existing:
                    metadata = existing.setdefault("metadata", {})
                    peer_ids = metadata.setdefault("peer_ids", [])
                    providers = metadata.setdefault("chain_registry_providers", [])
                    if peer_id and peer_id not in peer_ids:
                        peer_ids.append(peer_id)
                    if provider and provider not in providers:
                        providers.append(provider)
                    continue
                candidates[key] = {
                    "type": point_type,
                    "name": provider
                    if provider != "Unknown"
                    else f"Celestia testnet {point_type} {ip}",
                    "endpoint": f"{ip}:{port}" if port else ip,
                    "ip": ip,
                    "port": str(port) if port else "",
                    "source": CHAIN_REGISTRY_URL,
                    "description": description,
                    "metadata": {
                        "chain_registry_address": address,
                        "chain_registry_host": host,
                        "chain_registry_provider": provider,
                        "peer_ids": [peer_id] if peer_id else [],
                        "collection": registry_key,
                    },
                }


def add_observed_peer_candidates(
    candidates: dict[tuple[str, str, int | None], dict[str, Any]],
    rpc_sources: list[str],
) -> None:
    for rpc_url in rpc_sources:
        for peer in fetch_net_info(rpc_url):
            if not isinstance(peer, dict):
                continue
            node_info = (
                peer.get("node_info", {})
                if isinstance(peer.get("node_info"), dict)
                else {}
            )
            if node_info.get("network") != CHAIN_ID:
                continue
            remote_ip = str(peer.get("remote_ip") or "")
            if not is_global_ip(remote_ip):
                continue
            listen_addr = str(node_info.get("listen_addr") or "")
            _, listen_port = split_host_port(listen_addr, default_port=26656)
            key = ("observed_peer", remote_ip, listen_port)
            existing = candidates.get(key)
            if existing:
                sources = existing.setdefault("metadata", {}).setdefault(
                    "net_info_sources", []
                )
                if rpc_url not in sources:
                    sources.append(rpc_url)
                continue
            moniker = str(node_info.get("moniker") or "Observed Celestia peer")
            candidates[key] = {
                "type": "observed_peer",
                "name": moniker,
                "endpoint": f"{remote_ip}:{listen_port}" if listen_port else remote_ip,
                "ip": remote_ip,
                "port": str(listen_port) if listen_port else "",
                "source": f"{rpc_url}/net_info",
                "description": "Globally routable peer observed through public Celestia Mocha testnet RPC /net_info.",
                "metadata": {
                    "node_id": str(node_info.get("id") or ""),
                    "version": str(node_info.get("version") or ""),
                    "listen_addr": listen_addr,
                    "net_info_sources": [rpc_url],
                    "collection": "public_rpc_net_info",
                },
            }


def rpc_candidates(endpoints: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    health: dict[str, tuple[str, int | None, str | None, str | None]] = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(rpc_status, endpoint["address"]): endpoint["address"]
            for endpoint in endpoints
        }
        for future in as_completed(futures):
            address = futures[future]
            try:
                health[address] = future.result()
            except Exception:
                health[address] = ("unknown", None, None, None)
    for endpoint in endpoints:
        url = endpoint["address"]
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        if not host:
            continue
        ips = resolve_host(host)
        status, latency, chain_id_response, moniker = health.get(
            url, ("unknown", None, None, None)
        )
        for ip in ips:
            result.append(
                {
                    "type": "rpc",
                    "name": f"{endpoint['provider']} RPC",
                    "status": status,
                    "endpoint": url,
                    "ip": ip,
                    "latency_ms": latency,
                    "source": "cosmos chain-registry RPC API list + /status health check",
                    "description": "Public Celestia Mocha testnet RPC endpoint. DNS edge locations can represent gateway or CDN edge infrastructure, not validator/sentry topology.",
                    "metadata": {
                        "chain_id_response": chain_id_response,
                        "rpc_moniker": moniker,
                        "dns_host": host,
                        "registry_provider": endpoint["provider"],
                        "ip_family": f"IPv{ipaddress.ip_address(ip).version}",
                    },
                }
            )
    return result


def check_peer_latencies(
    candidates: dict[tuple[str, str, int | None], dict[str, Any]],
) -> dict[tuple[str, str, int | None], int | None]:
    result: dict[tuple[str, str, int | None], int | None] = {}
    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {
            executor.submit(
                tcp_latency_ms,
                point["ip"],
                int(point["port"]) if point.get("port") else None,
                1.5,
            ): key
            for key, point in candidates.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                result[key] = future.result()
            except Exception:
                result[key] = None
    return result


def source_entries(rpc_endpoints: list[dict[str, str]]) -> list[dict[str, str]]:
    entries = [
        {
            "label": "Cosmos chain-registry Celestia Mocha testnet",
            "url": CHAIN_REGISTRY_URL,
        }
    ]
    for rpc_url in NET_INFO_RPC_URLS:
        entries.append({"label": f"Public RPC /net_info: {rpc_url}", "url": rpc_url})
    for endpoint in rpc_endpoints:
        entries.append({"label": endpoint["provider"], "url": endpoint["address"]})
    entries.append({"label": "GeoIP lookup", "url": "http://ip-api.com/"})
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for entry in entries:
        if entry["url"] in seen:
            continue
        seen.add(entry["url"])
        deduped.append(entry)
    return deduped


def build_map() -> dict[str, Any]:
    now = utc_now()
    chain_data = fetch_json(CHAIN_REGISTRY_URL)
    rpc_endpoints = chain_registry_rpc_endpoints(chain_data)

    peer_candidates: dict[tuple[str, str, int | None], dict[str, Any]] = {}
    add_registry_peer_candidates(peer_candidates, chain_data)
    add_observed_peer_candidates(peer_candidates, NET_INFO_RPC_URLS)

    rpc_points = rpc_candidates(rpc_endpoints)
    peer_latencies = check_peer_latencies(peer_candidates)

    all_ips = [point["ip"] for point in rpc_points]
    all_ips.extend(point["ip"] for point in peer_candidates.values())
    geo_cache = prime_geo_cache(all_ips)

    points: list[dict[str, Any]] = []
    counters: dict[str, int] = {}

    for key, point in sorted(
        peer_candidates.items(),
        key=lambda item: (item[1]["type"], item[1]["ip"], item[1].get("port") or ""),
    ):
        point_type = point["type"]
        counters[point_type] = counters.get(point_type, 0) + 1
        latency = peer_latencies.get(key)
        rendered = {
            "id": f"{NETWORK_ID}-{point_type}-{counters[point_type]}",
            "network_id": NETWORK_ID,
            "type": point_type,
            "name": point["name"],
            "status": "online" if latency is not None else "observed",
            "endpoint": point["endpoint"],
            "ip": point["ip"],
            "port": point.get("port", ""),
            "latency_ms": latency,
            "source": point["source"],
            "last_checked_at": now,
            "description": point["description"],
            "metadata": point.get("metadata", {}),
            **location_fields(point["ip"], geo_cache),
        }
        points.append(rendered)

    rpc_count = 0
    seen_rpc: set[tuple[str, str]] = set()
    for point in sorted(rpc_points, key=lambda item: (item["endpoint"], item["ip"])):
        dedupe_key = (point["endpoint"], point["ip"])
        if dedupe_key in seen_rpc:
            continue
        seen_rpc.add(dedupe_key)
        rpc_count += 1
        rendered = {
            "id": f"{NETWORK_ID}-rpc-{rpc_count}",
            "network_id": NETWORK_ID,
            **point,
            "last_checked_at": now,
            **location_fields(point["ip"], geo_cache),
        }
        points.append(rendered)

    countries = {
        point.get("country_code") for point in points if point.get("country_code")
    }
    providers = {
        point.get("provider")
        for point in points
        if point.get("provider") and point.get("provider") != "Unknown"
    }

    return {
        "schema": "posthuman-decentralization-map/v1",
        "network": NETWORK,
        "network_id": NETWORK_ID,
        "chain_id": CHAIN_ID,
        "updated_at": now,
        "privacy": {
            "raw_validator_ips": "not published",
            "sentry_topology": "not published",
            "local_addrbook": "excluded when local node is not on Celestia Mocha testnet",
            "public_endpoints": "POSTHUMAN public testnet RPC, chain-registry testnet RPC/seed/peer entries, and public testnet RPC /net_info peers",
            "observed_public_peers": "globally routable peers returned by public Celestia Mocha testnet RPC /net_info",
            "note": "The map uses only public Celestia Mocha testnet endpoints. Private validator/sentry topology and non-global addresses are intentionally excluded. Local ~/.celestia-app data is ignored unless it is verified to be on chain_id mocha-4.",
        },
        "sources": source_entries(rpc_endpoints),
        "summary": {
            "points": len(points),
            "chain_registry_seeds": sum(
                1 for point in points if point["type"] == "bootstrap"
            ),
            "chain_registry_peers": sum(
                1 for point in points if point["type"] == "node"
            ),
            "observed_peers": sum(
                1 for point in points if point["type"] == "observed_peer"
            ),
            "rpc_endpoints": sum(1 for point in points if point["type"] == "rpc"),
            "countries": len(countries),
            "providers": len(providers),
        },
        "points": points,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Build data without writing celestia-testnet/decentralize-map.json",
    )
    args = parser.parse_args()

    data = build_map()
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path = ROOT / CHAIN / "decentralize-map.json"
    if args.check:
        print(
            f"{CHAIN}: points={data['summary']['points']} "
            f"seeds={data['summary']['chain_registry_seeds']} "
            f"peers={data['summary']['chain_registry_peers']} "
            f"observed={data['summary']['observed_peers']} "
            f"rpc={data['summary']['rpc_endpoints']} "
            f"countries={data['summary']['countries']}"
        )
        return 0
    path.write_text(rendered)
    print(f"updated {path.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
