import re

# ── Parser 1: ip route ──────────────────────────────────────────────────────
def parse_ip_route(raw: str) -> list:
    """
    Parses output of `ip route` into structured route objects.
    Handles: default gateway, kernel routes, linkdown routes.
    """
    routes = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        route = {}

        # destination
        parts = line.split()
        route["destination"] = parts[0]  # "default" or CIDR like "192.168.0.0/16"

        # gateway (via X.X.X.X)
        via = re.search(r'via (\S+)', line)
        route["gateway"] = via.group(1) if via else None

        # device
        dev = re.search(r'dev (\S+)', line)
        route["dev"] = dev.group(1) if dev else None

        # proto
        proto = re.search(r'proto (\S+)', line)
        route["proto"] = proto.group(1) if proto else None

        # src
        src = re.search(r'src (\S+)', line)
        route["src"] = src.group(1) if src else None

        # metric
        metric = re.search(r'metric (\d+)', line)
        route["metric"] = int(metric.group(1)) if metric else None

        # status
        route["status"] = "linkdown" if "linkdown" in line else "up"

        routes.append(route)
    return routes


# ── Parser 2: ip -s link ────────────────────────────────────────────────────
def parse_ip_stats(raw: str) -> list:
    """
    Parses output of `ip -s link` into per-interface stats.
    Handles multiple interfaces in one output block.
    """
    interfaces = []
    blocks = re.split(r'\n(?=\d+:)', raw.strip())

    for block in blocks:
        if not block.strip():
            continue
        iface = {}

        # interface name and state
        header = re.match(r'\d+:\s+(\S+):\s+<([^>]+)>', block)
        if not header:
            continue
        iface["interface"] = header.group(1).rstrip(':')
        flags = header.group(2)
        iface["state"] = "UP" if "UP" in flags else "DOWN"
        if "DORMANT" in block:
            iface["state"] = "DORMANT"

        # mtu
        mtu = re.search(r'mtu (\d+)', block)
        iface["mtu"] = int(mtu.group(1)) if mtu else None

        # RX and TX lines — ip -s link gives two number rows per direction
        numbers = re.findall(r'^\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', block, re.MULTILINE)
        if len(numbers) >= 2:
            rx = numbers[0]
            tx = numbers[1]
            iface["rx_bytes"]   = int(rx[0])
            iface["rx_packets"] = int(rx[1])
            iface["rx_errors"]  = int(rx[2])
            iface["rx_dropped"] = int(rx[3])
            iface["tx_bytes"]   = int(tx[0])
            iface["tx_packets"] = int(tx[1])
            iface["tx_errors"]  = int(tx[2])
        else:
            iface["rx_bytes"] = iface["rx_packets"] = iface["rx_errors"] = 0
            iface["tx_bytes"] = iface["tx_packets"] = iface["tx_errors"] = 0

        interfaces.append(iface)
    return interfaces


# ── Parser 3: iw dev ────────────────────────────────────────────────────────
def parse_iw_dev(raw: str) -> list:
    """
    Parses output of `iw dev` into per-interface wireless config.
    """
    interfaces = []
    blocks = re.split(r'\n\s*Interface ', raw)

    for block in blocks:
        if 'wdev' not in block and 'ifindex' not in block:
            continue
        iface = {}

        name = re.match(r'(\S+)', block)
        iface["interface"] = name.group(1) if name else "unknown"

        addr = re.search(r'addr ([\da-f:]+)', block)
        iface["addr"] = addr.group(1) if addr else None

        itype = re.search(r'type (\S+)', block)
        iface["type"] = itype.group(1) if itype else None

        channel = re.search(r'channel (\d+)', block)
        iface["channel"] = int(channel.group(1)) if channel else None

        txpower = re.search(r'txpower ([\d.]+)', block)
        iface["tx_power_dbm"] = float(txpower.group(1)) if txpower else None

        interfaces.append(iface)
    return interfaces


# ── Parser 4: iwconfig ──────────────────────────────────────────────────────
def parse_iwconfig(raw: str) -> list:
    """
    Parses output of `iwconfig` into wireless status per interface.
    Skips interfaces with 'no wireless extensions'.
    """
    interfaces = []
    blocks = re.split(r'\n(?=\S)', raw.strip())

    for block in blocks:
        if 'no wireless extensions' in block:
            continue
        if not block.strip():
            continue
        iface = {}

        name = re.match(r'(\S+)', block)
        iface["interface"] = name.group(1) if name else "unknown"

        essid = re.search(r'ESSID:"?([^"\s]+)"?', block)
        iface["essid"] = essid.group(1) if essid else "off/any"

        mode = re.search(r'Mode:(\S+)', block)
        iface["mode"] = mode.group(1) if mode else None

        ap = re.search(r'Access Point:\s*(\S+)', block)
        iface["access_point"] = ap.group(1) if ap else None

        freq = re.search(r'Frequency:([\d.]+)', block)
        iface["frequency_ghz"] = float(freq.group(1)) if freq else None

        interfaces.append(iface)
    return interfaces


