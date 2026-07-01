# Latency Benchmark Results

Machine: maruf-OptiPlex-7010
Interface: eno1

| Tool | Runs | Min (ms) | P50 (ms) | P95 (ms) | Max (ms) | SLA Threshold | Result |
|------|------|----------|----------|----------|----------|---------------|--------|
| hello_world | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 2000ms | PASS |
| get_routing_table | 10 | 1.82 | 2.33 | 3.29 | 3.29 | 2000ms | PASS |
| get_interface_stats | 10 | 1.34 | 1.88 | 2.4 | 2.4 | 2000ms | PASS |
| get_interface_config | 10 | 2.01 | 2.34 | 2.76 | 2.76 | 2000ms | PASS |
| list_neighbors | 5 | 6.9 | 7.43 | 7.94 | 7.94 | 2000ms | PASS |
| get_link_quality | 5 | 1.19 | 1.27 | 1.37 | 1.37 | 2000ms | PASS |
| ping_neighbor | 5 | 3070.18 | 3071.95 | 3091.27 | 3091.27 | 5000ms | PASS |
