# WMN MCP Server — Deployment Guide

## Prerequisites

### System requirements
- Ubuntu 22.04 LTS or 24.04 LTS (tested on both)
- Python 3.10 or higher
- sudo privileges for mesh interface operations
- Git

### Required CLI tools
```bash
sudo apt install -y iw batctl wireless-tools net-tools iputils-ping
```

### For emulated testing (Mininet-WiFi)
```bash
# Clone and install Mininet-WiFi
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv < /dev/null
```

---

## Option A — Local stdio deployment (recommended for development)

### Step 1: Clone the repository
```bash
git clone https://github.com/Tpradeep718/MCP_server_WMN_v2.git
cd MCP_server_WMN_v2
```

### Step 2: Create virtual environment
```bash
python3 -m venv wmn-mcp-env
source wmn-mcp-env/bin/activate
pip install mcp[cli] pyyaml
```

### Step 3: Configure
```bash
nano config.yaml
```

Key settings:
```yaml
network:
  interface: wlp4s0      # your Wi-Fi interface name (check with: iw dev)
  mesh_interface: bat0   # batman-adv interface (created when mesh is running)
  ping_count: 4
  command_timeout_seconds: 5

security:
  privilege_token: wmn-secret-2024   # CHANGE THIS in production
  allow_write_operations: true
```

### Step 4: Run the server
```bash
python3 src/server.py
```

### Step 5: Connect an AI client
Add to Claude Desktop config (`~/.config/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "wmn-mcp": {
      "command": "/path/to/wmn-mcp-env/bin/python3",
      "args": ["/path/to/src/server.py"]
    }
  }
}
```

Or for Cline (VS Code), edit `cline_mcp_settings.json`:
```json
{
  "mcpServers": {
    "wmn-mcp": {
      "command": "/path/to/src/server.py",
      "args": [],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## Option B — Docker deployment (recommended for production)

### Step 1: Build the container
```bash
git clone https://github.com/Tpradeep718/MCP_server_WMN_v2.git
cd MCP_server_WMN_v2
docker compose build
```

### Step 2: Configure
Edit `config.yaml` with your interface names and token before starting.

### Step 3: Run
```bash
docker compose up -d
```

The server starts on HTTP transport at port 8000.

### Step 4: Verify
```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

Expected response: JSON with `Missing session ID` — this confirms the server
is running and speaking correct MCP protocol (the session ID is provided
by the real MCP client during the initialization handshake).

---

## Option C — Mininet-WiFi emulated mesh (for testing without hardware)

### Step 1: Start the mesh topology
```bash
sudo python3 mininet/mesh_topo.py
```

Leave this running. The mesh creates three virtual stations:
- sta1: 10.0.0.1 (primary node, where server runs)
- sta2: 10.0.0.2
- sta3: 10.0.0.3

### Step 2: Configure passwordless sudo for nsenter
```bash
sudo bash -c 'echo "YOUR_USER ALL=(ALL) NOPASSWD: /usr/bin/nsenter" > /etc/sudoers.d/wmn-mcp-mesh'
sudo chmod 0440 /etc/sudoers.d/wmn-mcp-mesh
```

### Step 3: Connect AI client to mesh-aware server
Use the provided wrapper script which enters sta1's network namespace:
```bash
# Test it works
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | ./run_in_mesh.sh
```

Add to Cline config:
```json
{
  "mcpServers": {
    "wmn-mcp": {
      "command": "/full/path/to/run_in_mesh.sh",
      "args": [],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## Verifying the interface name on your machine

Different Linux distributions and hardware use different interface names:

```bash
iw dev          # shows wireless interfaces (look for type mesh point or managed)
ip link show    # shows all interfaces
```

Common names:
- `wlp4s0` — typical on ThinkCentre/OptiPlex with PCIe Wi-Fi
- `wlan0` — common on Raspberry Pi and USB Wi-Fi adapters
- `sta1-mp0` — Mininet-WiFi emulated mesh point interface

Update `config.yaml` with the correct name before running.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Interface not found` | Wrong interface name in config | Run `iw dev` and update config.yaml |
| `sudo requires password` | Missing sudoers rule | Add NOPASSWD rule for nsenter |
| `bat0 not present` | batman-adv not loaded | `sudo modprobe batman-adv` |
| `Connection closed` in Cline | Server exits immediately | Check nsenter passwordless sudo |
| `70%+ packet loss` in Mininet | wmediumd interference model | Remove `link=wmediumd` from topology |
| `Port 6277 in use` | Previous inspector still running | `pkill -f mcp` |
