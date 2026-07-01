# WMN MCP Server — Tool Reference

Server name: `wmn-mcp`
Protocol: MCP (Model Context Protocol) over stdio or Streamable HTTP
Version: 1.27.2

---

## hello_world

**Description:** Test tool — confirms the MCP server is running and returns
server metadata including the configured interface and transport mode.

**Input:** None required

**Output:**
```json
{
  "status": "ok",
  "server": "wmn-mcp",
  "interface": "sta1-mp0",
  "transport": "stdio",
  "tools": 7
}
```

**Example prompt:** *"Is the MCP server running?"*

---

## get_routing_table

**Description:** Returns the Linux IP routing table for the mesh node,
showing all routes including the default gateway, direct mesh links,
and any overlay routing entries.

**Input:** None required

**Output:**
```json
{
  "routes": [
    {
      "destination": "default",
      "gateway": "192.168.0.1",
      "dev": "enp0s31f6",
      "proto": "dhcp",
      "src": "192.168.50.102",
      "metric": 100,
      "status": "up"
    }
  ]
}
```

**Error cases:**
- `{"error": "Command not found: ip"}` — ip tool not installed
- `{"routes": [], "note": "Routing table is empty"}` — no routes configured

**Example prompt:** *"What routes does this mesh node have configured?"*

---

## get_interface_stats

**Description:** Returns RX/TX statistics for all (or one specific) network
interface on the mesh node — bytes transferred, packet counts, and errors.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| interface | string | No | Filter to one interface (e.g. `sta1-mp0`). Leave blank for all. |

**Output:**
```json
{
  "interfaces": [
    {
      "interface": "sta1-mp0",
      "state": "UP",
      "mtu": 1500,
      "rx_bytes": 1994,
      "rx_packets": 25,
      "rx_errors": 0,
      "rx_dropped": 0,
      "tx_bytes": 2124,
      "tx_packets": 19,
      "tx_errors": 0
    }
  ]
}
```

**Example prompt:** *"How much data has passed through the mesh interface?"*

---

## get_interface_config

**Description:** Returns wireless configuration for all (or one specific)
Wi-Fi interface — channel, mode, ESSID, TX power, and association status.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| interface | string | No | Filter to one interface name. Leave blank for all. |

**Output:**
```json
{
  "interfaces": [
    {
      "interface": "sta1-mp0",
      "type": "mesh point",
      "addr": "02:00:00:00:00:01",
      "channel": 5,
      "tx_power_dbm": 15.0,
      "mode": "Auto",
      "essid": "off/any"
    }
  ]
}
```

**Example prompt:** *"What channel is the mesh running on?"*

---

## list_neighbors

**Description:** Lists all batman-adv mesh neighbors visible from this node,
with their MAC address and last-seen timestamp.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| interface | string | No | Mesh interface name (default: `bat0`) |

**Output:**
```json
{
  "interface": "bat0",
  "neighbors": [
    {
      "neighbor_mac": "aa:bb:cc:dd:ee:01",
      "outgoing_interface": "wlp4s0",
      "last_seen_seconds": 0.392
    }
  ],
  "count": 1
}
```

**Note:** Returns empty list with explanatory note if batman-adv is not
running or the mesh interface is not present.

**Example prompt:** *"Who are this node's mesh neighbors?"*

---

## get_link_quality

**Description:** Returns per-peer link quality metrics for all stations
connected to the mesh interface — RSSI signal strength, TX/RX bitrate,
and calculated packet loss percentage.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| interface | string | No | Wireless interface name (default from config) |

**Output:**
```json
{
  "interface": "sta1-mp0",
  "stations": [
    {
      "mac": "02:00:00:00:02:00",
      "rssi_dbm": -35,
      "rssi_avg_dbm": -35,
      "tx_bitrate_mbps": 13.0,
      "rx_bitrate_mbps": null,
      "tx_packets": 3,
      "tx_failed": 0,
      "rx_packets": 1266,
      "inactive_ms": 525,
      "tx_loss_pct": 0.0
    }
  ],
  "count": 2
}
```

**RSSI interpretation:**
- Above -50 dBm: Excellent
- -50 to -70 dBm: Good
- -70 to -80 dBm: Fair
- Below -80 dBm: Poor (likely packet loss)

**Example prompt:** *"What is the signal strength to each mesh peer?"*

---

## ping_neighbor

**Description:** Sends ICMP ping packets to a target IP address and returns
round-trip time statistics and packet loss percentage.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| host | string | Yes | IP address or hostname to ping |
| count | integer | No | Number of ping packets (default: 4) |

**Output:**
```json
{
  "host": "10.0.0.2",
  "transmitted": 4,
  "received": 4,
  "loss_pct": 0.0,
  "rtt_min_ms": 0.085,
  "rtt_avg_ms": 0.126,
  "rtt_max_ms": 0.282
}
```

**On 100% loss:**
```json
{
  "host": "10.0.0.99",
  "transmitted": 4,
  "received": 0,
  "loss_pct": 100.0,
  "rtt_min_ms": null,
  "rtt_avg_ms": null,
  "rtt_max_ms": null,
  "note": "Host unreachable or all packets lost"
}
```

**Example prompt:** *"Ping 10.0.0.2 and tell me if the link is healthy"*

---

## set_wifi_channel

**Description:** Changes the Wi-Fi channel on a mesh interface. Requires
a valid privilege token and write operations must be enabled in config.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| interface | string | Yes | Wireless interface name (e.g. `wlp4s0`) |
| channel | integer | Yes | Channel number (1–13) |
| token | string | Yes | Privilege token from config (default: `wmn-secret-2024`) |

**Output on success:**
```json
{
  "success": true,
  "interface": "wlp4s0",
  "new_channel": 6
}
```

**Error cases:**
- `{"error": "privilege denied — invalid token"}` — wrong token
- `{"error": "invalid channel 14 — must be 1–13"}` — out of range
- `{"error": "write operations disabled in config"}` — config flag off
- `{"error": "interface 'wlan99' not found or not wireless"}` — bad interface

**Security note:** Every successful call is logged to `logs/audit.log`
with timestamp, interface, and channel for accountability.

**Example prompt:** *"Switch the mesh to channel 11 using token wmn-secret-2024"*

---

## Error response format

All tools return structured JSON errors rather than raising exceptions:

```json
{"error": "descriptive error message"}
```

This ensures the AI client always receives a parseable response it can
reason about, rather than a Python traceback that would be uninterpretable.
