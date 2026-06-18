#!/usr/bin/env python3
"""
3-node batman-adv style mesh topology for testing the WMN MCP server.
Based on the verified mn_wifi/examples/mesh.py reference implementation.
Run with: sudo python3 mininet/mesh_topo.py
"""

from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, mesh
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference


def topology():
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', ip='10.0.0.1/8', position='10,10,0')
    sta2 = net.addStation('sta2', ip='10.0.0.2/8', position='20,10,0')
    sta3 = net.addStation('sta3', ip='10.0.0.3/8', position='30,10,0')

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring nodes\n")
    net.configureNodes()

    info("*** Creating mesh links\n")
    net.addLink(sta1, cls=mesh, ssid='meshNet',
                intf='sta1-wlan0', channel=5, ht_cap='HT40+')
    net.addLink(sta2, cls=mesh, ssid='meshNet',
                intf='sta2-wlan0', channel=5, ht_cap='HT40+')
    net.addLink(sta3, cls=mesh, ssid='meshNet',
                intf='sta3-wlan0', channel=5, ht_cap='HT40+')

    info("*** Starting network\n")
    net.build()

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
