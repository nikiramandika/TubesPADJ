from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, arp, ipv4
from ryu.lib.packet import ether_types
from ipaddress import ip_network, ip_address


class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)

        # MAC learning per switch
        self.mac_to_port = {}

        # Firewall rules
        self.block_rules = [
            ("192.168.10.240/28", "192.168.10.96/27"),   # Mhs → Pimpinan
            ("192.168.10.240/28", "192.168.10.160/27"),  # Mhs → Lab
            ("172.16.21.0/28", "172.16.21.32/27"),       # G10 L1 → Dosen
            ("172.16.21.16/28", "172.16.21.32/27"),      # G10 L2 → Dosen
        ]

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            actions
        )]

        mod = parser.OFPFlowMod(datapath=datapath,
                                priority=priority,
                                match=match,
                                instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser

        # Default rule: always send unknown packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 0, match, actions)

    def check_block(self, src_ip, dst_ip):
        for s, d in self.block_rules:
            if ip_address(src_ip) in ip_network(s) and ip_address(dst_ip) in ip_network(d):
                return True
        return False

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        in_port = msg.match["in_port"]

        src = eth.src
        dst = eth.dst

        # MAC learning
        self.mac_to_port[dpid][src] = in_port

        # ====== ARP HANDLING (fix ARP not reachable) ======
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            out_port = ofproto.OFPP_FLOOD
            actions = [parser.OFPActionOutput(out_port)]

            # No flow install; always broadcast ARP
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=msg.data
            )
            datapath.send_msg(out)
            return

        # IPv4 – firewall check
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst

            if self.check_block(src_ip, dst_ip):
                self.logger.info("BLOCKED %s → %s", src_ip, dst_ip)
                return
            else:
                self.logger.info("ALLOW %s → %s", src_ip, dst_ip)

        # NORMAL SWITCHING
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow for learned destination
        match = parser.OFPMatch(eth_src=src, eth_dst=dst)
        self.add_flow(datapath, 10, match, actions)

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=in_port,
                                  actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
