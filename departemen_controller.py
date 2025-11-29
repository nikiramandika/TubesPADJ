from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, icmp

class MedicalSimpleController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MedicalSimpleController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
                
        self.zones = {
            # Mahasiswa: Semua IP Nirkabel dari Gedung G9 dan G10
            'MAHASISWA': [
                # G9 Lantai 1 Nirkabel: 192.168.1.0/22
                '192.168.1.1', '192.168.1.2',
                # G9 Lantai 2 Nirkabel: 192.168.5.0/24
                '192.168.5.1', '192.168.5.2',
                # G9 Lantai 3 Nirkabel: 192.168.6.0/22
                '192.168.6.1', '192.168.6.2',
                # G10 Lantai 1 Nirkabel: 192.168.20.0/26
                '192.168.20.1', '192.168.20.2',
                # G10 Lantai 2 Nirkabel: 192.168.20.64/25
                '192.168.20.65', '192.168.20.66',
                # G10 Lantai 3 Nirkabel: 192.168.20.192/26
                '192.168.20.193', '192.168.20.194'
            ],

            # Lab Komputer: Diperlakukan sama seperti Mahasiswa (Student Network)
            'LAB': [
                # G9 Lantai 3 Kabel: 192.168.10.96/25
                '192.168.10.97', '192.168.10.98', # Lab 1
                '192.168.10.99', '192.168.10.100', # Lab 2
                '192.168.10.101', '192.168.10.102'  # Lab 3
            ],

            # Secure: Keuangan, Admin, Pimpinan, Ujian
            'SECURE': [
                # G9 Lantai 2 Kabel: 192.168.10.32/26 (Keuangan)
                '192.168.10.33', '192.168.10.34',
                # G10 Lantai 1 Kabel: 192.168.21.0/28 (Admin)
                '192.168.21.1', '192.168.21.2',
                # G9 Lantai 2 Kabel: 192.168.10.32/26 (Pimpinan)
                '192.168.10.35', '192.168.10.36',
                # G9 Lantai 2 Kabel: 192.168.10.32/26 (Ujian)
                '192.168.10.39', '192.168.10.40'
            ],

            # Dosen: Semua IP Kabel Dosen dari Gedung G9 dan G10
            'DOSEN': [
                # G9 Lantai 2 Kabel: 192.168.10.32/26
                '192.168.10.37', '192.168.10.38',
                # G10 Lantai 2 Kabel: 192.168.21.16/29
                '192.168.21.17', '192.168.21.18',
                # G10 Lantai 3 Kabel: 192.168.21.32/26
                '192.168.21.33', '192.168.21.34'
            ],

            # Sub-group khusus untuk rule spesifik
            'KEUANGAN':  [
                # G9 Lantai 2 Kabel: 192.168.10.32/26
                '192.168.10.33', '192.168.10.34'
            ],
            'DEKAN':     [
                # G9 Lantai 2 Kabel: 192.168.10.32/26
                '192.168.10.35', '192.168.10.36'
            ],
            'UJIAN':     [
                # G9 Lantai 2 Kabel: 192.168.10.32/26
                '192.168.10.39', '192.168.10.40'
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
        # Cek IP masuk kategori mana
        if ip_addr in self.zones['MAHASISWA']: return 'MAHASISWA'
        if ip_addr in self.zones['LAB']:       return 'MAHASISWA'
        if ip_addr in self.zones['SECURE']:    return 'SECURE'
        if ip_addr in self.zones['DOSEN']:     return 'DOSEN'
        return 'UNKNOWN'

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # RULE 1: Keuangan ke Dekan -> ALLOW (Izin Khusus Internal Secure)
        if src_ip in self.zones['KEUANGAN'] and dst_ip in self.zones['DEKAN']:
             return True, "ALLOW: Internal Report (Keuangan -> Dekan)", True

        # RULE 1a: Dekan bisa mengakses semua zona (Mahasiswa, Lab, Dosen) -> ALLOW
        if src_ip in self.zones['DEKAN']:
            return True, "ALLOW: Dekan mengakses jaringan", True

        # RULE 2: Mahasiswa/Lab -> Secure (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Mahasiswa/Lab mencoba akses Zona Aman", False

        # RULE 3: Mahasiswa/Lab -> Dosen (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Mahasiswa/Lab mencoba akses Dosen Pribadi", False

        # RULE 4: Dosen -> Ujian (BLOCK)
        if src_cat == 'DOSEN' and dst_ip in self.zones['UJIAN']:
            return False, "BLOCK: Dosen akses Server Ujian", False

        # RULE 5: Dosen -> Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Dosen akses Zona Aman", False

        # RULE 6: Antar lantai yang sama di gedung yang sama - PERIKSA OKTET KE-3
        # Gedung G9: 192.168.1.*, 192.168.5.*, 192.168.6.*, 192.168.10.*
        # Gedung G10: 192.168.20.*, 192.168.21.*
        def get_building(ip_addr):
            try:
                octets = ip_addr.split('.')
                if octets[0] == '192' and octets[1] == '168':
                    if octets[2] in ['1', '5', '6', '10']:
                        return 'G9'
                elif octets[0] == '172' and octets[1] == '16':
                    if octets[2] in ['20', '21']:
                        return 'G10'
            except:
                pass
            return 'UNKNOWN'

        src_building = get_building(src_ip)
        dst_building = get_building(dst_ip)

        # RULE 6a: Antar lantai di gedung yang sama - ALLOW untuk semua kategori kecuali mahasiswa ke secure/dosen
        if src_building == dst_building and src_building != 'UNKNOWN':
            if src_cat == 'MAHASISWA' and dst_cat in ['SECURE', 'DOSEN']:
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    return True, "ALLOW: Ping Reply (Return Traffic)", False
                return False, f"BLOCK: Mahasiswa lantai lain akses {dst_cat} di {src_building}", False
            else:
                return True, f"ALLOW: Komunikasi antar lantai di {src_building}", True

        # RULE 7: Antar gedung (G9 <-> G10) - ALLOW untuk Dosen dan Secure, BLOCK untuk Mahasiswa
        if src_building != dst_building and src_building != 'UNKNOWN' and dst_building != 'UNKNOWN':
            if src_cat in ['DOSEN', 'SECURE']:
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