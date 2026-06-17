
## Week 6-7 Hardening Notes

All tools now return structured error responses for the following failure modes:
- Command not found (missing CLI tool)
- Command timeout (configurable via command_timeout_seconds)
- Interface not found (invalid interface name passed)
- Empty/missing data (graceful empty list + note, not an error)
- Partial source failure (get_interface_config returns partial data if one of iw/iwconfig fails)
- Malformed CLI output (skipped gracefully, never crashes)
- Sudo password prompt (list_neighbors uses sudo -n to fail fast instead of hanging)

Total test coverage: 80 tests (parsers + tool-level with mocked subprocess)
Latency SLA verified: all read tools <2s p95, ping_neighbor <5s p95
