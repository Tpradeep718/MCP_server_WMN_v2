"""
Integration tests against a live Mininet-WiFi mesh.
These tests require:
  - sudo privileges
  - Mininet-WiFi installed
  - Must be run from inside a Mininet station namespace (e.g. via `sta1 pytest ...`)
  - NOT run as part of the regular unit test suite (no mocking, real subprocess calls)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
import server


def mesh_interface_exists():
    """Check if we're actually running inside a station with a mesh interface."""
    result = server.run_cmd(["iw", "dev"])
    return "mp0" in result["stdout"]


requires_mesh = pytest.mark.skipif(
    not mesh_interface_exists(),
    reason="No mesh point interface found — run inside a Mininet station namespace"
)


@requires_mesh
class TestLiveMeshLinkQuality:

    def test_returns_at_least_one_station(self):
        result = server.get_link_quality(interface="sta1-mp0")
        assert "stations" in result
        assert len(result["stations"]) >= 1

    def test_rssi_is_realistic_range(self):
        result = server.get_link_quality(interface="sta1-mp0")
        for station in result["stations"]:
            assert -100 <= station["rssi_dbm"] <= 0

    def test_no_error_key_present(self):
        result = server.get_link_quality(interface="sta1-mp0")
        assert "error" not in result


@requires_mesh
class TestLiveMeshPing:

    def test_ping_to_known_peer_succeeds(self):
        result = server.ping_neighbor(host="10.0.0.2")
        assert result["loss_pct"] < 100.0
        assert result["received"] > 0

    def test_ping_to_unreachable_host_fails_gracefully(self):
        result = server.ping_neighbor(host="10.0.0.250")
        assert result["loss_pct"] == 100.0
        assert "note" in result

    def test_rtt_values_are_positive(self):
        result = server.ping_neighbor(host="10.0.0.2")
        if result["rtt_avg_ms"] is not None:
            assert result["rtt_avg_ms"] > 0


@requires_mesh
class TestLiveMeshInterfaceStats:

    def test_mesh_point_interface_is_up(self):
        result = server.get_interface_stats()
        mp_interfaces = [i for i in result["interfaces"] if "mp0" in i["interface"]]
        assert len(mp_interfaces) == 1
        assert mp_interfaces[0]["state"] == "UP"

    def test_loopback_always_present(self):
        result = server.get_interface_stats()
        names = [i["interface"] for i in result["interfaces"]]
        assert "lo" in names
