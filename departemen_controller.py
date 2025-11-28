from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, udp, icmp, arp
from ryu.lib.packet import ether_types
import ipaddress

class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

        # --- DEFINISI ZONA & SUBNET ---
        # Disimpan dalam dictionary agar mudah dicari namanya untuk logging
        self.subnets = {
            'RUANG_KULIAH_G9_L1': ipaddress.ip_network("192.168.10.0/27"),
            'DOSEN_G9_L2': ipaddress.ip_network("192.168.10.32/27"),
            'ADMIN_G9_L2': ipaddress.ip_network("192.168.10.64/27"),
            'PIMPINAN_G9_L2': ipaddress.ip_network("192.168.10.96/27"),
            'UJIAN_G9_L2': ipaddress.ip_network("192.168.10.128/27"),
            'LAB1_G9_L3': ipaddress.ip_network("192.168.10.160/27"),
            'LAB2_G9_L3': ipaddress.ip_network("192.168.10.192/27"),
            'LAB3_G9_L3': ipaddress.ip_network("192.168.10.224/27"),
            'MAHASISWA_G9_L3': ipaddress.ip_network("192.168.10.240/28"),
            
            'RUANG_KULIAH_G10_L1': ipaddress.ip_network("172.16.21.0/28"),
            'DOSEN_G10_L2': ipaddress.ip_network("172.16.21.16/28"),
            'DOSEN_G10_L3': ipaddress.ip_network("172.16.21.32/27")
        }

        # Grouping untuk logic yang lebih mudah
        self.SENSITIVE_ZONES = ['ADMIN_G9_L2', 'PIMPINAN_G9_L2']
        self.DOSEN_ZONES = ['DOSEN_G9_L2', 'DOSEN_G10_L2', 'DOSEN_G10_L3']
        self.STUDENT_ZONES = ['RUANG_KULIAH_G9_L1', 'MAHASISWA_G9_L3', 
                              'LAB1_G9_L3', 'LAB2_G9_L3', 'LAB3_G9_L3', 
                              'RUANG_KULIAH_G10_L1']

    def get_zone_name(self, ip_str):
        """Mencari nama zona berdasarkan IP Address"""
        ip = ipaddress.ip_address(ip_str)
        for name, network in self.subnets.items():
            if ip in network:
                return name
        return "UNKNOWN_ZONE"

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def _check_acl(self, src_ip, dst_ip, tcp_pkt=None):
        """
        Return (Allowed: Bool, Reason: String)
        """
        src_zone = self.get_zone_name(src_ip)
        dst_zone = self.get_zone_name(dst_ip)
        
        # --- LOGIKA TCP REPLY (Dosen akses Mahasiswa, Mahasiswa reply OK) ---
        # Jika paket adalah TCP ACK (Balasan), biasanya kita izinkan (Stateful simple)
        is_tcp_reply = False
        if tcp_pkt and (tcp_pkt.bits & tcp.TCP_ACK):
            is_tcp_reply = True

        # --- RULE 1: PROTEKSI PIMPINAN & ADMIN (Sangat Ketat) ---
        if dst_zone in self.SENSITIVE_ZONES:
            # Hanya sesama sensitive zone yang boleh akses
            if src_zone not in self.SENSITIVE_ZONES:
                return False, f"BLOCK: {src_zone} mencoba akses Zona Sensitif {dst_zone}"

        # --- RULE 2: PROTEKSI UJIAN ---
        if dst_zone == 'UJIAN_G9_L2':
            # Mahasiswa DILARANG KERAS masuk ke server Ujian
            if src_zone in self.STUDENT_ZONES:
                return False, f"BLOCK: Mahasiswa ({src_zone}) dilarang akses Server Ujian"

        # --- RULE 3: MAHASISWA ke DOSEN ---
        # Mahasiswa gabisa initiate ke Dosen, tapi bisa reply
        if src_zone in self.STUDENT_ZONES and dst_zone in self.DOSEN_ZONES:
            if is_tcp_reply:
                return True, f"ALLOW (REPLY): Mahasiswa menjawab request Dosen"
            else:
                return False, f"BLOCK: Mahasiswa mencoba initiate koneksi ke Dosen"

        # --- RULE 4: DOSEN ke MAHASISWA ---
        if src_zone in self.DOSEN_ZONES and dst_zone in self.STUDENT_ZONES:
            return True, f"ALLOW: Dosen mengakses Mahasiswa"

        # --- RULE 5: DEFAULT ALLOW (Sesama Gedung / Zona Aman) ---
        return True, f"ALLOW: Traffic Normal {src_zone} -> {dst_zone}"

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        # Skip LLDP & IPv6
        if eth.ethertype == ether_types.ETH_TYPE_LLDP: return
        if eth.ethertype == ether_types.ETH_TYPE_IPV6: return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # --- HANDLE ARP (PENTING AGAR PING JALAN) ---
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            # ARP selalu di allow untuk discovery MAC Address
            pass

        # --- HANDLE IPV4 & FIREWALL ---
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Cek Logic Firewall
            allowed, reason = self._check_acl(src_ip, dst_ip, tcp_pkt)

            if not allowed:
                # LOGGING SAAT BLOCK
                self.logger.warning(f" [X] {reason} | Src: {src_ip} -> Dst: {dst_ip}")
                return  # <--- PENTING: Return di sini agar paket di-DROP (tidak diteruskan)
            
            # LOGGING SAAT ALLOW (Opsional, matikan jika terlalu berisik)
            # Hanya log paket inisiasi (SYN) atau paket pertama UDP agar tidak spam
            if (tcp_pkt and tcp_pkt.bits & tcp.TCP_SYN) or not tcp_pkt:
                 self.logger.info(f" [V] {reason}")

        # --- FORWARDING LOGIC ---
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)