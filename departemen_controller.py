"""
departemen_controller.py
Ryu controller (OpenFlow 1.3) untuk Topologi Departemen
Fitur:
- Per-switch MAC learning (learning switch)
- ARP handling: ARP diflood supaya resolusi MAC berhasil
- Firewall rules (zone-based) sesuai skema:
    - Mahasiswa -> Pimpinan  : BLOCK
    - Mahasiswa -> Ujian     : BLOCK (selama ujian)
    - Mahasiswa -> Administrasi (opsional): BLOCK (kita blok kalau mau)
    - Administrasi hanya izinkan dari administrasi & pimpinan (aturan contoh)
- Logging: ALLOWED / BLOCKED messages
- Flow install menggunakan match eth_dst saja (agar tidak terlalu spesifik)
"""

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
        # mac_to_port per-datapath (dpid)
        self.mac_to_port = {}

        # Define zone networks (sesuai topologi)
        # G9:
        self.zone_g9_l1 = ip_network("192.168.10.0/27")      # Ruang Kuliah + AP (Mahasiswa L1)
        self.zone_g9_l2_dosen = ip_network("192.168.10.32/27")
        self.zone_g9_l2_admin = ip_network("192.168.10.64/27")
        self.zone_g9_l2_pimpinan = ip_network("192.168.10.96/27")
        self.zone_g9_l2_ujian = ip_network("192.168.10.128/27")
        self.zone_g9_l3_lab1 = ip_network("192.168.10.160/27")
        self.zone_g9_l3_lab2 = ip_network("192.168.10.192/27")
        self.zone_g9_l3_lab3 = ip_network("192.168.10.224/27")
        self.zone_g9_l3_mhs = ip_network("192.168.10.240/28")  # Mahasiswa L3 AP+hosts

        # G10:
        self.zone_g10_l1 = ip_network("172.16.21.0/28")
        self.zone_g10_l2 = ip_network("172.16.21.16/28")
        self.zone_g10_l3 = ip_network("172.16.21.32/27")

        # We'll use list-based blocking rules (src_net, dst_net)
        self.block_rules = [
            # Block mahasiswa (G9 L3 + G9 L1 + G10 APs) -> pimpinan (VERY HIGH)
            (self.zone_g9_l1, self.zone_g9_l2_pimpinan),
            (self.zone_g9_l3_mhs, self.zone_g9_l2_pimpinan),
            (self.zone_g10_l1, self.zone_g9_l2_pimpinan),  # example cross-building
            (self.zone_g10_l2, self.zone_g9_l2_pimpinan),

            # Block mahasiswa -> ujian zone
            (self.zone_g9_l1, self.zone_g9_l2_ujian),
            (self.zone_g9_l3_mhs, self.zone_g9_l2_ujian),
            (self.zone_g10_l1, self.zone_g9_l2_ujian),

            # Block students (G10 APs) -> admin/pimpinan in G9 (example)
            (self.zone_g10_l1, self.zone_g9_l2_admin),
            (self.zone_g10_l2, self.zone_g9_l2_admin),
        ]

        # Optional: allow-lists (exceptions) can be appended as needed
        # e.g., allow admin hosts (pimpinan) to reach everything:
        # self.allow_rules = [(self.zone_g9_l2_pimpinan, ip_network('0.0.0.0/0'))]

    # Helper: add flow
    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id and buffer_id != ofproto.OFP_NO_BUFFER:
            mod = parser.OFPFlowMod(datapath=datapath,
                                    buffer_id=buffer_id,
                                    priority=priority,
                                    match=match,
                                    instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath,
                                    priority=priority,
                                    match=match,
                                    instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    # Table-miss: send to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        # priority 0 - table-miss
        self.add_flow(datapath, 0, match, actions)

    # Check if packet should be blocked according to block_rules
    def check_block(self, src_ip, dst_ip):
        try:
            s_ip = ip_address(src_ip)
            d_ip = ip_address(dst_ip)
        except Exception:
            return False

        for src_net, dst_net in self.block_rules:
            if s_ip in src_net and d_ip in dst_net:
                return True
        return False

    # Packet-In handler: ARP flood, learning, firewall, flow-install
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match.get('in_port')

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        # ignore lldp packets (topology discovery)
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src = eth.src
        dst = eth.dst

        # init mac table for this dpid
        self.mac_to_port.setdefault(dpid, {})
        # learning
        self.mac_to_port[dpid][src] = in_port

        # Handle ARP: flood so ARP resolution works across switches
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            # Log ARP for debugging
            self.logger.debug("ARP %s -> %s (dpid=%s, in_port=%s)", arp_pkt.src_ip, arp_pkt.dst_ip, dpid, in_port)
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=msg.buffer_id,
                                      in_port=in_port,
                                      actions=actions,
                                      data=data)
            datapath.send_msg(out)
            return

        # IPv4 packet: enforce firewall rules
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst

            if self.check_block(src_ip, dst_ip):
                self.logger.info("[BLOCKED] %s -> %s (dpid=%s)", src_ip, dst_ip, dpid)
                # drop packet: do nothing further
                return
            else:
                self.logger.info("[ALLOWED] %s -> %s (dpid=%s)", src_ip, dst_ip, dpid)

        # Decide out port for this switch
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow on this switch that matches eth_dst only.
        # This helps forwarding at switch level without matching eth_src.
        match = parser.OFPMatch(eth_dst=dst)
        # Install flow (use buffer_id so first packet may be handled)
        self.add_flow(datapath, priority=10, match=match, actions=actions, buffer_id=msg.buffer_id)

        # send packet out (if not buffered)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=in_port,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
