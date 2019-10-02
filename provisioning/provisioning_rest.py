import json

from ryu.controller.handler import set_ev_cls
from ryu.lib.mac import haddr_to_bin

from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import route
from ryu.app.wsgi import WSGIApplication
from ryu.controller import dpset
from ryu.app.ofctl import api
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link, get_host
from ryu.topology import event, switches

import networkx as nx
import topology_service as ts



class ProvisioningAPI(app_manager.RyuApp):
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(ProvisioningAPI, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        print "DPSET"
        print self.dpset.dps
        wsgi = kwargs['wsgi']
        wsgi.register(ProvisioningController, {'topology_api_app': self})


class ProvisioningController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(ProvisioningController, self).__init__(req, link, data, **config)
        self.topology_api_app = data['topology_api_app']
        self.topologyService = ts.TopologyService()


    @route('provisioning', '/provisioning/add', methods=['POST'])
    def add_provisioning(self, req, **kwargs):
        print req.body
        param = req.json if req.body else {} #transformando em mapa

        src = param["source"]
        dst = param["destination"]

        print "NETWORK"
        print self.topologyService.__getinstance__().net

        #buscando melhor caminho
        path = nx.shortest_path(self.topologyService.__getinstance__().net, src, dst) # get shortest path

        print "PATH"
        print path

        self._installflow(src, dst, path)

        body = json.dumps({ 'status': 200, 'message': 'Caminho Provisionado', 'source': src, 'destination': dst})

        return Response(content_type="application/json", body=body)

    @route('topology', '/topology/switches', methods=['GET'])
    def list_switches(self, req, **kwargs):
        return self._switches(req, **kwargs)

    @route('topology', '/topology/switches/{dpid}',
           methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def get_switch(self, req, **kwargs):
        return self._switches(req, **kwargs)

    # @route('discovery', '/discoveryv0', methods=['GET'])
    # def discovery(self, req, **kwargs):
    #     return self._discovery(req, **kwargs)

    # def _discovery(self, req, **kwargs):
    #     nodes = self.topologyService.__getinstance__().net.nodes()
    #     links = self.topologyService.__getinstance__().net.edges()
    #     body = json.dumps({ 'datapaths': nodes, 'links': links})
    #     return Response(content_type='application/json', body=body)


    def _switches(self, req, **kwargs):
        dpid = None
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        switches = get_switch(self.topology_api_app, dpid)
        body = json.dumps([switch.to_dict() for switch in switches])
        return Response(content_type='application/json', body=body)

    def _extractdatapaths(self, switches):
        datapaths = {}
        for switch in switches:
            dp = switch.dp
            datapaths[dp.id] = dp
        return datapaths

    def _installflow(self, src, dst, path):
        switches = get_switch(self.topology_api_app, None)
        datapaths = self._extractdatapaths(switches)
        print datapaths

        for node in path:
            if node == src:
                print "SOURCE"
            elif node == dst:
                print "DESTINATION"
            else:
                #install flow
                print "install flow"
                datapath = datapaths[node]
                next = path[path.index(datapath.id)+1] #next HOP
                previous = path[path.index(datapath.id)-1]
                # print "DATAPATH"
                # print node
                # print "NEXT HOP"
                # print next
                # print "PREVIOUS HOP"
                # print previous
                in_port = self.topologyService.__getinstance__().net[datapath.id][previous]['port'] #get input port
                out_port = self.topologyService.__getinstance__().net[datapath.id][next]['port'] #get output port
                # print "IN PORT"
                # print in_port
                # print "OUT PORT"
                # print out_port
                #cria a action
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, in_port, dst, actions)


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
        print "MESSAGE SENT"

