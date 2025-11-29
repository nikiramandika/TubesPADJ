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
            # Mahasiswa: Gedung G9 Nirkabel (Lt1, Lt2, Lt3) - sesuai topology
            'MAHASISWA': [
                # G9 Lt1 Nirkabel: 192.168.1.10, 192.168.1.11
                '192.168.1.10', '192.168.1.11',
                # G9 Lt3 Nirkabel: 192.168.6.10, 192.168.6.11
                '192.168.6.10', '192.168.6.11'
            ],

            # Lab Komputer: Diperlakukan sama seperti Mahasiswa (Student Network) - sesuai topology
            'LAB': [
                # Lab 1: 192.168.1.50, 192.168.1.51
                '192.168.1.50', '192.168.1.51',
                # Lab 2: 192.168.2.50, 192.168.2.51
                '192.168.2.50', '192.168.2.51',
                # Lab 3: 192.168.3.50, 192.168.3.51
                '192.168.3.50', '192.168.3.51'
            ],

            # Secure: Keuangan, Admin, Pimpinan, Ujian - sesuai topology
            'SECURE': [
                # Keuangan: Gedung G9 Kabel Lt1
                '192.168.10.11', '192.168.10.12',
                # Pimpinan: Gedung G9 Kabel Lt2
                '192.168.10.33', '192.168.10.34',
                # Ujian: Gedung G9 Kabel Lt3
                '192.168.10.97', '192.168.10.98'
            ],

            # Dosen: Gedung G9 Kabel + Gedung G10 Nirkabel dan Kabel - sesuai topology
            'DOSEN': [
                # G9 Lt2 Kabel (Dosen Gedung G9)
                '192.168.10.35', '192.168.10.36',
                # G10 Lt2 Nirkabel (Dosen)
                '172.16.20.71', '172.16.20.72',
                # G10 Lt3 Nirkabel (Dosen)
                '172.16.20.201', '172.16.20.202'
            ],

            # Administrasi Gedung G10 - sesuai topology
            'ADMIN_G10': [
                # G10 Lt1 Kabel (Administrasi)
                '172.16.21.11', '172.16.21.12'
            ],

            # Aula - sesuai topology
            'AULA': [
                # G10 Lt2 Kabel (Aula)
                '172.16.21.18', '172.16.21.19'
            ],

            # Sub-group khusus untuk rule spesifik
            'KEUANGAN':  ['192.168.10.11', '192.168.10.12'],
            'DEKAN':     ['192.168.10.33', '192.168.10.34'],
            'UJIAN':     ['192.168.10.97', '192.168.10.98']
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
        if ip_addr in self.zones['ADMIN_G10']: return 'ADMIN_G10'
        if ip_addr in self.zones['AULA']:      return 'AULA'
        return 'UNKNOWN'

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # RULE 1: Keuangan ke Dekan -> ALLOW (Izin Khusus Internal Secure)
        if src_ip in self.zones['KEUANGAN'] and dst_ip in self.zones['DEKAN']:
             return True, "ALLOW: Internal Report (Keuangan -> Dekan)", True

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

        # RULE 4: Mahasiswa/Lab -> Admin G10 (ALLOW)
        if src_cat == 'MAHASISWA' and dst_cat == 'ADMIN_G10':
            return True, "ALLOW: Mahasiswa akses Administrasi G10", True

        # RULE 5: Mahasiswa/Lab -> Aula (ALLOW)
        if src_cat == 'MAHASISWA' and dst_cat == 'AULA':
            return True, "ALLOW: Mahasiswa akses Aula", True

        # RULE 6: Dosen -> Ujian (BLOCK)
        if src_cat == 'DOSEN' and dst_ip in self.zones['UJIAN']:
            return False, "BLOCK: Dosen akses Server Ujian", False

        # RULE 7: Dosen -> Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Dosen akses Zona Aman", False

        # RULE 8: Admin G10 -> Secure (ALLOW for administrative access)
        if src_cat == 'ADMIN_G10' and dst_cat == 'SECURE':
            return True, "ALLOW: Admin G10 akses Zona Aman (Administrative)", True

        # RULE 9: Aula -> Secure (BLOCK)
        if src_cat == 'AULA' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False

            return False, "BLOCK: Aula mencoba akses Zona Aman", False

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