# ── Parser 5: batctl neighbors ──────────────────────────────────────────────
def parse_batctl_neighbors(raw: str) -> list:
    """
    Parses output of `batctl meshif bat0 n`.
    Returns empty list if interface not present (expected without mesh).
    """
    if 'Error' in raw or 'not present' in raw:
        return []

    neighbors = []
    for line in raw.strip().splitlines():
        # skip header lines
        if line.startswith('[') or line.startswith('IF'):
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                last_seen = float(parts[2].replace('s', ''))
            except ValueError:
                continue
            neighbors.append({
                "outgoing_interface": parts[0],
                "neighbor_mac":       parts[1],
                "last_seen_seconds":  last_seen
            })
    return neighbors


# ── Self-test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, subprocess

    print("=" * 50)
    print("TEST 1: ip route")
    raw = subprocess.run(["ip", "route"], capture_output=True, text=True).stdout
    result = parse_ip_route(raw)
    print(json.dumps(result, indent=2))

    print("=" * 50)
    print("TEST 2: ip -s link")
    raw = subprocess.run(["ip", "-s", "link"], capture_output=True, text=True).stdout
    result = parse_ip_stats(raw)
    print(json.dumps(result, indent=2))

    print("=" * 50)
    print("TEST 3: iw dev")
    raw = subprocess.run(["iw", "dev"], capture_output=True, text=True).stdout
    result = parse_iw_dev(raw)
    print(json.dumps(result, indent=2))

    print("=" * 50)
    print("TEST 4: iwconfig")
    raw = subprocess.run(["iwconfig"], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    result = parse_iwconfig(raw)
    print(json.dumps(result, indent=2))

    print("=" * 50)
    print("TEST 5: batctl neighbors (mock)")
    mock = open("fixtures/batctl_neighbors_mock.txt").read()
    result = parse_batctl_neighbors(mock)
    print(json.dumps(result, indent=2))


# ── Parser 6: iw station dump ───────────────────────────────────────────────
def parse_station_dump(raw: str) -> list:
    """
    Parses output of `iw dev <interface> station dump`.
    Returns RSSI, TX/RX bitrate, and packet loss per connected peer.
    """
    import re
    if not raw.strip() or 'error' in raw.lower():
        return []

    stations = []
    current  = {}

    for line in raw.strip().splitlines():
        if line.startswith('Station'):
            if current:
                stations.append(current)
            mac = re.match(r'Station\s+([\da-f:]+)', line)
            current = {"mac": mac.group(1) if mac else "unknown"}
        elif 'signal:' in line and 'avg' not in line:
            val = re.search(r'signal:\s*([-\d]+)', line)
            current["rssi_dbm"] = int(val.group(1)) if val else None
        elif 'signal avg:' in line:
            val = re.search(r'signal avg:\s*([-\d]+)', line)
            current["rssi_avg_dbm"] = int(val.group(1)) if val else None
        elif 'tx bitrate:' in line:
            val = re.search(r'tx bitrate:\s*([\d.]+)', line)
            current["tx_bitrate_mbps"] = float(val.group(1)) if val else None
        elif 'rx bitrate:' in line:
            val = re.search(r'rx bitrate:\s*([\d.]+)', line)
            current["rx_bitrate_mbps"] = float(val.group(1)) if val else None
        elif 'tx packets:' in line:
            val = re.search(r'tx packets:\s*(\d+)', line)
            current["tx_packets"] = int(val.group(1)) if val else None
        elif 'tx failed:' in line:
            val = re.search(r'tx failed:\s*(\d+)', line)
            current["tx_failed"] = int(val.group(1)) if val else None
        elif 'rx packets:' in line:
            val = re.search(r'rx packets:\s*(\d+)', line)
            current["rx_packets"] = int(val.group(1)) if val else None
        elif 'inactive time:' in line:
            val = re.search(r'inactive time:\s*(\d+)', line)
            current["inactive_ms"] = int(val.group(1)) if val else None

    if current and "mac" in current:
        stations.append(current)

    for s in stations:
        tx     = s.get("tx_packets", 0) or 0
        failed = s.get("tx_failed",  0) or 0
        total  = tx + failed
        s["tx_loss_pct"] = round(failed / total * 100, 1) if total > 0 else 0.0

    return stations
