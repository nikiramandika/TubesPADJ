from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, icmp, arp

class MedicalSimpleController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MedicalSimpleController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.arp_table = {}  # IP to MAC mapping
        self.ip_to_mac = {}   # Additional IP to MAC mapping

        # Pre-populate ARP table dengan known MAC addresses
        self.arp_table = {
            # G9 Building
            '192.168.1.10': '00:00:00:00:01:01',  # mhs1
            '192.168.1.11': '00:00:00:00:01:02',  # mhs2
            '192.168.1.50': '00:00:00:00:01:50',  # lab1a
            '192.168.1.51': '00:00:00:00:01:51',  # lab1b
            '192.168.10.33': '00:00:00:00:0A:01',  # dekan
            '192.168.10.34': '00:00:00:00:0A:02',  # sekre

            # G10 Building
            '192.16.21.11': '00:00:00:00:15:01',  # adm10a
            '192.16.21.12': '00:00:00:00:15:02',  # adm10b
        }

        # Copy ke ip_to_mac untuk routing
        self.ip_to_mac = self.arp_table.copy()
                
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
                '192.16.20.71', '192.16.20.72',
                # G10 Lt3 Nirkabel (Dosen)
                '192.16.20.201', '192.16.20.202'
            ],

            # Administrasi Gedung G10 - sesuai topology
            'ADMIN_G10': [
                # G10 Lt1 Kabel (Administrasi)
                '192.16.21.11', '192.16.21.12'
            ],

            # Aula - sesuai topology
            'AULA': [
                # G10 Lt2 Kabel (Aula)
                '192.16.21.18', '192.16.21.19'
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

    def handle_arp(self, datapath, in_port, eth_pkt, arp_pkt):
        """Handle ARP packets for inter-subnet communication"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Learn IP to MAC mapping
        self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
        self.ip_to_mac[arp_pkt.src_ip] = arp_pkt.src_mac

        # Update MAC to port mapping
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][arp_pkt.src_mac] = in_port

        if arp_pkt.opcode == arp.ARP_REQUEST:
            # Handle ARP request
            self.logger.info(f"🔍 ARP Request: {arp_pkt.src_ip} ({arp_pkt.src_mac}) asking for {arp_pkt.dst_ip}")
            self.logger.info(f"📋 Current ARP table: {self.arp_table}")

            # Check if we know the target MAC
            if arp_pkt.dst_ip in self.arp_table:
                # Send ARP reply
                target_mac = self.arp_table[arp_pkt.dst_ip]
                self.logger.info(f"Sending ARP Reply: {arp_pkt.dst_ip} is at {target_mac}")

                # Create ARP reply packet
                ether = ethernet.ethernet(
                    dst=eth_pkt.src,
                    src=target_mac,
                    ethertype=ether_types.ETH_TYPE_ARP
                )

                arp_reply = arp.arp(
                    opcode=arp.ARP_REPLY,
                    src_mac=target_mac,
                    src_ip=arp_pkt.dst_ip,
                    dst_mac=arp_pkt.src_mac,
                    dst_ip=arp_pkt.src_ip
                )

                p = packet.Packet()
                p.add_protocol(ether)
                p.add_protocol(arp_reply)
                p.serialize()

                # Send ARP reply
                actions = [parser.OFPActionOutput(in_port)]
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=ofproto.OFPP_CONTROLLER,
                    actions=actions,
                    data=p.data
                )
                datapath.send_msg(out)

            else:
                # Flood ARP request if we don't know the target
                self.logger.info(f"Flooding ARP Request for {arp_pkt.dst_ip}")
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=actions,
                    data=eth_pkt
                )
                datapath.send_msg(out)

        elif arp_pkt.opcode == arp.ARP_REPLY:
            # Handle ARP reply
            self.logger.info(f"ARP Reply: {arp_pkt.src_ip} is at {arp_pkt.src_mac}")
            # Learn from ARP reply
            self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
            self.ip_to_mac[arp_pkt.src_ip] = arp_pkt.src_mac

            # Install flow for this IP-to-MAC mapping
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_ARP,
                arp_tpa=arp_pkt.src_ip
            )
            actions = [parser.OFPActionOutput(in_port)]
            self.add_flow(datapath, 2, match, actions)

            # Flood ARP reply to other ports
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port,
                actions=actions,
                data=eth_pkt
            )
            datapath.send_msg(out)

    def check_security(self, src_ip, dst_ip, icmp_type=None):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # Helper function to check if IP is in G9 building
        def is_g9_building(ip):
            return (ip.startswith('192.168.1.') or ip.startswith('192.168.2.') or
                    ip.startswith('192.168.3.') or ip.startswith('192.168.4.') or
                    ip.startswith('192.168.5.') or ip.startswith('192.168.6.') or
                    ip.startswith('192.168.7.') or ip.startswith('192.168.8.') or
                    ip.startswith('192.168.9.') or ip.startswith('192.168.10.'))

        # Helper function to check if IP is in G10 building
        def is_g10_building(ip):
            return ip.startswith('192.16.20.') or ip.startswith('192.16.21.')

        # Helper function to check if two IPs can communicate within same building
        def can_communicate_within_building(src_ip, dst_ip):
            """Check if two IPs can communicate based on building assignment"""
            src_in_g9 = is_g9_building(src_ip)
            dst_in_g9 = is_g9_building(dst_ip)
            src_in_g10 = is_g10_building(src_ip)
            dst_in_g10 = is_g10_building(dst_ip)

            # Same building communication is allowed
            if (src_in_g9 and dst_in_g9) or (src_in_g10 and dst_in_g10):
                return True
            return False

        # Helper function to add routing flows for inter-subnet communication
        def setup_routing(datapath, src_ip, dst_ip, in_port, out_port):
            """Setup routing flows for inter-subnet communication"""
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # Create flow for return traffic
            match = parser.OFPMatch(
                eth_type=0x0800,  # IPv4
                ipv4_dst=src_ip,
                in_port=out_port
            )
            actions = [parser.OFPActionOutput(in_port)]
            self.add_flow(datapath, 2, match, actions)

        # RULE 1: Keuangan ke Dekan -> ALLOW (Izin Khusus Internal Secure)
        if src_ip in self.zones['KEUANGAN'] and dst_ip in self.zones['DEKAN']:
             return True, "ALLOW: Internal Report (Keuangan -> Dekan)", True

        # RULE 1a: Internal Communication within same building -> ALLOW
        if can_communicate_within_building(src_ip, dst_ip):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Internal Building)", False
            # Exception: Dosen -> Ujian masih di BLOCK
            if not (src_cat == 'DOSEN' and dst_ip in self.zones['UJIAN']):
                return True, "ALLOW: Internal Building Communication", True

        # RULE 2: Cross-Building Admin Communication -> ALLOW
        if ((src_cat == 'SECURE' and dst_cat == 'ADMIN_G10') or
            (src_cat == 'ADMIN_G10' and dst_cat == 'SECURE')):
            return True, "ALLOW: Cross-Building Admin Communication", True

        # RULE 3: Mahasiswa/Lab -> Secure (BLOCK) - only for cross-building
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE' and is_g9_building(src_ip) and is_g9_building(dst_ip):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Mahasiswa/Lab mencoba akses Zona Aman", False

        # RULE 4: Mahasiswa/Lab -> Dosen (BLOCK) - only for cross-building
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN' and is_g9_building(src_ip) and is_g9_building(dst_ip):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Mahasiswa/Lab mencoba akses Dosen Pribadi", False

        # RULE 5: Dosen -> Ujian (BLOCK) - spesifik rule tetap berlaku
        if src_cat == 'DOSEN' and dst_ip in self.zones['UJIAN']:
            return False, "BLOCK: Dosen akses Server Ujian", False

        # RULE 6: Mahasiswa/Lab → Admin G10 (ALLOW) - cross building
        if src_cat == 'MAHASISWA' and dst_cat == 'ADMIN_G10':
            return True, "ALLOW: Mahasiswa akses Administrasi G10", True

        # RULE 7: Mahasiswa/Lab → Aula (ALLOW)
        if src_cat == 'MAHASISWA' and dst_cat == 'AULA':
            return True, "ALLOW: Mahasiswa akses Aula", True

        # RULE 8: Dosen → Secure (BLOCK) - only if different buildings
        if src_cat == 'DOSEN' and dst_cat == 'SECURE' and not (is_g9_building(src_ip) and is_g9_building(dst_ip)):
            if icmp_type == icmp.ICMP_ECHO_REPLY:
                return True, "ALLOW: Ping Reply (Return Traffic)", False
            return False, "BLOCK: Dosen akses Zona Aman", False

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

        # Handle ARP packets
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            if arp_pkt:
                self.handle_arp(datapath, in_port, eth, arp_pkt)
                return

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

        # --- LOGIKA ROUTING ---
        # Cek apakah ini adalah traffic antar subnet dalam gedung yang sama
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst

            # Helper function untuk menentukan gedung
            def is_g9_building(ip):
                return (ip.startswith('192.168.1.') or ip.startswith('192.168.2.') or
                        ip.startswith('192.168.3.') or ip.startswith('192.168.4.') or
                        ip.startswith('192.168.5.') or ip.startswith('192.168.6.') or
                        ip.startswith('192.168.7.') or ip.startswith('192.168.8.') or
                        ip.startswith('192.168.9.') or ip.startswith('192.168.10.'))

            def is_g10_building(ip):
                return ip.startswith('192.16.20.') or ip.startswith('192.16.21.')

            # Helper function untuk menentukan subnet
            def get_subnet_network(ip):
                if ip.startswith('192.168.1.'): return '192.168.1.0/22'
                if ip.startswith('192.168.2.'): return '192.168.2.0/24'
                if ip.startswith('192.168.3.'): return '192.168.3.0/24'
                if ip.startswith('192.168.5.'): return '192.168.5.0/24'
                if ip.startswith('192.168.6.'): return '192.168.6.0/22'
                if ip.startswith('192.168.10.'): return '192.168.10.0/24'
                if ip.startswith('192.16.20.'): return '192.16.20.0/24'
                if ip.startswith('192.16.21.'): return '192.16.21.0/24'
                return None

            # Jika beda subnet tapi dalam gedung yang sama, lakukan routing
            src_subnet = get_subnet_network(src_ip)
            dst_subnet = get_subnet_network(dst_ip)

            if (src_subnet != dst_subnet and
                ((is_g9_building(src_ip) and is_g9_building(dst_ip)) or
                 (is_g10_building(src_ip) and is_g10_building(dst_ip)))):

                self.logger.info(f"Inter-subnet routing: {src_ip} ({src_subnet}) -> {dst_ip} ({dst_subnet})")

                # Learn IP to MAC mapping for routing
                if dst_ip in self.ip_to_mac:
                    dst_mac = self.ip_to_mac[dst_ip]
                    self.logger.info(f"Known destination MAC for {dst_ip}: {dst_mac}")

                    # Install specific flow for this IP pair
                    match_specific = parser.OFPMatch(
                        eth_type=ether_types.ETH_TYPE_IP,
                        eth_dst=dst_mac,
                        ipv4_src=src_ip,
                        ipv4_dst=dst_ip,
                        in_port=in_port
                    )
                    actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                    self.add_flow(datapath, 10, match_specific, actions)
                else:
                    # Flood to learn MAC address
                    self.logger.info(f"Unknown destination MAC for {dst_ip}, flooding...")
                    match_flood = parser.OFPMatch(
                        eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_src=src_ip,
                        ipv4_dst=dst_ip,
                        in_port=in_port
                    )
                    actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                    self.add_flow(datapath, 5, match_flood, actions)

        # --- LOGIKA FORWARDING ---
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