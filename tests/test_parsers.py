import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from parsers import (
    parse_ip_route, parse_ip_stats,
    parse_iw_dev, parse_iwconfig,
    parse_batctl_neighbors, parse_station_dump
)

IP_ROUTE = """
default via 192.168.0.1 dev enp0s31f6 proto dhcp src 192.168.50.102 metric 100
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
192.168.0.0/16 dev enp0s31f6 proto kernel scope link src 192.168.50.102 metric 100
"""

IP_STATS = """
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    RX: bytes  packets  errors  dropped  missed  mcast
    53462963   500364   0       0        0       0
    TX: bytes  packets  errors  dropped  carrier collsns
    53462963   500364   0       0        0       0
2: enp0s31f6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP
    link/ether 4c:cc:6a:cc:06:21 brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped  missed  mcast
    5689901740 3868840  0       1        0       2528
    TX: bytes  packets  errors  dropped  carrier collsns
    88440160   570323   0       4        0       0
3: wlp4s0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN
    link/ether 00:28:f8:e9:9b:3e brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped  missed  mcast
    0          0        0       0        0       0
    TX: bytes  packets  errors  dropped  carrier collsns
    0          0        0       0        0       0
"""

IW_DEV = """
phy#0
    Unnamed/non-netdev interface
        wdev 0x2
        addr 00:28:f8:e9:9b:3f
        type P2P-device
    Interface wlp4s0
        ifindex 3
        wdev 0x1
        addr 00:28:f8:e9:9b:3e
        type managed
"""

IWCONFIG = """
wlp4s0    IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on

lo        no wireless extensions.
enp0s31f6 no wireless extensions.
docker0   no wireless extensions.
"""

BATCTL_NEIGHBORS = """
[B.A.T.M.A.N. adv 2023.3, MainIF/MAC: wlp4s0/00:28:f8:e9:9b:3e (bat0 BATMAN_IV)]
IF             Neighbor              last-seen
wlp4s0         aa:bb:cc:dd:ee:01    0.392s
wlp4s0         aa:bb:cc:dd:ee:02    1.204s
"""

BATCTL_ERROR = "Error - interface bat0 is not present or not a batman-adv interface"

STATION_DUMP = """
Station aa:bb:cc:dd:ee:01 (on wlp4s0)
	inactive time:	120 ms
	rx packets:	1234
	tx packets:	980
	tx failed:	20
	signal:  	-65 dBm
	signal avg:	-63 dBm
	tx bitrate:	54.0 MBit/s
	rx bitrate:	48.0 MBit/s
Station aa:bb:cc:dd:ee:02 (on wlp4s0)
	inactive time:	340 ms
	rx packets:	500
	tx packets:	450
	tx failed:	0
	signal:  	-72 dBm
	signal avg:	-70 dBm
	tx bitrate:	36.0 MBit/s
	rx bitrate:	24.0 MBit/s
"""

class TestParseIpRoute:
    def test_returns_three_routes(self):
        assert len(parse_ip_route(IP_ROUTE)) == 3
    def test_default_route_gateway(self):
        result = parse_ip_route(IP_ROUTE)
        default = next(r for r in result if r["destination"] == "default")
        assert default["gateway"] == "192.168.0.1"
    def test_default_route_dev(self):
        result = parse_ip_route(IP_ROUTE)
        default = next(r for r in result if r["destination"] == "default")
        assert default["dev"] == "enp0s31f6"
    def test_default_route_metric(self):
        result = parse_ip_route(IP_ROUTE)
        default = next(r for r in result if r["destination"] == "default")
        assert default["metric"] == 100
    def test_linkdown_route_flagged(self):
        result = parse_ip_route(IP_ROUTE)
        docker = next(r for r in result if r["dev"] == "docker0")
        assert docker["status"] == "linkdown"
    def test_normal_route_status_up(self):
        result = parse_ip_route(IP_ROUTE)
        default = next(r for r in result if r["destination"] == "default")
        assert default["status"] == "up"
    def test_no_gateway_for_kernel_route(self):
        result = parse_ip_route(IP_ROUTE)
        docker = next(r for r in result if r["dev"] == "docker0")
        assert docker["gateway"] is None
    def test_empty_input_returns_empty_list(self):
        assert parse_ip_route("") == []

