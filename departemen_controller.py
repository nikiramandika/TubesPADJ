from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3

class ACLCampus(app_manager.RyuApp):
    OFP_VERSION = [ofproto_v1_3.OFP_VERSION]

    # Subnet yang aksesnya harus dilindungi
    ADMIN     = ("192.168.20.", "192.168.21.")   # Adm & Pimpinan
    BLOCKERS  = ("192.168.10.", "192.168.31.", "192.168.22.", "192.168.41.", "192.168.43.")

    def __init__(self, *args, **kwargs):
        super(ACLCampus, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Default rule: drop semua dulu
        match = parser.OFPMatch()
        actions = []
        self.add_flow(datapath, 0, match, actions)

        # Allow all except admin/pimpinan
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, 1, match, actions)

        # BLOCK RULES
        for blk in self.BLOCKERS:
            for adm in self.ADMIN:
                match = parser.OFPMatch(ipv4_src=(blk + "0/24"),
                                        ipv4_dst=(adm + "0/24"),
                                        eth_type=0x0800)
                self.add_flow(datapath, 100, match, [])

                match = parser.OFPMatch(ipv4_src=(adm + "0/24"),
                                        ipv4_dst=(blk + "0/24"),
                                        eth_type=0x0800)
                self.add_flow(datapath, 100, match, [])

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst)
        datapath.send_msg(mod)
