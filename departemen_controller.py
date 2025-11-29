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

        # Semua zona berdasarkan rentang IP
        self.zones = {
            'MAHASISWA': [
                {'start': '192.168.1.1', 'end': '192.168.4.254'},
                {'start': '192.168.5.1', 'end': '192.168.5.254'},
                {'start': '192.168.6.1', 'end': '192.168.9.254'},
                {'start': '192.168.20.1', 'end': '192.168.20.62'},
                {'start': '192.168.20.65', 'end': '192.168.20.190'},
                {'start': '192.168.20.193', 'end': '192.168.20.254'},
            ],

            'LAB': [
                {'start': '192.168.10.97', 'end': '192.168.10.126'},
            ],

            'SECURE': [
                {'start': '192.168.10.33', 'end': '192.168.10.62'},
                {'start': '192.168.21.1', 'end': '192.168.21.14'},
            ],

            'DOSEN': [
                {'start': '192.168.10.37', 'end': '192.168.10.38'},
                {'start': '192.168.21.17', 'end': '192.168.21.22'},
                {'start': '192.168.21.33', 'end': '192.168.21.62'},
            ],

            'KEUANGAN': [{'start': '192.168.10.33', 'end': '192.168.10.34'}],
            'DEKAN': [{'start': '192.168.10.35', 'end': '192.168.10.36'}],
            'UJIAN': [{'start': '192.168.10.39', 'end': '192.168.10.40'}],
        }

    # ============================================================
    # Helper umum
    # ============================================================

    def ip_to_int(self, ip):
        try:
            p = ip.split('.')
            return (int(p[0]) << 24) + (int(p[1]) << 16) + (int(p[2]) << 8) + int(p[3])
        except:
            return 0

    def ip_in_range(self, ip, range_info):
        ip_i = self.ip_to_int(ip)
        s = self.ip_to_int(range_info['start'])
        e = self.ip_to_int(range_info['end'])
        return s <= ip_i <= e

    def ip_in_zone(self, ip, zone_name):
        for r in self.zones[zone_name]:
            if self.ip_in_range(ip, r):
                return True
        return False

    # ============================================================
    # Menentukan kategori zona
    # ============================================================

    def get_zone_category(self, ip):
        for zone in ['KEUANGAN', 'DEKAN', 'UJIAN']:  # special group
            if self.ip_in_zone(ip, zone):
                return zone

        if self.ip_in_zone(ip, 'LAB'):
            return 'MAHASISWA'

        for zone in ['MAHASISWA', 'SECURE', 'DOSEN']:
            if self.ip_in_zone(ip, zone):
                return zone

        return 'UNKNOWN'

    # ============================================================
    # Gedung berdasarkan subnet
    # ============================================================

    def get_building(self, ip_addr):
        try:
            o = ip_addr.split('.')
            if o[0] == '192' and o[1] == '168':
                if o[2] in ['1', '5', '6', '10']:
                    return 'G9'
                if o[2] in ['20', '21']:
                    return 'G10'
        except:
            pass
        return 'UNKNOWN'

    # ============================================================
    # Firewall rules
    # ============================================================

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # RULE 1: Keuangan → Dekan (ALLOW)
        if self.ip_in_zone(src_ip, 'KEUANGAN') and self.ip_in_zone(dst_ip, 'DEKAN'):
            return True, "[SECURITY] Allowed: Finance → Dean (Internal Access)", True

        # RULE 1A: Dekan bisa akses apapun
        if self.ip_in_zone(src_ip, 'DEKAN'):
            return True, "[SECURITY] Allowed: Dean authorized across network", True

        # RULE 2: Mahasiswa → Secure (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "[SECURITY] Allowed: ICMP reply to student", False
            return False, "[SECURITY] Blocked: Student → Secure zone", False

        # RULE 3: Mahasiswa → Dosen (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "[SECURITY] Allowed: ICMP reply to student", False
            return False, "[SECURITY] Blocked: Student → Lecturer zone", False

        # RULE 4: Dosen → Ujian (BLOCK)
        if src_cat == 'DOSEN' and self.ip_in_zone(dst_ip, 'UJIAN'):
            return False, "[SECURITY] Blocked: Lecturer → Exam Server", False

        # RULE 5: Dosen → Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "[SECURITY] Allowed: ICMP reply to Lecturer", False
            return False, "[SECURITY] Blocked: Lecturer → Secure zone", False

        # RULE 6: Antar lantai gedung yang sama
        src_b = self.get_building(src_ip)
        dst_b = self.get_building(dst_ip)

        if src_b == dst_b and src_b != 'UNKNOWN':
            if src_cat == 'MAHASISWA' and dst_cat in ['SECURE', 'DOSEN']:
                return False, f"[SECURITY] Blocked: Student cross-floor → {dst_cat}", False
            return True, f"[ACCESS] Allowed: Same building communication ({src_b})", True

        # RULE 7: Antar gedung (G9 ↔ G10)
        if src_b != dst_b and src_b != 'UNKNOWN' and dst_b != 'UNKNOWN':
            if src_cat in ['DOSEN', 'SECURE']:
                return True, f"[ACCESS] Allowed: {src_cat} inter-building access", True
            if src_cat == 'MAHASISWA':
                return False, "[SECURITY] Blocked: Student inter-building access", False

        # DEFAULT ALLOW
        return True, "[ACCESS] Allowed: General Access", True

    # ============================================================
    # INSTALL DEFAULT FLOW
    # ============================================================

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_CONTROLLER,
                                          datapath.ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, parser.OFPMatch(), actions)
        self.logger.info("[FLOW] Installed default controller flow")

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            buffer_id=buffer_id if buffer_id else ofproto.OFP_NO_BUFFER,
            priority=priority,
            match=match,
            instructions=inst
        )

        datapath.send_msg(mod)

    # ============================================================
    # PACKET IN HANDLER
    # ============================================================

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # ignore LLDP

        src = eth.src
        dst = eth.dst
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        should_install_flow = True

        # FIREWALL: jika IP packet → cek rules
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            icmp_type = None
            if ip_pkt.proto == 1:
                icmp_p = pkt.get_protocol(icmp.icmp)
                if icmp_p:
                    icmp_type = icmp_p.type

            allowed, reason, should_install_flow = self.check_security(src_ip, dst_ip, icmp_type)

            if not allowed:
                self.logger.warning(f"{reason} | {src_ip} → {dst_ip}")
                return
            else:
                self.logger.info(f"{reason} | {src_ip} → {dst_ip}")

        # SWITCHING LOGIC
        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)

            if should_install_flow:
                self.add_flow(datapath, 1, match, actions)
            else:
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=msg.buffer_id,
                    in_port=in_port,
                    actions=actions,
                    data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None,
                )
                datapath.send_msg(out)
                return

        # Flooding
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        )
        datapath.send_msg(out)
