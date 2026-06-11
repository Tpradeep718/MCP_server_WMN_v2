from mcp.server.fastmcp import FastMCP
import subprocess, yaml, os, re, datetime
from parsers import (
    parse_ip_route, parse_ip_stats,
    parse_iw_dev, parse_iwconfig,
    parse_batctl_neighbors, parse_station_dump
)

def load_config(path="config.yaml"):
    default = {
        "server":   {"name": "wmn-mcp", "transport": "stdio"},
        "network":  {"interface": "wlp4s0", "mesh_interface": "bat0",
                     "ping_count": 4, "command_timeout_seconds": 5},
        "security": {"privilege_token": "wmn-secret-2024",
                     "allow_write_operations": True},
        "logging":  {"level": "INFO"}
    }
    if os.path.exists(path):
        with open(path) as f:
            loaded = yaml.safe_load(f)
            if loaded:
                for section, values in loaded.items():
                    if section in default and isinstance(values, dict):
                        default[section].update(values)
    return default

CFG     = load_config()
NET     = CFG["network"]
SEC     = CFG["security"]
IFACE   = NET["interface"]
MESH    = NET["mesh_interface"]
TIMEOUT = NET["command_timeout_seconds"]
TOKEN   = SEC["privilege_token"]

mcp = FastMCP(CFG["server"]["name"])

def run_cmd(cmd, timeout=None):
    t = timeout or TIMEOUT
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=t)
        return {"stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode, "error": None}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "", "returncode": -1,
                "error": f"Command {cmd} timed out after {t}s"}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "", "returncode": -1,
                "error": f"Command not found: {cmd[0]}"}
    except Exception as e:
        return {"stdout": "", "stderr": "", "returncode": -1,
                "error": str(e)}

@mcp.tool()
def hello_world():
    """Test tool — confirms MCP server is running"""
    return {"status": "ok", "server": CFG["server"]["name"],
            "interface": IFACE, "transport": CFG["server"]["transport"],
            "tools": 7}

@mcp.tool()
def get_routing_table():
    """Get Linux IP routing table with gateway, device, and metric info"""
    result = run_cmd(["ip", "route"])
    if result["error"]:
        return {"error": result["error"]}
    if not result["stdout"].strip():
        return {"routes": [], "note": "Routing table is empty"}
    return {"routes": parse_ip_route(result["stdout"])}

@mcp.tool()
def get_interface_stats(interface: str = ""):
    """Get RX/TX bytes, packets and errors for all network interfaces"""
    result = run_cmd(["ip", "-s", "link"])
    if result["error"]:
        return {"error": result["error"]}
    stats = parse_ip_stats(result["stdout"])
    if interface:
        stats = [s for s in stats if s["interface"] == interface]
        if not stats:
            return {"error": f"Interface '{interface}' not found"}
    return {"interfaces": stats}

@mcp.tool()
def get_interface_config(interface: str = ""):
    """Get wireless config — channel, mode, ESSID, TX power"""
    iw_result  = run_cmd(["iw", "dev"])
    iwc_result = run_cmd(["iwconfig"])
    if iw_result["error"] and iwc_result["error"]:
        return {"error": "Both iw and iwconfig failed"}
    merged = {}
    if not iw_result["error"]:
        for item in parse_iw_dev(iw_result["stdout"]):
            merged[item["interface"]] = item
    if not iwc_result["error"]:
        for item in parse_iwconfig(iwc_result["stdout"] + iwc_result["stderr"]):
            name = item["interface"]
            if name in merged:
                merged[name].update(item)
            else:
                merged[name] = item
    results = list(merged.values())
    if interface:
        results = [r for r in results if r["interface"] == interface]
        if not results:
            return {"error": f"Interface '{interface}' not found"}
    return {"interfaces": results}

