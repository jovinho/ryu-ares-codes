# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""
import json

from ryu.app.wsgi import WSGIApplication
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import route
from ryu.app.wsgi import Response


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

import networkx as nx
import topology_service as ts
import event_api_service as evt


class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.topologyService = ts.TopologyService()

    def ls(self,obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    #evento de packet_in
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        if eth.ethertype != ether_types.ETH_TYPE_ARP:
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id

        self.logger.info("packet in dp: %s, src: %s dest: %s in_port: %s \n\n", dpid, src, dst, msg.in_port)
        print "nodes"
        print self.topologyService.__getinstance__().net.nodes()
        #print self.net.nodes()
        print "edges"
        print self.topologyService.__getinstance__().net.edges()
        #print self.net.edges()

        if src not in self.topologyService.__getinstance__().net:
            portDict = { 'port' : msg.in_port }
            self.topologyService.__getinstance__().net.add_node(src)
            self.topologyService.__getinstance__().net.add_edge(src, dpid)
            self.topologyService.__getinstance__().net.add_edge(dpid, src, portDict)

        if dst in self.topologyService.__getinstance__().net:
            print("FINDIND SHORTEST PATH")
            #migrar o shortestpath pra dentro do servico
            path = nx.shortest_path(self.topologyService.__getinstance__().net, src, dst) # get shortest path
            next=path[path.index(dpid)+1] #get next hop
            print(self.topologyService.__getinstance__().net[dpid]) #e um dicionario
            out_port = self.topologyService.__getinstance__().net[dpid][next]['port'] #get output port
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        #if out_port != ofproto.OFPP_FLOOD:
            #self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    #evento de porta do switch
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        instance = evt.EventApiService()
        instance.send_request()

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        print "TRYING TO GET DAPATH"
        print ev

        #getting switches and links
        switch_list = get_switch(self.topology_api_app, None)

        print "SWITCHES"
        print switch_list

        datapaths = [switch.dp for switch in switch_list]
        print datapaths

        switches= [switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]

        for switch in switch_list:
            self.topologyService.__getinstance__().datapaths.append(switch)

        for link in links:
            self.topologyService.__getinstance__().links.append(link)

        #showing info

        print("SHOWING LNKS")
        print links
        print("SHOWING SWITCHES")
        print switches


        ##adding info do the topology service
        self.topologyService.__getinstance__().net.add_nodes_from(switches)
        self.topologyService.__getinstance__().net.add_edges_from(links)
