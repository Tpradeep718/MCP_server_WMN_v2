# Latency Benchmark Results

Machine: maruf-OptiPlex-7010
Interface: eno1

| Tool | Runs | Min (ms) | P50 (ms) | P95 (ms) | Max (ms) | SLA Threshold | Result |
|------|------|----------|----------|----------|----------|---------------|--------|
| hello_world | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 2000ms | PASS |
| get_routing_table | 10 | 1.26 | 1.99 | 2.82 | 2.82 | 2000ms | PASS |
| get_interface_stats | 10 | 1.4 | 1.93 | 2.32 | 2.32 | 2000ms | PASS |
| get_interface_config | 10 | 1.97 | 2.33 | 2.78 | 2.78 | 2000ms | PASS |
| list_neighbors | 5 | 6.02 | 6.84 | 7.23 | 7.23 | 2000ms | PASS |
| get_link_quality | 5 | 0.89 | 1.21 | 1.57 | 1.57 | 2000ms | PASS |
| ping_neighbor | 5 | 3071.31 | 3071.98 | 3089.34 | 3089.34 | 5000ms | PASS |