@mcp.tool()
def list_neighbors(interface: str = ""):
    """List all batman-adv mesh neighbors with last-seen time"""
    iface  = interface or MESH
    result = run_cmd(["sudo", "batctl", "meshif", iface, "n"])
    raw    = result["stdout"] + result["stderr"]
    if result["error"] and "timed out" in result["error"]:
        return {"error": result["error"]}
    if "not present" in raw or "not a batman-adv" in raw:
        return {"neighbors": [], "note": f"Interface {iface} not present — mesh not running yet"}
    neighbors = parse_batctl_neighbors(raw)
    return {"interface": iface, "neighbors": neighbors, "count": len(neighbors)}

@mcp.tool()
def get_link_quality(interface: str = ""):
    """Get per-peer RSSI, TX/RX bitrate and packet loss"""
    iface  = interface or IFACE
    result = run_cmd(["iw", "dev", iface, "station", "dump"])
    if result["error"]:
        return {"error": result["error"]}
    if "No such device" in result["stderr"]:
        return {"error": f"Interface '{iface}' not found"}
    if not result["stdout"].strip():
        return {"interface": iface, "stations": [],
                "note": "No stations associated yet"}
    stations = parse_station_dump(result["stdout"])
    return {"interface": iface, "stations": stations, "count": len(stations)}

@mcp.tool()
def ping_neighbor(host: str, count: int = 0):
    """Ping a mesh neighbor — returns RTT min/avg/max and packet loss"""
    if not host:
        return {"error": "host is required"}
    n      = count or NET["ping_count"]
    result = run_cmd(["ping", "-c", str(n), "-W", "2", host],
                     timeout=TIMEOUT + n * 3)
    if result["error"]:
        return {"error": result["error"]}
    out  = result["stdout"]
    loss = re.search(r'(\d+)% packet loss', out)
    rtt  = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)', out)
    sent = re.search(r'(\d+) packets transmitted', out)
    recv = re.search(r'(\d+) received', out)
    return {
        "host":        host,
        "transmitted": int(sent.group(1)) if sent else n,
        "received":    int(recv.group(1)) if recv else 0,
        "loss_pct":    float(loss.group(1)) if loss else 100.0,
        "rtt_min_ms":  float(rtt.group(1)) if rtt else None,
        "rtt_avg_ms":  float(rtt.group(2)) if rtt else None,
        "rtt_max_ms":  float(rtt.group(3)) if rtt else None,
    }

@mcp.tool()
def set_wifi_channel(interface: str, channel: int, token: str):
    """Change Wi-Fi channel on mesh interface. Requires privilege token."""
    if not SEC.get("allow_write_operations", False):
        return {"error": "write operations disabled in config"}
    if token != TOKEN:
        return {"error": "privilege denied — invalid token"}
    if not (1 <= channel <= 13):
        return {"error": f"invalid channel {channel} — must be 1–13"}
    check = run_cmd(["iw", "dev", interface, "info"])
    if check["error"] or "No such device" in check["stderr"]:
        return {"error": f"interface '{interface}' not found or not wireless"}
    result = run_cmd(["sudo", "iw", "dev", interface,
                      "set", "channel", str(channel)])
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/audit.log", "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} "
                    f"set_wifi_channel interface={interface} "
                    f"channel={channel} success={result['returncode']==0}\n")
    except Exception:
        pass
    if result["returncode"] == 0:
        return {"success": True, "interface": interface, "new_channel": channel}
    return {"success": False, "error": result["stderr"].strip() or "failed"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WMN MCP Server")
    parser.add_argument("--config",    default="config.yaml")
    parser.add_argument("--transport", default=None, choices=["stdio","http"])
    parser.add_argument("--port",      type=int, default=8000)
    args = parser.parse_args()

    cfg       = load_config(args.config)
    transport = args.transport or cfg["server"]["transport"]

    print("=" * 50)
    print("  WMN MCP Server starting up")
    print(f"  Interface  : {cfg['network']['interface']}")
    print(f"  Mesh iface : {cfg['network']['mesh_interface']}")
    print(f"  Transport  : {transport}")
    print(f"  Timeout    : {cfg['network']['command_timeout_seconds']}s")
    print(f"  Write ops  : {cfg['security'].get('allow_write_operations')}")
    print("=" * 50)

    if transport == "http":
        print(f"  HTTP port  : {args.port}")
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