class TestParseIpStats:
    def test_returns_three_interfaces(self):
        assert len(parse_ip_stats(IP_STATS)) == 3
    def test_loopback_state_up(self):
        result = parse_ip_stats(IP_STATS)
        lo = next(r for r in result if r["interface"] == "lo")
        assert lo["state"] == "UP"
    def test_wlp4s0_state_down(self):
        result = parse_ip_stats(IP_STATS)
        wlp = next(r for r in result if r["interface"] == "wlp4s0")
        assert wlp["state"] == "DOWN"
    def test_enp_rx_bytes(self):
        result = parse_ip_stats(IP_STATS)
        enp = next(r for r in result if r["interface"] == "enp0s31f6")
        assert enp["rx_bytes"] == 5689901740
    def test_enp_rx_dropped(self):
        result = parse_ip_stats(IP_STATS)
        enp = next(r for r in result if r["interface"] == "enp0s31f6")
        assert enp["rx_dropped"] == 1
    def test_wlp_all_zeros(self):
        result = parse_ip_stats(IP_STATS)
        wlp = next(r for r in result if r["interface"] == "wlp4s0")
        assert wlp["rx_bytes"] == 0 and wlp["tx_bytes"] == 0
    def test_mtu_parsed(self):
        result = parse_ip_stats(IP_STATS)
        lo = next(r for r in result if r["interface"] == "lo")
        assert lo["mtu"] == 65536

class TestParseIwDev:
    def test_finds_wlp4s0(self):
        result = parse_iw_dev(IW_DEV)
        assert "wlp4s0" in [r["interface"] for r in result]
    def test_wlp4s0_type_managed(self):
        result = parse_iw_dev(IW_DEV)
        wlp = next(r for r in result if r["interface"] == "wlp4s0")
        assert wlp["type"] == "managed"
    def test_wlp4s0_addr(self):
        result = parse_iw_dev(IW_DEV)
        wlp = next(r for r in result if r["interface"] == "wlp4s0")
        assert wlp["addr"] == "00:28:f8:e9:9b:3e"

class TestParseIwconfig:
    def test_only_wireless_interfaces_returned(self):
        result = parse_iwconfig(IWCONFIG)
        names = [r["interface"] for r in result]
        assert "lo" not in names and "enp0s31f6" not in names
    def test_wlp4s0_found(self):
        result = parse_iwconfig(IWCONFIG)
        assert len(result) == 1 and result[0]["interface"] == "wlp4s0"
    def test_mode_managed(self):
        assert parse_iwconfig(IWCONFIG)[0]["mode"] == "Managed"
    def test_not_associated(self):
        assert parse_iwconfig(IWCONFIG)[0]["access_point"] == "Not-Associated"

class TestParseBatctlNeighbors:
    def test_returns_two_neighbors(self):
        assert len(parse_batctl_neighbors(BATCTL_NEIGHBORS)) == 2
    def test_first_neighbor_mac(self):
        assert parse_batctl_neighbors(BATCTL_NEIGHBORS)[0]["neighbor_mac"] == "aa:bb:cc:dd:ee:01"
    def test_last_seen_is_float(self):
        assert isinstance(parse_batctl_neighbors(BATCTL_NEIGHBORS)[0]["last_seen_seconds"], float)
    def test_last_seen_value(self):
        assert parse_batctl_neighbors(BATCTL_NEIGHBORS)[1]["last_seen_seconds"] == 1.204
    def test_error_returns_empty_list(self):
        assert parse_batctl_neighbors(BATCTL_ERROR) == []
    def test_empty_input_returns_empty_list(self):
        assert parse_batctl_neighbors("") == []

class TestParseStationDump:
    def test_returns_two_stations(self):
        assert len(parse_station_dump(STATION_DUMP)) == 2
    def test_first_station_mac(self):
        assert parse_station_dump(STATION_DUMP)[0]["mac"] == "aa:bb:cc:dd:ee:01"
    def test_rssi_parsed(self):
        assert parse_station_dump(STATION_DUMP)[0]["rssi_dbm"] == -65
    def test_tx_bitrate(self):
        assert parse_station_dump(STATION_DUMP)[0]["tx_bitrate_mbps"] == 54.0
    def test_loss_pct_calculated(self):
        assert parse_station_dump(STATION_DUMP)[0]["tx_loss_pct"] == 2.0
    def test_zero_loss(self):
        assert parse_station_dump(STATION_DUMP)[1]["tx_loss_pct"] == 0.0
    def test_empty_returns_empty_list(self):
        assert parse_station_dump("") == []
