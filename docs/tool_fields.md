# MCP Tool Field Mapping

## get_routing_table
CLI: ip route
Fields: destination, gateway, dev, proto, src, metric

## get_interface_stats  
CLI: ip -s link
Fields: interface, state, rx_bytes, rx_packets, rx_errors, rx_dropped, tx_bytes, tx_packets, tx_errors

## get_interface_config
CLI: iw dev + iwconfig
Fields: interface, type, addr, essid, mode, access_point, channel

## list_neighbors
CLI: batctl meshif bat0 n
Fields: interface, neighbor_mac, last_seen_seconds

## get_routing_table (batman)
CLI: batctl meshif bat0 o
Fields: originator_mac, last_seen, quality, nexthop_mac, outgoing_if
