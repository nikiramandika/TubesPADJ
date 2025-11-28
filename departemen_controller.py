from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
import ipaddress

class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.logger.info("Department Firewall Controller Started")

    def ip_in_subnet(self, ip_str, subnet_str):
        """Check if IP address is in subnet"""
        try:
            return ipaddress.ip_address(ip_str) in ipaddress.ip_network(subnet_str, strict=False)
        except:
            return False

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.logger.info(f"Switch {datapath.id} connected")

        # Install table-miss flow entry untuk packet ke controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # --- LOGIKA FIREWALL BERDASARKAN ZONA SENSITIVITAS ---
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        blocked = False

        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Define ALL subnets based on topology
            RUANG_KULIAH_G9_L1 = "192.168.10.0/27"          # ap9l1, rk9l1
            DOSEN_G9_L2_S1 = "192.168.10.32/27"         # d9s1_1, d9s1_2
            ADMIN_G9_L2_S2 = "192.168.10.64/27"         # ad9s2_1, ad9s2_2
            PIMPINAN_G9_L2_S3 = "192.168.10.96/27"       # p9s3_1, p9s3_2
            UJIAN_G9_L2_S4 = "192.168.10.128/27"        # uj9s4_1, uj9s4_2
            LAB1_G9_L3_S1 = "192.168.10.160/27"       # lab1_1, lab1_2
            LAB2_G9_L3_S2 = "192.168.10.192/27"       # lab2_1, lab2_2
            LAB3_G9_L3_S3 = "192.168.10.224/27"       # lab3_1, lab3_2
            MAHASISWA_G9_L3_AP = "192.168.10.240/28"     # ap9l3_1, ap9l3_2, ap9l3_3

            RUANG_KULIAH_G10_L1 = "172.16.21.0/28"        # ap10l1, rk10l1
            DOSEN_G10_L2 = "172.16.21.16/28"            # d10l2_1, d10l2_2
            AP_MAHASISWA_G10 = ["172.16.21.1", "172.16.21.19", "172.16.21.35"]  # ap10l1, ap10l2, ap10l3
            AP_AULA_G10 = "172.16.21.21"              # apaula

            # FAST BLOCKING: Install flow rules untuk memblokir traffic tertentu secara permanen
            # Block Mahasiswa -> Dosen (192.168.10.32/27)
            if self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) and self.ip_in_subnet(dst_ip, DOSEN_G9_L2_S1):
                self.logger.error(f"*** IMMEDIATE BLOCK: Mahasiswa {src_ip} -> Dosen {dst_ip}")
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                self.add_flow(datapath, 200, match, [], hard_timeout=300)  # High priority block
                return  # JANGAN forward

            # Block Mahasiswa -> Admin (192.168.10.64/27)
            if self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) and self.ip_in_subnet(dst_ip, ADMIN_G9_L2_S2):
                self.logger.error(f"*** IMMEDIATE BLOCK: Mahasiswa {src_ip} -> Admin {dst_ip}")
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                self.add_flow(datapath, 200, match, [], hard_timeout=300)
                return  # JANGAN forward

            # Block Mahasiswa -> Pimpinan (192.168.10.96/27)
            if self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) and self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3):
                self.logger.error(f"*** IMMEDIATE BLOCK: Mahasiswa {src_ip} -> Pimpinan {dst_ip}")
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                self.add_flow(datapath, 200, match, [], hard_timeout=300)
                return  # JANGAN forward

            # Block Mahasiswa AP G10 -> Admin/Pimpinan
            if src_ip in AP_MAHASISWA_G10:
                if self.ip_in_subnet(dst_ip, ADMIN_G9_L2_S2) or self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3):
                    self.logger.error(f"*** IMMEDIATE BLOCK: AP Mahasiswa {src_ip} -> zona sensitif {dst_ip}")
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 200, match, [], hard_timeout=300)
                    return  # JANGAN forward

            # Block AP Aula -> Pimpinan
            if src_ip == AP_AULA_G10 and self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3):
                self.logger.error(f"*** IMMEDIATE BLOCK: AP Aula {src_ip} -> Pimpinan {dst_ip}")
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                self.add_flow(datapath, 200, match, [], hard_timeout=300)
                return  # JANGAN forward

            # Rules untuk VERY HIGH-SENSITIVITY (Pimpinan & Sekretariat - 192.168.10.96/27)
            if self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3):
                if not (self.ip_in_subnet(src_ip, ADMIN_G9_L2_S2) or
                        self.ip_in_subnet(src_ip, PIMPINAN_G9_L2_S3)):
                    self.logger.error(f"*** BLOCKED: Akses tidak diizinkan ke Zona Pimpinan & Sekretariat dari {src_ip} ke {dst_ip}")
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 100, match, [], hard_timeout=300)
                    return  # JANGAN forward packet yang diblok

            # Rules untuk HIGH-SENSITIVITY (Administrasi & Keuangan - 192.168.10.64/27)
            if self.ip_in_subnet(dst_ip, ADMIN_G9_L2_S2):
                if not (self.ip_in_subnet(src_ip, ADMIN_G9_L2_S2) or
                        self.ip_in_subnet(src_ip, PIMPINAN_G9_L2_S3)):
                    self.logger.error(f"*** BLOCKED: Akses tidak diizinkan ke Zona Administrasi & Keuangan dari {src_ip} ke {dst_ip}")
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 100, match, [], hard_timeout=300)
                    return  # JANGAN forward packet yang diblok

            # Rules untuk CONTROLLED & ISOLATED (Ujian - 192.168.10.128/27)
            if self.ip_in_subnet(dst_ip, UJIAN_G9_L2_S4):
                if (self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) or
                    self.ip_in_subnet(src_ip, MAHASISWA_G9_L3_AP)):  # Mahasiswa
                    self.logger.error(f"*** BLOCKED: Mahasiswa tidak diizinkan mengakses Zona Ujian dari {src_ip} ke {dst_ip}")
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 100, match, [], hard_timeout=300)
                    return  # JANGAN forward packet yang diblok

            # Rules untuk AP Mahasiswa Gedung G10
            if src_ip in AP_MAHASISWA_G10:
                if (self.ip_in_subnet(dst_ip, ADMIN_G9_L2_S2) or
                    self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3)):
                    self.logger.error(f"*** BLOCKED: Mahasiswa AP G10 tidak diizinkan akses zona sensitif dari {src_ip} ke {dst_ip}")
                    # Install permanent block flow
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 100, match, [], hard_timeout=300)
                    return  # JANGAN forward packet yang diblok
                else:
                    self.logger.info(f"ALLOWED: Mahasiswa AP G10 mengakses {dst_ip} dari {src_ip}")

            # Rules untuk AP Aula Gedung G10
            if src_ip == AP_AULA_G10:
                if self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3):
                    self.logger.error(f"*** BLOCKED: AP Aula tidak diizinkan akses zona Pimpinan dari {src_ip} ke {dst_ip}")
                    # Install permanent block flow
                    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                    self.add_flow(datapath, 100, match, [], hard_timeout=300)
                    return  # JANGAN forward packet yang diblok
                else:
                    self.logger.info(f"ALLOWED: AP Aula mengakses {dst_ip} dari {src_ip}")

            # FAST PATH: Install flow rules untuk allowed traffic agar tidak ke controller lagi
            # Allow Dosen -> Semua zona (high priority)
            if (self.ip_in_subnet(src_ip, DOSEN_G9_L2_S1) or
                self.ip_in_subnet(src_ip, DOSEN_G10_L2) or
                self.ip_in_subnet(src_ip, PIMPINAN_G9_L2_S3)):
                if not blocked:
                    self.logger.info(f"*** FAST-ALLOW: Dosen/Pimpinan {src_ip} -> {dst_ip}")
                    # Install high priority fast path flow
                    if dst in self.mac_to_port[dpid]:
                        out_port = self.mac_to_port[dpid][dst]
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                        actions = [parser.OFPActionOutput(out_port)]
                        self.add_flow(datapath, 150, match, actions, idle_timeout=60, hard_timeout=300)  # High priority
                    blocked = False  # Allow to proceed with fast path

            # Allow Admin -> Pimpinan & Mahasiswa
            if self.ip_in_subnet(src_ip, ADMIN_G9_L2_S2):
                if (self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2_S3) or
                    self.ip_in_subnet(dst_ip, RUANG_KULIAH_G9_L1) or
                    self.ip_in_subnet(dst_ip, MAHASISWA_G9_L3_AP)):
                    if not blocked:
                        self.logger.info(f"*** FAST-ALLOW: Admin {src_ip} -> {dst_ip}")
                        # Install fast path flow
                        if dst in self.mac_to_port[dpid]:
                            out_port = self.mac_to_port[dpid][dst]
                            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(datapath, 140, match, actions, idle_timeout=60, hard_timeout=300)
                        blocked = False

            # Allow Lab -> Lab, Mahasiswa -> Mahasiswa (same level)
            if (self.ip_in_subnet(src_ip, LAB1_G9_L3_S1) or
                self.ip_in_subnet(src_ip, LAB2_G9_L3_S2) or
                self.ip_in_subnet(src_ip, LAB3_G9_L3_S3)):
                if (self.ip_in_subnet(dst_ip, LAB1_G9_L3_S1) or
                    self.ip_in_subnet(dst_ip, LAB2_G9_L3_S2) or
                    self.ip_in_subnet(dst_ip, LAB3_G9_L3_S3) or
                    self.ip_in_subnet(dst_ip, RUANG_KULIAH_G9_L1) or
                    self.ip_in_subnet(dst_ip, MAHASISWA_G9_L3_AP)):
                    if not blocked:
                        self.logger.info(f"*** FAST-ALLOW: Lab/Mahasiswa {src_ip} -> {dst_ip}")
                        # Install fast path flow
                        if dst in self.mac_to_port[dpid]:
                            out_port = self.mac_to_port[dpid][dst]
                            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                            actions = [parser.OFPActionOutput(out_port)]
                            self.add_flow(datapath, 130, match, actions, idle_timeout=60, hard_timeout=300)
                        blocked = False

            # Universal same subnet fast path (lowest priority)
            src_network = None
            dst_network = None

            if src_ip.startswith("192.168.10."):
                src_network = "G9"
            elif src_ip.startswith("172.16.21."):
                src_network = "G10"

            if dst_ip.startswith("192.168.10."):
                dst_network = "G9"
            elif dst_ip.startswith("172.16.21."):
                dst_network = "G10"

            # Fast path untuk traffic dalam network yang sama
            if src_network == dst_network and src_network is not None:
                if not blocked:
                    self.logger.info(f"*** FAST-ALLOW: Same network {src_ip} -> {dst_ip}")
                    if dst in self.mac_to_port[dpid]:
                        out_port = self.mac_to_port[dpid][dst]
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                        actions = [parser.OFPActionOutput(out_port)]
                        self.add_flow(datapath, 100, match, actions, idle_timeout=60, hard_timeout=300)
                        blocked = False

            # Fast path untuk inter-building (allowed by default)
            if src_network != dst_network and src_network is not None and dst_network is not None:
                if not blocked:
                    self.logger.info(f"*** FAST-ALLOW: Inter-building {src_ip} -> {dst_ip}")
                    if dst in self.mac_to_port[dpid]:
                        out_port = self.mac_to_port[dpid][dst]
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip, ipv4_dst=dst_ip)
                        actions = [parser.OFPActionOutput(out_port)]
                        self.add_flow(datapath, 90, match, actions, idle_timeout=60, hard_timeout=300)
                        blocked = False

        # --- END FIREWALL ---

        # Jika packet diblok, jangan forward
        if blocked:
            return

        # Determine output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        # Forward packet yang diizinkan
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)