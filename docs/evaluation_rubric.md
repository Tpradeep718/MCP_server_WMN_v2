# Evaluation Rubric — WMN MCP Server

## Dimensions

### 1. Tool Correctness (pass/fail per tool call)
- Does the tool return structured JSON with expected fields?
- Are field values accurate compared to raw CLI output?
- Are error cases handled gracefully (structured error, not crash)?

### 2. Response Latency (measured in ms)
- Read tools: p95 must be < 2000ms
- Probe tools: p95 must be < 5000ms
- Measured via benchmark.py (10 runs per tool)

### 3. AI Plan Quality (1-5 scale)
Scoring criteria for multi-step AI-driven tasks:
- 5: Correct tool sequence, correct interpretation, actionable conclusion
- 4: Correct tools, minor interpretation gap
- 3: Correct tools, but conclusion partially wrong or incomplete
- 2: Wrong tool selected for at least one step
- 1: Failed to use tools at all, or completely wrong conclusion

## Test Scenarios

| # | Prompt | Expected tools called | Correct outcome |
|---|--------|-----------------------|-----------------|
| 1 | "What is the current routing table?" | get_routing_table | Returns all routes with correct fields |
| 2 | "How much traffic has passed through sta1-mp0?" | get_interface_stats | Returns RX/TX bytes for correct interface |
| 3 | "What channel is the mesh running on?" | get_interface_config | Returns channel 5 |
| 4 | "Ping 10.0.0.2 and tell me if the link is healthy" | ping_neighbor | 0% loss = healthy conclusion |
| 5 | "Who are sta1's mesh neighbors?" | list_neighbors | Correct empty/populated result |
| 6 | "What is the signal strength to each peer?" | get_link_quality | RSSI values returned per peer |
| 7 | "Give me a complete health snapshot of sta1" | get_interface_stats + get_interface_config + get_link_quality | Synthesized summary |
| 8 | "Compare link quality to 10.0.0.2 and 10.0.0.3" | ping_neighbor x2 | Comparative conclusion |
| 9 | "Is there a default gateway configured?" | get_routing_table | Correct gateway or null interpretation |
| 10 | "Change the channel to 6" | set_wifi_channel | Token validation enforced |
