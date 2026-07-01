# Evaluation Results — WMN MCP Server

## Latency (from benchmark.py, 10 runs each on eno1 interface)

| Tool | P50 (ms) | P95 (ms) | SLA | Result |
|------|----------|----------|-----|--------|
| hello_world | 0.0 | 0.0 | 2000ms | PASS |
| get_routing_table | 2.33 | 3.29 | 2000ms | PASS |
| get_interface_stats | 1.88 | 2.40 | 2000ms | PASS |
| get_interface_config | 2.34 | 2.76 | 2000ms | PASS |
| list_neighbors | 7.43 | 7.94 | 2000ms | PASS |
| get_link_quality | 1.27 | 1.37 | 2000ms | PASS |
| ping_neighbor | 3071.95 | 3091.27 | 5000ms | PASS |

All 7 tools pass their respective SLA thresholds.

## Tool Correctness (tested against live Mininet-WiFi mesh)

| Tool | Correctness | Notes |
|------|-------------|-------|
| hello_world | ✅ Pass | Returns server metadata correctly |
| get_routing_table | ✅ Pass | Returns correct routes for sta1 namespace |
| get_interface_stats | ✅ Pass | Correct RX/TX for sta1-mp0, lo, sta1-wlan0 |
| get_interface_config | ✅ Pass | Correct channel 5, 15dBm, mesh type |
| list_neighbors | ⚠️ Partial | Works correctly but bat0 not present in 802.11s topology |
| get_link_quality | ✅ Pass | Returns RSSI -35dBm for both peers after interface fix |
| ping_neighbor | ✅ Pass | 0% loss, sub-ms RTT on stable mesh (wmediumd removed) |
| set_wifi_channel | ✅ Pass | Token validation, channel range, write-ops flag all enforced |

## AI Plan Quality (from Week 11 Cline validation session)

| Scenario | Tools called | AI quality score (1-5) | Notes |
|----------|-------------|------------------------|-------|
| Routing table analysis | get_routing_table | 5 | Correctly identified missing gateway significance |
| Ping both neighbors | ping_neighbor x2 | 5 | Correct comparison, correct conclusion |
| Mesh health check | list_neighbors → ping | 4 | Correctly diagnosed bat0 missing; minor: assumed batman-adv |
| Unified health snapshot | get_interface_stats + get_interface_config + get_link_quality | 5 | Full structured report with correct health verdict |
| Bug discovery | get_link_quality | 5 | Identified and fixed wrong default interface independently |

**Mean AI plan quality score: 4.8 / 5.0**

## Security Audit Results

| Test | Result |
|------|--------|
| Empty token rejected | ✅ Pass |
| Wrong token rejected | ✅ Pass |
| Injection attempt rejected | ✅ Pass |
| Channel 0 rejected | ✅ Pass |
| Channel 14 rejected | ✅ Pass |
| Write ops disabled blocks request | ✅ Pass |

## Test Coverage

| Test type | Count | Result |
|-----------|-------|--------|
| Unit tests (mocked subprocess) | 90 | All passing |
| Integration tests (live mesh) | 8 | All passing |
| Latency tests (live mesh) | 3 | All passing |
| Security tests | 6 | All passing |
| **Total** | **107** | **107 passing** |
