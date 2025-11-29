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

        # IP Ranges for each zone (subnet-based)
        self.zones = {
            # Mahasiswa: WiFi networks
            'MAHASISWA': {
                'networks': [
                    {'base': '192.168.1.0', 'mask': 22,   'start': '192.168.1.1', 'end': '192.168.4.254'},   # G9 Lt1
                    {'base': '192.168.5.0', 'mask': 24,   'start': '192.168.5.1', 'end': '192.168.5.254'},    # G9 Lt2
                    {'base': '192.168.6.0', 'mask': 22,   'start': '192.168.6.1', 'end': '192.168.9.254'},    # G9 Lt3
                    {'base': '192.168.20.0', 'mask': 26,  'start': '192.168.20.1', 'end': '192.168.20.62'},   # G10 Lt1
                    {'base': '192.168.20.64', 'mask': 25,  'start': '192.168.20.65', 'end': '192.168.20.126'}, # G10 Lt2
                    {'base': '192.168.20.192', 'mask': 26, 'start': '192.168.20.193', 'end': '192.168.20.254'} # G10 Lt3
                ]
            },

            # Lab Komputer: treated as Mahasiswa
            'LAB': {
                'networks': [
                    {'base': '192.168.10.96', 'mask': 25, 'start': '192.168.10.97', 'end': '192.168.10.126'}  # Lab network
                ]
            },

            # Secure: Keuangan, Admin, Pimpinan, Ujian
            'SECURE': {
                'networks': [
                    {'base': '192.168.10.32', 'mask': 26, 'start': '192.168.10.33', 'end': '192.168.10.62'},   # Keuangan/Dekan/Ujian
                    {'base': '192.168.21.0', 'mask': 28, 'start': '192.168.21.1', 'end': '192.168.21.14'}    # Admin
                ]
            },

            # Dosen: All cable networks for lecturers
            'DOSEN': {
                'networks': [
                    {'base': '192.168.10.32', 'mask': 26, 'start': '192.168.10.37', 'end': '192.168.10.38'},   # G9 Dosen
                    {'base': '192.168.21.16', 'mask': 29, 'start': '192.168.21.17', 'end': '192.168.21.22'},  # G10 Lt2 Dosen
                    {'base': '192.168.21.32', 'mask': 26, 'start': '192.168.21.33', 'end': '192.168.21.62'}   # G10 Lt3 Dosen
                ]
            },

            # Special sub-groups
            'KEUANGAN': {
                'networks': [
                    {'base': '192.168.10.32', 'mask': 26, 'start': '192.168.10.33', 'end': '192.168.10.34'}
                ]
            },
            'DEKAN': {
                'networks': [
                    {'base': '192.168.10.32', 'mask': 26, 'start': '192.168.10.35', 'end': '192.168.10.36'}
                ]
            },
            'UJIAN': {
                'networks': [
                    {'base': '192.168.10.32', 'mask': 26, 'start': '192.168.10.39', 'end': '192.168.10.40'}
                ]
            }
        }

    def ip_to_int(self, ip):
        try:
            parts = ip.split('.')
            return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
        except:
            return 0

    def ip_in_network(self, ip, network_info):
        ip_int = self.ip_to_int(ip)
        network_base = self.ip_to_int(network_info['start'])
        network_end = self.ip_to_int(network_info['end'])
        return network_base <= ip_int <= network_end

    def get_zone_category(self, ip_addr):
        # Check if IP is in specific sub-group first
        for zone_name in ['KEUANGAN', 'DEKAN', 'UJIAN']:
            if zone_name in self.zones:
                for network in self.zones[zone_name]['networks']:
                    if self.ip_in_network(ip_addr, network):
                        return zone_name

        # Check main zones
        for zone_name in ['MAHASISWA', 'LAB', 'SECURE', 'DOSEN']:
            if zone_name in self.zones:
                for network in self.zones[zone_name]['networks']:
                    if self.ip_in_network(ip_addr, network):
                        # Lab is treated as Mahasiswa
                        return 'MAHASISWA' if zone_name == 'LAB' else zone_name

        return 'UNKNOWN'

    def get_building(self, ip_addr):
        try:
            octets = ip_addr.split('.')
            if octets[0] == '192' and octets[1] == '168':
                if octets[2] in ['1', '5', '6', '10']:
                    return 'G9'
                elif octets[2] in ['20', '21']:
                    return 'G10'
        except:
            pass
        return 'UNKNOWN'

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

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)
        src_building = self.get_building(src_ip)
        dst_building = self.get_building(dst_ip)

        self.logger.info(f"Traffic: {src_ip}({src_cat},{src_building}) -> {dst_ip}({dst_cat},{dst_building})")

        # RULE 1: Keuangan ke Dekan -> ALLOW
        if src_cat == 'KEUANGAN' and dst_cat == 'DEKAN':
            return True, "ALLOW: Internal Report (Keuangan -> Dekan)", True

        # RULE 1a: Dekan bisa akses semua zona -> ALLOW
        if src_cat == 'DEKAN':
            return True, "ALLOW: Dekan mengakses jaringan", True

        # RULE 2: Mahasiswa/Lab -> Secure -> BLOCK
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, f"BLOCK: Mahasiswa mengakses zona aman", False

        # RULE 3: Mahasiswa/Lab -> Dosen -> BLOCK
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, f"BLOCK: Mahasiswa mengakses dosen", False

        # RULE 4: Dosen -> Ujian -> BLOCK
        if src_cat == 'DOSEN' and dst_cat == 'UJIAN':
            return False, "BLOCK: Dosen mengakses server ujian", False

        # RULE 5: Dosen -> Secure -> BLOCK
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Dosen mengakses zona aman", False

        # RULE 6: Komunikasi antar lantai di gedung yang sama
        if src_building == dst_building and src_building != 'UNKNOWN':
            if src_cat == 'MAHASISWA' and dst_cat in ['SECURE', 'DOSEN']:
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    return True, "ALLOW: Ping Reply (Return Traffic)", False
                return False, f"BLOCK: Mahasiswa lantai lain akses {dst_cat}", False
            elif src_cat in ['MAHASISWA', 'SECURE', 'DOSEN'] and dst_cat in ['MAHASISWA', 'SECURE', 'DOSEN']:
                # Allow communication between same category in same building
                if src_cat == dst_cat or (src_cat == 'MAHASISWA' and dst_cat == 'MAHASISWA'):
                    return True, f"ALLOW: Komunikasi antar lantai di {src_building}", True

        # RULE 7: Komunikasi antar gedung -> BLOCK Mahasiswa, allow yang lain
        if src_building != dst_building and src_building != 'UNKNOWN' and dst_building != 'UNKNOWN':
            if src_cat == 'MAHASISWA':
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    return True, "ALLOW: Ping Reply (Return Traffic)", False
                return False, f"BLOCK: Mahasiswa akses antar gedung", False
            elif src_cat in ['DOSEN', 'SECURE']:
                return True, f"ALLOW: {src_cat} akses antar gedung", True

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

        should_install_flow = True

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst

            icmp_type = None
            if ipv4_pkt.proto == 1:  # ICMP
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