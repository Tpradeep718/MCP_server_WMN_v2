import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import patch
import server


class TestListNeighborsTool:

    @patch('server.run_cmd')
    def test_no_mesh_returns_empty_with_note(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "Error - interface bat0 is not present or not a batman-adv interface",
            "returncode": 1, "error": None
        }
        result = server.list_neighbors()
        assert result["neighbors"] == []
        assert "not present" in result["note"]

    @patch('server.run_cmd')
    def test_timeout_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command timed out after 5s"
        }
        result = server.list_neighbors()
        assert "error" in result
        assert "timed out" in result["error"]

    @patch('server.run_cmd')
    def test_successful_neighbors_returned(self, mock_run):
        mock_run.return_value = {
            "stdout": "[B.A.T.M.A.N. adv]\nIF Neighbor last-seen\nwlp4s0 aa:bb:cc:dd:ee:01 0.392s\n",
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.list_neighbors()
        assert result["count"] == 1
        assert result["neighbors"][0]["neighbor_mac"] == "aa:bb:cc:dd:ee:01"

    @patch('server.run_cmd')
    def test_custom_interface_used(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "not present", "returncode": 1, "error": None
        }
        server.list_neighbors(interface="bat1")
        called_cmd = mock_run.call_args[0][0]
        assert "bat1" in called_cmd


class TestGetLinkQualityTool:

    @patch('server.run_cmd')
    def test_interface_not_found(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "No such device", "returncode": 1, "error": None
        }
        result = server.get_link_quality(interface="wlan99")
        assert "error" in result
        assert "not found" in result["error"]

    @patch('server.run_cmd')
    def test_no_stations_returns_note(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_link_quality()
        assert result["stations"] == []
        assert "note" in result

    @patch('server.run_cmd')
    def test_stations_parsed_correctly(self, mock_run):
        mock_run.return_value = {
            "stdout": "Station aa:bb:cc:dd:ee:01 (on wlp4s0)\n\tsignal:  \t-65 dBm\n",
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_link_quality()
        assert result["count"] == 1
        assert result["stations"][0]["rssi_dbm"] == -65

    @patch('server.run_cmd')
    def test_command_error_propagates(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command not found: iw"
        }
        result = server.get_link_quality()
        assert "error" in result


class TestPingNeighborTool:

    def test_missing_host_returns_error(self):
        result = server.ping_neighbor(host="")
        assert "error" in result
        assert "required" in result["error"]

    @patch('server.run_cmd')
    def test_successful_ping_parsed(self, mock_run):
        mock_run.return_value = {
            "stdout": "4 packets transmitted, 4 received, 0% packet loss\nrtt min/avg/max/mdev = 0.384/0.414/0.445/0.020 ms\n",
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.ping_neighbor(host="192.168.0.1")
        assert result["loss_pct"] == 0.0
        assert result["rtt_avg_ms"] == 0.414

    @patch('server.run_cmd')
    def test_full_loss_adds_note(self, mock_run):
        mock_run.return_value = {
            "stdout": "4 packets transmitted, 0 received, 100% packet loss\n",
            "stderr": "", "returncode": 1, "error": None
        }
        result = server.ping_neighbor(host="10.0.0.99")
        assert result["loss_pct"] == 100.0
        assert "note" in result


class TestSetWifiChannelTool:

    def test_invalid_token_denied(self):
        result = server.set_wifi_channel(interface="wlp4s0", channel=6, token="wrong-token")
        assert result["error"] == "privilege denied — invalid token"

    def test_invalid_channel_rejected(self):
        result = server.set_wifi_channel(interface="wlp4s0", channel=99, token=server.TOKEN)
        assert "invalid channel" in result["error"]

    @patch('server.run_cmd')
    def test_interface_not_found_preflight(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "No such device", "returncode": 1, "error": None
        }
        result = server.set_wifi_channel(interface="wlan99", channel=6, token=server.TOKEN)
        assert "not found" in result["error"]

class TestGetInterfaceConfigTool:

    @patch('server.run_cmd')
    def test_both_sources_fail_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command not found"
        }
        result = server.get_interface_config()
        assert "error" in result

    @patch('server.run_cmd')
    def test_iw_succeeds_iwconfig_fails_partial_result(self, mock_run):
        def side_effect(cmd, timeout=None):
            if cmd[0] == "iw":
                return {"stdout": "phy#0\n    Interface wlan0\n        ifindex 3\n        addr 00:11:22:33:44:55\n        type managed\n",
                        "stderr": "", "returncode": 0, "error": None}
            else:
                return {"stdout": "", "stderr": "", "returncode": -1,
                        "error": "Command not found: iwconfig"}
        mock_run.side_effect = side_effect
        result = server.get_interface_config()
        assert "interfaces" in result
        assert len(result["interfaces"]) >= 1
        assert result["interfaces"][0]["interface"] == "wlan0"

    @patch('server.run_cmd')
    def test_filter_by_nonexistent_interface_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": "Interface wlan0\n\taddr 00:11:22:33:44:55\n\ttype managed\n",
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_interface_config(interface="ghost0")
        assert "error" in result
        assert "not found" in result["error"]


class TestGetInterfaceStatsTool:

    @patch('server.run_cmd')
    def test_command_failure_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command not found: ip"
        }
        result = server.get_interface_stats()
        assert "error" in result

    @patch('server.run_cmd')
    def test_filter_by_interface_name(self, mock_run):
        mock_run.return_value = {
            "stdout": ("2: eth0: <UP> mtu 1500 qdisc fq_codel state UP\n"
                       "    link/ether aa:bb:cc:dd:ee:ff brd ff:ff:ff:ff:ff:ff\n"
                       "    RX: bytes  packets  errors  dropped  missed  mcast\n"
                       "    100 10 0 0 0 0\n"
                       "    TX: bytes  packets  errors  dropped  carrier collsns\n"
                       "    50 5 0 0 0 0\n"),
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_interface_stats(interface="eth0")
        assert "interfaces" in result
        assert result["interfaces"][0]["interface"] == "eth0"

    @patch('server.run_cmd')
    def test_filter_nonexistent_interface_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": ("2: eth0: <UP> mtu 1500 qdisc fq_codel state UP\n"
                       "    link/ether aa:bb:cc:dd:ee:ff brd ff:ff:ff:ff:ff:ff\n"
                       "    RX: bytes  packets  errors  dropped  missed  mcast\n"
                       "    100 10 0 0 0 0\n"
                       "    TX: bytes  packets  errors  dropped  carrier collsns\n"
                       "    50 5 0 0 0 0\n"),
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_interface_stats(interface="ghost0")
        assert "error" in result


class TestGetRoutingTableTool:

    @patch('server.run_cmd')
    def test_command_failure_returns_error(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command not found: ip"
        }
        result = server.get_routing_table()
        assert "error" in result

    @patch('server.run_cmd')
    def test_empty_table_returns_note(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_routing_table()
        assert result["routes"] == []
        assert "note" in result

    @patch('server.run_cmd')
    def test_successful_routes_returned(self, mock_run):
        mock_run.return_value = {
            "stdout": "default via 10.0.0.1 dev eth0 proto static metric 100\n",
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.get_routing_table()
        assert len(result["routes"]) == 1
        assert result["routes"][0]["gateway"] == "10.0.0.1"

class TestPingNeighborEdgeCases:

    @patch('server.run_cmd')
    def test_dns_failure_returns_high_loss(self, mock_run):
        mock_run.return_value = {
            "stdout": "ping: nonexistent.invalid: Name or service not known\n",
            "stderr": "", "returncode": 2, "error": None
        }
        result = server.ping_neighbor(host="nonexistent.invalid")
        assert result["loss_pct"] == 100.0
        assert "note" in result

    @patch('server.run_cmd')
    def test_ping_command_not_found(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command not found: ping"
        }
        result = server.ping_neighbor(host="192.168.0.1")
        assert "error" in result

    @patch('server.run_cmd')
    def test_partial_packet_loss_parsed(self, mock_run):
        mock_run.return_value = {
            "stdout": ("4 packets transmitted, 2 received, 50% packet loss\n"
                       "rtt min/avg/max/mdev = 1.0/2.0/3.0/0.5 ms\n"),
            "stderr": "", "returncode": 0, "error": None
        }
        result = server.ping_neighbor(host="192.168.0.50")
        assert result["loss_pct"] == 50.0
        assert result["received"] == 2
        assert "note" not in result

    def test_custom_count_used(self):
        with patch('server.run_cmd') as mock_run:
            mock_run.return_value = {
                "stdout": "10 packets transmitted, 10 received, 0% packet loss\n",
                "stderr": "", "returncode": 0, "error": None
            }
            server.ping_neighbor(host="192.168.0.1", count=10)
            called_cmd = mock_run.call_args[0][0]
            assert "10" in called_cmd

    @patch('server.run_cmd')
    def test_timeout_during_ping(self, mock_run):
        mock_run.return_value = {
            "stdout": "", "stderr": "", "returncode": -1,
            "error": "Command timed out after 17s"
        }
        result = server.ping_neighbor(host="192.168.0.1")
        assert "error" in result
        assert "timed out" in result["error"]


class TestSetWifiChannelEdgeCases:

    def test_write_ops_disabled_blocks_request(self):
        original = server.SEC.get("allow_write_operations")
        server.SEC["allow_write_operations"] = False
        result = server.set_wifi_channel(interface="wlan0", channel=6, token=server.TOKEN)
        server.SEC["allow_write_operations"] = original
        assert "disabled" in result["error"]

    def test_channel_zero_rejected(self):
        result = server.set_wifi_channel(interface="wlan0", channel=0, token=server.TOKEN)
        assert "invalid channel" in result["error"]

    def test_channel_14_rejected(self):
        result = server.set_wifi_channel(interface="wlan0", channel=14, token=server.TOKEN)
        assert "invalid channel" in result["error"]

    @patch('server.run_cmd')
    def test_successful_channel_change(self, mock_run):
        def side_effect(cmd, timeout=None):
            if "info" in cmd:
                return {"stdout": "Interface wlan0\n\ttype managed\n", "stderr": "",
                        "returncode": 0, "error": None}
            else:
                return {"stdout": "", "stderr": "", "returncode": 0, "error": None}
        mock_run.side_effect = side_effect
        result = server.set_wifi_channel(interface="wlan0", channel=6, token=server.TOKEN)
        assert result["success"] is True
        assert result["new_channel"] == 6

    @patch('server.run_cmd')
    def test_channel_change_command_fails(self, mock_run):
        def side_effect(cmd, timeout=None):
            if "info" in cmd:
                return {"stdout": "Interface wlan0\n\ttype managed\n", "stderr": "",
                        "returncode": 0, "error": None}
            else:
                return {"stdout": "", "stderr": "Invalid channel for this band",
                        "returncode": 1, "error": None}
        mock_run.side_effect = side_effect
        result = server.set_wifi_channel(interface="wlan0", channel=13, token=server.TOKEN)
        assert result["success"] is False
        assert "Invalid channel" in result["error"]
