from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, icmp

class GedungController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(GedungController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
                
        self.zones = {
            # Mahasiswa: Semua IP Nirkabel (subnet ranges)
            'MAHASISWA': [
                # G9 WiFi ranges
                {'network': '192.168.1.0', 'mask': 16,   # 192.168.1.0/16 (192.168.1.1 - 192.168.4.254)
                 'start': '192.168.1.1', 'end': '192.168.4.254'},
                {'network': '192.168.5.0', 'mask': 16,   # 192.168.5.0/16
                 'start': '192.168.5.1', 'end': '192.168.5.254'},
                {'network': '192.168.6.0', 'mask': 16,   # 192.168.6.0/16 (192.168.6.1 - 192.168.9.254)
                 'start': '192.168.6.1', 'end': '192.168.9.254'},
                # G10 WiFi ranges
                {'network': '192.168.20.0', 'mask': 16,  # 192.168.20.0/16
                 'start': '192.168.20.1', 'end': '192.168.20.62'},
                {'network': '192.168.20.64', 'mask': 16, # 192.168.20.64/16
                 'start': '192.168.20.65', 'end': '192.168.20.190'},
                {'network': '192.168.20.192', 'mask': 16, # 192.168.20.192/16
                 'start': '192.168.20.193', 'end': '192.168.20.254'}
            ],

            # Lab Komputer: Student Network (subnet ranges)
            'LAB': [
                {'network': '192.168.10.96', 'mask': 16, # 192.168.10.96/16
                 'start': '192.168.10.97', 'end': '192.168.10.126'},
            ],

            # Secure: Admin, Pimpinan, Keuangan (subnet ranges) - Ujian dipisah
            'SECURE': [
                # G9 Secure ranges
                {'network': '192.168.10.32', 'mask': 16, # Admin/Keuangan 192.168.10.32/16
                 'start': '192.168.10.33', 'end': '192.168.10.38'},
                # G10 Secure ranges
                {'network': '192.168.21.0', 'mask': 16,   # Administrasi 192.168.21.0/16
                 'start': '192.168.21.1', 'end': '192.168.21.14'},
            ],

            # Ujian: Dipisah dari Secure zone
            'UJIAN': [
                # G9 Ujian ranges - terpisah dari secure
                {'network': '192.168.10.32', 'mask': 16, # Ujian 192.168.10.32/16
                 'start': '192.168.10.39', 'end': '192.168.10.40'}
            ],

            # Dosen: Semua IP Kabel Dosen (subnet ranges)
            'DOSEN': [
                # G9 Dosen
                {'network': '192.168.10.32', 'mask': 16, # 192.168.10.32/16 (bagian dosen)
                 'start': '192.168.10.37', 'end': '192.168.10.38'},
                # G10 Dosen ranges
                {'network': '192.168.21.16', 'mask': 16,  # 192.168.21.16/16
                 'start': '192.168.21.17', 'end': '192.168.21.22'},
                {'network': '192.168.21.32', 'mask': 16,  # 192.168.21.32/16
                 'start': '192.168.21.33', 'end': '192.168.21.62'},
            ],

            # Sub-group khusus untuk rule spesifik - KEUANGAN dan UJIAN sudah dipindah ke atas
            'DEKAN': [
                {'network': '192.168.10.32', 'mask': 16,
                 'start': '192.168.10.35', 'end': '192.168.10.36'}
            ]
        }

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    def get_zone_category(self, ip_addr):
        # Helper function untuk convert IP to integer
        def ip_to_int(ip):
            try:
                parts = ip.split('.')
                return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
            except:
                return 0

        # Helper function untuk cek IP dalam range
        def ip_in_range(ip_addr, range_info):
            if 'start' in range_info and 'end' in range_info:
                ip_int = ip_to_int(ip_addr)
                start_int = ip_to_int(range_info['start'])
                end_int = ip_to_int(range_info['end'])
                return start_int <= ip_int <= end_int
            return False

        def ip_in_zone(ip_addr, zone_name):
            for range_info in self.zones[zone_name]:
                if ip_in_range(ip_addr, range_info):
                    return True
            return False

        # Cek IP masuk kategori mana dengan subnet ranges
        for zone_name, zone_ranges in self.zones.items():
            if zone_name in ['DEKAN']:
                continue
            if zone_name == 'LAB':
                # Lab diperlakukan sebagai Mahasiswa
                for range_info in zone_ranges:
                    if ip_in_range(ip_addr, range_info):
                        return 'MAHASISWA'
            else:
                for range_info in zone_ranges:
                    if ip_in_range(ip_addr, range_info):
                        return zone_name

        return 'UNKNOWN'

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # Helper functions
        def ip_to_int(ip):
            try:
                parts = ip.split('.')
                return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
            except:
                return 0

        def ip_in_range(ip_addr, range_info):
            if 'start' in range_info and 'end' in range_info:
                ip_int = ip_to_int(ip_addr)
                start_int = ip_to_int(range_info['start'])
                end_int = ip_to_int(range_info['end'])
                return start_int <= ip_int <= end_int
            return False

        def ip_in_zone(ip_addr, zone_name):
            for range_info in self.zones[zone_name]:
                if ip_in_range(ip_addr, range_info):
                    return True
            return False

        # RULE 1: Keuangan (bagian dari SECURE) ke Dekan -> BLOCK (Keuangan tidak bisa akses Dekan)
        if src_cat == 'SECURE' and ip_in_zone(dst_ip, 'DEKAN'):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Mencoba akses Dekan", False

        # RULE 1a: Dekan bisa mengakses semua zona (Mahasiswa, Lab, Dosen, Keuangan) -> ALLOW
        if ip_in_zone(src_ip, 'DEKAN'):
            return True, "ALLOW: Dekan mengakses jaringan", True

        # RULE 2: Mahasiswa/Lab -> Ujian (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'UJIAN':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Mahasiswa/Lab mencoba akses Ujian", False

        # RULE 3: Mahasiswa/Lab -> Secure (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Mahasiswa/Lab mencoba akses Zona Aman", False

        # RULE 4: Mahasiswa/Lab -> Dosen (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Mahasiswa/Lab mencoba akses Dosen", False

        # RULE 6: Dosen -> Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Dosen mencoba akses Zona Aman", False
        
        
        def get_building(ip_addr):
            try:
                octets = ip_addr.split('.')
                if octets[0] == '192' and octets[1] == '168':
                    if octets[2] in ['1', '5', '6', '10']:
                        return 'G9'
                elif octets[0] == '192' and octets[1] == '168':
                    if octets[2] in ['20', '21']:
                        return 'G10'
            except:
                pass
            return 'UNKNOWN'

        src_building = get_building(src_ip)
        dst_building = get_building(dst_ip)

        # RULE 8a: Antar lantai di gedung yang sama - ALLOW untuk semua kategori kecuali mahasiswa ke secure/dosen/ujian
        if src_building == dst_building and src_building != 'UNKNOWN':
            if src_cat == 'MAHASISWA' and dst_cat in ['SECURE', 'DOSEN', 'UJIAN']:
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    return True, "ALLOW: Ping Reply (Return Traffic)", False
                return False, f"BLOCK: Mahasiswa lantai lain akses {dst_cat} di {src_building}", False
            else:
                return True, f"ALLOW: Komunikasi antar lantai di {src_building}", True

        # RULE 9: Antar gedung (G9 <-> G10) - ALLOW untuk Dosen, Secure, dan Ujian, BLOCK untuk Mahasiswa
        if src_building != dst_building and src_building != 'UNKNOWN' and dst_building != 'UNKNOWN':
            if src_cat in ['DOSEN', 'SECURE', 'UJIAN']:
                return True, f"ALLOW: {src_cat} akses antar gedung", True
            elif src_cat == 'MAHASISWA':
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    return True, "ALLOW: Ping Reply (Return Traffic)", False
                return False, "BLOCK: Mahasiswa akses antar gedung", False

        return True, "ALLOW: Akses Diizinkan", True

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP: return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # Variabel kontrol flow
        should_install_flow = True

        # --- LOGIKA FIREWALL ---
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst
            
            icmp_type = None
            if ipv4_pkt.proto == 1:
                icmp_p = pkt.get_protocol(icmp.icmp)
                if icmp_p:
                    icmp_type = icmp_p.type

            allowed, reason, should_install_flow = self.check_security(src_ip, dst_ip, icmp_type)
            
            if not allowed:
                self.logger.warning(f"{reason} | {src_ip} -> {dst_ip}")
                return 
            else:
                self.logger.info(f"{reason} | {src_ip} -> {dst_ip}")

        out_port = ofproto.OFPP_FLOOD
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=eth.ethertype)
            
            if should_install_flow:
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions)
            else:
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER: data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, 
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                return
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER: data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)