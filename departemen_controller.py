from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, icmp
import ipaddress

class MedicalSimpleController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MedicalSimpleController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        
        # Definisi zona dengan subnet CIDR (strict=False untuk mengizinkan host bits)
        self.zones = {
            # GEDUNG G9
            'MAHASISWA_G9_LT1_WIRELESS': ipaddress.ip_network('192.168.0.0/22', strict=False),
            'MAHASISWA_G9_LT1_KABEL': ipaddress.ip_network('192.168.10.0/27', strict=False),
            
            'ADMIN_SECURE_G9_LT2_WIRELESS': ipaddress.ip_network('192.168.5.0/24', strict=False),
            'ADMIN_SECURE_G9_LT2_KABEL': ipaddress.ip_network('192.168.10.32/26', strict=False),
            
            'LAB_G9_LT3_WIRELESS': ipaddress.ip_network('192.168.4.0/22', strict=False),
            'LAB_G9_LT3_KABEL': ipaddress.ip_network('192.168.10.96/25', strict=False),
            
            # GEDUNG G10
            'ADMIN_G10_LT1_WIRELESS': ipaddress.ip_network('172.16.20.0/26', strict=False),
            'ADMIN_G10_LT1_KABEL': ipaddress.ip_network('172.16.21.0/28', strict=False),
            
            'DOSEN_G10_LT2_WIRELESS': ipaddress.ip_network('172.16.20.64/25', strict=False),
            'DOSEN_G10_LT2_KABEL': ipaddress.ip_network('172.16.21.16/29', strict=False),
            
            'DOSEN_G10_LT3_WIRELESS': ipaddress.ip_network('172.16.20.192/26', strict=False),
            'DOSEN_G10_LT3_KABEL': ipaddress.ip_network('172.16.21.32/26', strict=False),
        }
        
        # Mapping IP ke kategori zona
        self.zone_mapping = {
            'MAHASISWA': ['MAHASISWA_G9_LT1_WIRELESS', 'MAHASISWA_G9_LT1_KABEL', 
                         'LAB_G9_LT3_WIRELESS', 'LAB_G9_LT3_KABEL'],
            'SECURE': ['ADMIN_SECURE_G9_LT2_WIRELESS', 'ADMIN_SECURE_G9_LT2_KABEL',
                      'ADMIN_G10_LT1_WIRELESS', 'ADMIN_G10_LT1_KABEL'],
            'DOSEN': ['DOSEN_G10_LT2_WIRELESS', 'DOSEN_G10_LT2_KABEL',
                     'DOSEN_G10_LT3_WIRELESS', 'DOSEN_G10_LT3_KABEL'],
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
        """Tentukan kategori zona dari IP address"""
        try:
            ip = ipaddress.ip_address(ip_addr)
            
            for zone_name, network in self.zones.items():
                if ip in network:
                    # Tentukan kategori utama
                    if 'MAHASISWA' in zone_name or 'LAB' in zone_name:
                        return 'MAHASISWA', zone_name
                    elif 'SECURE' in zone_name or 'ADMIN' in zone_name:
                        return 'SECURE', zone_name
                    elif 'DOSEN' in zone_name:
                        return 'DOSEN', zone_name
            
            return 'UNKNOWN', None
        except:
            return 'UNKNOWN', None

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        """Cek keamanan komunikasi antar zona"""
        src_cat, src_zone = self.get_zone_category(src_ip)
        dst_cat, dst_zone = self.get_zone_category(dst_ip)

        # RULE 1: Intra-zone communication - ALLOW (komunikasi dalam zone yang sama)
        if src_zone == dst_zone and src_cat != 'UNKNOWN':
            return True, f"ALLOW: Intra-zone communication ({src_cat})", True

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

        # RULE 4: Dosen -> Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Dosen akses Zona Aman", False

        # RULE 5: Secure -> Dosen (ALLOW - admin dapat akses semua)
        if src_cat == 'SECURE' and dst_cat == 'DOSEN':
            return True, "ALLOW: Admin/Secure akses Dosen", True

        # RULE 6: Secure -> Mahasiswa (ALLOW - admin dapat akses semua)
        if src_cat == 'SECURE' and dst_cat == 'MAHASISWA':
            return True, "ALLOW: Admin/Secure akses Mahasiswa", True

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
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        should_install_flow = True

        # LOGIKA FIREWALL
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
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, 
                                         in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                return
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, 
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)