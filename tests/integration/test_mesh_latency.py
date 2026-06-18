"""
Latency verification against the live Mininet-WiFi mesh.
Run inside a station namespace via: sta1 pytest tests/integration/test_mesh_latency.py -v -s
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
import server


def mesh_interface_exists():
    result = server.run_cmd(["iw", "dev"])
    return "mp0" in result["stdout"]


requires_mesh = pytest.mark.skipif(
    not mesh_interface_exists(),
    reason="No mesh point interface found"
)


def measure(func, runs=10, **kwargs):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        func(**kwargs)
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    return {
        "p50": times[len(times) // 2],
        "p95": times[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "max": max(times),
    }


@requires_mesh
class TestMeshLatencySLA:

    def test_get_link_quality_under_2s_p95(self, capsys):
        stats = measure(server.get_link_quality, runs=10, interface="sta1-mp0")
        with capsys.disabled():
            print(f"\nget_link_quality on live mesh: p50={stats['p50']:.1f}ms "
                  f"p95={stats['p95']:.1f}ms max={stats['max']:.1f}ms")
        assert stats["p95"] < 2000

    def test_get_interface_stats_under_2s_p95(self, capsys):
        stats = measure(server.get_interface_stats, runs=10)
        with capsys.disabled():
            print(f"\nget_interface_stats on live mesh: p50={stats['p50']:.1f}ms "
                  f"p95={stats['p95']:.1f}ms max={stats['max']:.1f}ms")
        assert stats["p95"] < 2000

    def test_ping_neighbor_under_5s_p95(self, capsys):
        stats = measure(server.ping_neighbor, runs=5, host="10.0.0.2")
        with capsys.disabled():
            print(f"\nping_neighbor on live mesh: p50={stats['p50']:.1f}ms "
                  f"p95={stats['p95']:.1f}ms max={stats['max']:.1f}ms")
        assert stats["p95"] < 5000
