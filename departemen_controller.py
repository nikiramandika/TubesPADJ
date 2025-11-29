from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, icmp
import time

class GedungController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(GedungController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # Track flows for logging purposes
        self.installed_flows = {}  # {(src_ip, dst_ip): timestamp}
        self.log_counter = {}      # {(src_ip, dst_ip): count}
        self.last_log_time = {}    # {(src_ip, dst_ip): timestamp}
                
        self.zones = {
            # Mahasiswa: Semua IP Nirkabel + Aula G10 (subnet ranges)
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
                 'start': '192.168.20.193', 'end': '192.168.20.254'},
                # G10 Aula ranges (sebelumnya dosen)
                {'network': '192.168.21.16', 'mask': 16,  # 192.168.21.16/16
                 'start': '192.168.21.17', 'end': '192.168.21.22'},
                {'network': '192.168.21.32', 'mask': 16,  # 192.168.21.32/16
                 'start': '192.168.21.33', 'end': '192.168.21.62'}
            ],

            # Lab Komputer: Student Network (subnet ranges)
            'LAB': [
                {'network': '192.168.10.96', 'mask': 16, # 192.168.10.96/16
                 'start': '192.168.10.97', 'end': '192.168.10.126'},
            ],

            # Secure: Administrasi(Keuangan), Admin, Pimpinan, Ujian (subnet ranges)
            'SECURE': [
                # G9 Secure ranges
                {'network': '192.168.10.32', 'mask': 16, # Keuangan/Ujian 192.168.10.32/16
                 'start': '192.168.10.33', 'end': '192.168.10.62'},
                # G10 Secure ranges
                {'network': '192.168.21.0', 'mask': 16,   # Administrasi 192.168.21.0/16
                 'start': '192.168.21.1', 'end': '192.168.21.14'},
            ],

            # Dosen: Semua IP Kabel Dosen (subnet ranges)
            'DOSEN': [
                # G9 Dosen
                {'network': '192.168.10.32', 'mask': 16, # 192.168.10.32/16 (bagian dosen)
                 'start': '192.168.10.37', 'end': '192.168.10.38'},
                # G10 Dosen ranges dipindahkan ke Mahasiswa (Aula G10)
            ],

            # Sub-group khusus untuk rule spesifik
            'KEUANGAN': [
                {'network': '192.168.10.32', 'mask': 16,
                 'start': '192.168.10.33', 'end': '192.168.10.34'}
            ],
            'DEKAN': [
                {'network': '192.168.10.32', 'mask': 16,
                 'start': '192.168.10.35', 'end': '192.168.10.36'}
            ],
            'UJIAN': [
                {'network': '192.168.10.32', 'mask': 16,
                 'start': '192.168.10.39', 'end': '192.168.10.40'}
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
            if zone_name in ['KEUANGAN', 'DEKAN', 'UJIAN']:
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

        def format_log_message(action, traffic_type, src_zone, dst_zone, context=""):
            """Format log message yang lebih deskriptif dan konsisten"""
            if context:
                return f"{action}: {traffic_type} ({src_zone} -> {dst_zone}) - {context}"
            else:
                return f"{action}: {traffic_type} ({src_zone} -> {dst_zone})"

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

        # RULE 1: Keuangan -> Dekan (ICMP reply) -> ALLOW
        if ip_in_zone(src_ip, 'KEUANGAN') and ip_in_zone(dst_ip, 'DEKAN'):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, format_log_message("ALLOW", "ICMP Echo Reply", "Keuangan", "Dekan"), False
            return True, format_log_message("ALLOW", "Internal Report", "Keuangan", "Dekan"), True

        # RULE 1a: Dekan bisa mengakses semua zona -> ALLOW
        if ip_in_zone(src_ip, 'DEKAN'):
            # Install flow untuk efisiensi, tapi tetap log untuk visibility
            return True, format_log_message("ALLOW", "Administrative Access", "Dekan", dst_cat), True

        # RULE 2: Secure -> Mahasiswa/Dosen (ICMP reply) -> ALLOW
        if src_cat == 'SECURE' and dst_cat in ['MAHASISWA', 'DOSEN']:
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                # ICMP reply dari Secure ke user zone
                return True, format_log_message("ALLOW", "ICMP Echo Reply", src_cat, dst_cat), False
            # Non-ICMP traffic tetap di-block
            return False, format_log_message("BLOCK", "Unauthorized Access", src_cat, dst_cat, "Security Zone"), False

        # RULE 3: Mahasiswa/Dosen -> Secure (BLOCK)
        if src_cat in ['MAHASISWA', 'DOSEN'] and dst_cat == 'SECURE':
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                # Ini tidak mungkin (reply tidak mungkin dari mahasiswa ke secure)
                return False, format_log_message("BLOCK", "Invalid ICMP Reply", src_cat, dst_cat), False
            return False, format_log_message("BLOCK", "Unauthorized Access", src_cat, dst_cat, "Security Zone"), False

        # RULE 4: Dosen -> Ujian (BLOCK)
        if src_cat == 'DOSEN' and ip_in_zone(dst_ip, 'UJIAN'):
            return False, format_log_message("BLOCK", "Unauthorized Access", src_cat, "Ujian", "Exam Server"), False

        # RULE 5: Dosen -> Secure (BLOCK)
        if src_cat == 'DOSEN' and dst_cat == 'SECURE':
            return False, format_log_message("BLOCK", "Unauthorized Access", src_cat, dst_cat, "Security Zone"), False

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

        # RULE 6: Antar lantai di gedung yang sama
        if src_building == dst_building and src_building != 'UNKNOWN':
            if src_cat in ['DOSEN', 'SECURE']:
                # Dosen dan Secure boleh akses antar lantai
                return True, format_log_message("ALLOW", "Inter-floor Communication", src_cat, dst_cat, src_building), True
            elif src_cat == 'MAHASISWA' and dst_cat in ['DOSEN', 'SECURE']:
                # Mahasiswa coba akses Dosen/Secure -> BLOCK (kecuali ICMP reply)
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    # ICMP reply dari Dosen/Secure ke Mahasiswa
                    return True, format_log_message("ALLOW", "ICMP Echo Reply", src_cat, dst_cat, f"inter-floor {src_building}"), False
                return False, format_log_message("BLOCK", "Inter-floor Access", src_cat, dst_cat, f"inter-floor {src_building}"), False
            else:
                # Default allow untuk lainnya
                return True, format_log_message("ALLOW", "Inter-floor Communication", src_cat, dst_cat, src_building), True

        # RULE 7: Antar gedung (G9 <-> G10)
        if src_building != dst_building and src_building != 'UNKNOWN' and dst_building != 'UNKNOWN':
            if src_cat in ['DOSEN', 'SECURE']:
                # Dosen dan Secure boleh akses antar gedung
                return True, format_log_message("ALLOW", "Inter-building Access", src_cat, dst_cat, f"{src_building}->{dst_building}"), True
            elif src_cat == 'MAHASISWA':
                # Mahasiswa coba akses antar gedung -> BLOCK (kecuali ICMP reply)
                if icmp_type == icmp.ICMP_ECHO_REPLY:
                    # ICMP reply dari target ke Mahasiswa
                    return True, format_log_message("ALLOW", "ICMP Echo Reply", src_cat, dst_cat, f"inter-building {src_building}->{dst_building}"), False
                return False, format_log_message("BLOCK", "Inter-building Access", src_cat, dst_cat, f"{src_building}->{dst_building}"), False

        return True, format_log_message("ALLOW", "Default Access", src_cat, dst_cat), True

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
            flow_key = (src_ip, dst_ip)
            current_time = time.time()

            if not allowed:
                self.logger.warning(f"{reason} | {src_ip} -> {dst_ip}")
                return
            else:
                # Smart logging logic
                should_log = False

                if flow_key not in self.installed_flows:
                    # First time seeing this flow
                    should_log = True
                    self.installed_flows[flow_key] = current_time
                    self.log_counter[flow_key] = 1
                elif icmp_type != icmp.ICMP_ECHO_REPLY:
                    # Non-ICMP reply traffic
                    should_log = True
                    self.log_counter[flow_key] = self.log_counter.get(flow_key, 0) + 1
                elif should_install_flow:
                    # Flow being installed (first packet)
                    should_log = True
                    self.log_counter[flow_key] = 1
                elif current_time - self.last_log_time.get(flow_key, 0) > 10:  # Log every 10 seconds
                    # Periodic logging for long-running flows
                    should_log = True
                    self.log_counter[flow_key] = self.log_counter.get(flow_key, 0) + 1

                if should_log:
                    count = self.log_counter.get(flow_key, 1)
                    if count > 1:
                        self.logger.info(f"{reason} | {src_ip} -> {dst_ip} (packet #{count})")
                    else:
                        self.logger.info(f"{reason} | {src_ip} -> {dst_ip}")
                    self.last_log_time[flow_key] = current_time

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