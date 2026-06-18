# Mininet-WiFi Setup Notes — Week 9

## Installation
- Ubuntu 24.04.4 LTS, kernel 6.17
- Cloned from https://github.com/intrig-unicamp/mininet-wifi
- Installed via: sudo util/install.sh -Wlnfv < /dev/null
- Patch warnings for hostapd/wpa_supplicant defconfig were safe to skip (already applied in source)
- Verified: mn_wifi module v2.7, mn command, hostapd compiled successfully

## Working mesh topology configuration
- 3 stations: sta1, sta2, sta3
- Propagation model: logDistance, exp=3 (exp=4 was too aggressive, no peers formed)
- Positions: 10,10,0 / 20,10,0 / 30,10,0 (closer spacing required for exp=3 to connect)
- Link type: cls=mesh (not cls=None) — critical, addLink fails with AttributeError otherwise
- Node setup: net.configureNodes() (not configureWifiNodes — method name differs in v2.7)

## Verified working
- Mesh peering: plink ESTAB between all stations, confirmed via `iw dev sta1-mp0 station dump`
- Signal strength: -45 dBm (sta1↔sta2), -54 dBm (sta1↔sta3 via relay)
- Ping sta1→sta2: 0% packet loss, RTT 0.485-10.7ms
- Mesh interface naming: each station gets <name>-mp0 (mesh point, carries traffic) AND <name>-wlan0 (managed, mostly idle) — MCP tools must target the mp0 interface, not wlan0, when testing against this emulator

## Key troubleshooting notes for future reference
- `iw dev sta1-mp0 station dump` is the command to check mesh peer status
- Empty output = no peers found (check propagation model / distance)
- `mesh plink: ESTAB` = successfully peered
- First ping after mesh formation is always slow (ARP resolution ~10ms), subsequent pings settle to <1ms

## Server verification against live mesh (Week 9 completion)

Ran actual server.py functions (not mocks) against sta1-mp0 in the live emulated mesh:
- get_link_quality: correctly identified 2 mesh peers with real RSSI (-54dBm, -45dBm)
- ping_neighbor: 0% loss to sta2, RTT 0.451-14.038ms
- get_interface_stats: correctly distinguished active mp0 interface from idle wlan0

This confirms the MCP server's parsing and tool logic work correctly against real
(simulated) wireless mesh kernel output, not just unit test fixtures.

## CI/CD limitations (Week 10)

GitHub Actions hosted runners do not support the sudo-level network namespace
operations Mininet-WiFi requires (creating virtual interfaces, joining mesh
networks, raw socket access). As a result:

- tests/ (90 unit tests, mocked subprocess) run automatically in CI on every push
- tests/integration/ (8 integration + 3 latency tests) require a live mesh and
  must be run locally or via a self-hosted GitHub Actions runner

This is a deliberate scope decision: setting up a persistent self-hosted runner
introduces meaningful security surface (granting GitHub Actions sudo access to
a personal machine) that is disproportionate to the benefit for an individual
academic project. The integration test suite is fully automated and repeatable
when run manually, satisfying the verification goal without that tradeoff.
