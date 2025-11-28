from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, udp, icmp
from ryu.lib.packet import ether_types
import ipaddress

class DeptController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

        # =================================================================
        # DEFINISI KELOMPOK SUBNET (Berdasarkan Topologi Mininet Anda)
        # =================================================================
        
        # 1. Kelompok Mahasiswa & Public (G9 Floor 1, Labs, APs, G10 Floor 1)
        self.STUDENT_SUBNETS = [
            ipaddress.ip_network('192.168.10.0/27'),    # G9 Floor 1
            ipaddress.ip_network('192.168.10.128/27'),  # G9 Floor 2 Sw4 (Ujian)
            ipaddress.ip_network('192.168.10.160/27'),  # G9 Lab 1
            ipaddress.ip_network('192.168.10.192/27'),  # G9 Lab 2
            ipaddress.ip_network('192.168.10.224/27'),  # G9 Lab 3
            ipaddress.ip_network('192.168.10.240/28'),  # G9 AP
            ipaddress.ip_network('172.16.21.0/28')      # G10 Floor 1
        ]

        # 2. Kelompok Dosen (G9 Floor 2 Sw1, G10 Floor 2 & 3)
        self.DOSEN_SUBNETS = [
            ipaddress.ip_network('192.168.10.32/27'),   # G9 Floor 2 Sw1
            ipaddress.ip_network('172.16.21.16/28'),    # G10 Floor 2
            ipaddress.ip_network('172.16.21.32/27')     # G10 Floor 3
        ]

        # 3. Kelompok Admin & Keuangan (G9 Floor 2 Sw2)
        self.ADMIN_SUBNETS = [
            ipaddress.ip_network('192.168.10.64/27')
        ]

        # 4. Kelompok Pimpinan (G9 Floor 2 Sw3)
        self.PIMPINAN_SUBNETS = [
            ipaddress.ip_network('192.168.10.96/27')
        ]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry (default: send to controller)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def _check_acl(self, ipv4_pkt, tcp_pkt=None):
        """
        Return True jika paket DIIZINKAN.
        Return False jika paket DIBLOKIR.
        """
        src_ip = ipaddress.ip_address(ipv4_pkt.src)
        dst_ip = ipaddress.ip_address(ipv4_pkt.dst)

        # Helper functions to check membership
        def is_student(ip):
            return any(ip in net for net in self.STUDENT_SUBNETS)
        
        def is_dosen(ip):
            return any(ip in net for net in self.DOSEN_SUBNETS)
        
        def is_admin(ip):
            return any(ip in net for net in self.ADMIN_SUBNETS)
        
        def is_pimpinan(ip):
            return any(ip in net for net in self.PIMPINAN_SUBNETS)

        # ================= RULES =================

        # RULE 1: Mahasiswa BLOCKED to Dosen, Admin, Pimpinan
        # Exception: Jika paket adalah TCP ACK (Balasan), izinkan (Stateful simulation)
        if is_student(src_ip):
            target_is_restricted = is_dosen(dst_ip) or is_admin(dst_ip) or is_pimpinan(dst_ip)
            
            if target_is_restricted:
                # Cek apakah ini trafik balasan (Established)
                if tcp_pkt and (tcp_pkt.bits & tcp.TCP_ACK):
                    return True # Allow reply
                
                print(f"*** BLOCK: Mahasiswa ({src_ip}) mencoba akses Restricted ({dst_ip})")
                return False

        # RULE 2: Dosen BLOCKED to Admin, Pimpinan
        if is_dosen(src_ip):
            if is_admin(dst_ip) or is_pimpinan(dst_ip):
                print(f"*** BLOCK: Dosen ({src_ip}) mencoba akses Mgmt ({dst_ip})")
                return False

        # Default Allow (Dosen ke Mahasiswa, Antar Gedung lain, dll)
        return True

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        # Abaikan paket LLDP/IPV6 untuk simplifikasi
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Pelajari MAC address (Learning Switch)
        self.mac_to_port[dpid][src] = in_port

        # --- ACL CHECKING ---
        # Kita hanya mencek paket IPv4
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = pkt.get_protocol(tcp.tcp) # Ambil header TCP jika ada

        if ip_pkt:
            # Jalankan logika firewall
            allowed = self._check_acl(ip_pkt, tcp_pkt)
            if not allowed:
                # Jika diblokir, kita return (drop packet) tanpa meneruskan
                return

        # --- FORWARDING LOGIC ---
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install Flow (Agar paket selanjutnya langsung lewat switch tanpa ke controller)
        # HATI-HATI: Jika kita install flow permanen, logika ACL di atas mungkin ter-bypass
        # untuk paket selanjutnya.
        # Untuk keamanan maksimal (tapi performa turun), jangan install flow (packet-by-packet).
        # Atau, install flow dengan match spesifik IP Src/Dst.
        
        # Di sini saya akan meneruskan packet_out saja agar Logic ACL selalu dicek tiap paket
        # (Mode Secure tapi agak lambat). 
        # Jika ingin cepat, uncomment bagian add_flow di bawah, tapi flow static tidak mengecek logic python.
        
        # if out_port != ofproto.OFPP_FLOOD:
        #     match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
        #     self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)