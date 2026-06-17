import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import server

def benchmark(name, func, runs=10, **kwargs):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        func(**kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    p50 = times[len(times)//2]
    p95 = times[int(len(times)*0.95)] if len(times) > 1 else times[0]
    return {
        "tool": name,
        "runs": runs,
        "min_ms": round(min(times), 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(max(times), 2),
    }

if __name__ == "__main__":
    print("=" * 60)
    print("  WMN MCP Server — Latency Benchmark")
    print(f"  Interface: {server.IFACE}")
    print("=" * 60)

    results = []
    results.append(benchmark("hello_world", server.hello_world))
    results.append(benchmark("get_routing_table", server.get_routing_table))
    results.append(benchmark("get_interface_stats", server.get_interface_stats))
    results.append(benchmark("get_interface_config", server.get_interface_config))
    results.append(benchmark("list_neighbors", server.list_neighbors, runs=5))
    results.append(benchmark("get_link_quality", server.get_link_quality, runs=5))
    results.append(benchmark("ping_neighbor", server.ping_neighbor, runs=5, host="192.168.0.1"))

    SLA_MS = {
        "hello_world": 2000,
        "get_routing_table": 2000,
        "get_interface_stats": 2000,
        "get_interface_config": 2000,
        "list_neighbors": 2000,
        "get_link_quality": 2000,
        "ping_neighbor": 5000,
    }

    print(f"\n{'Tool':<22} {'Min':>8} {'P50':>8} {'P95':>8} {'Max':>8}   SLA")
    print("-" * 70)
    for r in results:
        threshold = SLA_MS.get(r["tool"], 2000)
        sla = f"OK <{threshold}ms" if r["p95_ms"] < threshold else "OVER SLA"
        print(f"{r['tool']:<22} {r['min_ms']:>6}ms {r['p50_ms']:>6}ms "
              f"{r['p95_ms']:>6}ms {r['max_ms']:>6}ms   {sla}")

    os.makedirs("docs", exist_ok=True)
    with open("docs/latency_log.md", "w") as f:
        f.write("# Latency Benchmark Results\n\n")
        f.write(f"Machine: {os.uname().nodename}\n")
        f.write(f"Interface: {server.IFACE}\n\n")
        f.write("| Tool | Runs | Min (ms) | P50 (ms) | P95 (ms) | Max (ms) | SLA Threshold | Result |\n")
        f.write("|------|------|----------|----------|----------|----------|---------------|--------|\n")
        for r in results:
            threshold = SLA_MS.get(r["tool"], 2000)
            result_str = "PASS" if r["p95_ms"] < threshold else "FAIL"
            f.write(f"| {r['tool']} | {r['runs']} | {r['min_ms']} | "
                    f"{r['p50_ms']} | {r['p95_ms']} | {r['max_ms']} | {threshold}ms | {result_str} |\n")

    print(f"\nResults saved to docs/latency_log.md")
