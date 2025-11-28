from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types

class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def _ip_in_subnet(self, ip, network, prefix_len):
        """Helper method untuk mengecek apakah IP berada dalam subnet"""
        import ipaddress
        try:
            network_obj = ipaddress.IPv4Network(f"{network}/{prefix_len}", strict=False)
            ip_obj = ipaddress.IPv4Address(ip)
            return ip_obj in network_obj
        except:
            # Fallback ke string matching jika ipaddress gagal
            return ip.startswith(network.split('.')[0] + '.' + network.split('.')[1] + '.' + network.split('.')[2])

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install ARP flow rule (priority 1000) - highest priority
        match = parser.OFPMatch(eth_type=0x0806)  # ARP
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 1000, match, actions)

        # Install ICMP flow rule (priority 900) - allow ping
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=1)  # IPv4 + ICMP
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 900, match, actions)

        # Install basic routing for internal subnets (priority 800)
        # Allow traffic within same subnet groups
        match = parser.OFPMatch(eth_type=0x0800,
                              ipv4_src=('192.168.10.0', '255.255.255.0'),
                              ipv4_dst=('192.168.10.0', '255.255.255.0'))
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 800, match, actions)

        match = parser.OFPMatch(eth_type=0x0800,
                              ipv4_src=('172.16.21.0', '255.255.255.0'),
                              ipv4_dst=('172.16.21.0', '255.255.255.0'))
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 800, match, actions)

        # Install table-miss flow entry
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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # --- LOGIKA FIREWALL BERDASARKAN ZONA SENSITIVITAS ---
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Update subnet mapping yang benar:
            # G9 L1: 192.168.10.0/27 - Ruang Kuliah + AP Mahasiswa (h1,h2)
            # G9 L2 S1: 192.168.10.32/27 - Dosen (h3,h4)
            # G9 L2 S2: 192.168.10.64/27 - Administrasi & Keuangan (h5,h6) - HIGH-SENSITIVITY
            # G9 L2 S3: 192.168.10.96/27 - Pimpinan & Sekretariat (h7,h8) - VERY HIGH-SENSITIVITY
            # G9 L2 S4: 192.168.10.128/27 - Ujian & Mahasiswa (h9,h10) - CONTROLLED
            # G9 L3 S1: 192.168.10.160/27 - Lab 1 (h11,h12)
            # G9 L3 S2: 192.168.10.192/27 - Lab 2 (h13,h14)
            # G9 L3 S3: 192.168.10.224/27 - Lab 3 (h15,h16)
            # G9 L3 Main: 192.168.10.128/27 - AP + Mahasiswa (h17,h18,h19)
            # G10: 172.16.21.0/24 - Seluruh Gedung G10

            # Priority rules:
            # 1. SELALU izinkan traffic dalam subnet yang sama
            # 2. SELALU izinkan ARP (sudah di handle switch features)
            # 3. SELALU izinkan ICMP untuk testing
            # 4. Firewall logic untuk traffic antar subnet

            # Basic connectivity rules (PERMISSIVE untuk testing)
            if (src_ip.startswith("192.168.10.") and dst_ip.startswith("192.168.10.")) or \
               (src_ip.startswith("172.16.21.") and dst_ip.startswith("172.16.21.")):
                self.logger.info(f"ALLOWED: Same building traffic dari {src_ip} ke {dst_ip}")
                # Lanjut ke normal processing (tidak return)

            # VERY HIGH-SENSITIVITY: Pimpinan & Sekretariat (192.168.10.96/27)
            if self._ip_in_subnet(dst_ip, "192.168.10.96", 27):
                # Hanya izinkan dari zona yang sama dan dari Administrasi
                if not (self._ip_in_subnet(src_ip, "192.168.10.96", 27) or
                       self._ip_in_subnet(src_ip, "192.168.10.64", 27)):
                    self.logger.info(f"BLOCKED: Akses ke zona Pimpinan & Sekretariat ditolak dari {src_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Akses ke zona Pimpinan & Sekretariat dari {src_ip}")

            # HIGH-SENSITIVITY: Administrasi & Keuangan (192.168.10.64/27)
            elif self._ip_in_subnet(dst_ip, "192.168.10.64", 27):
                # Hanya izinkan dari zona yang sama, dari Pimpinan, dan dari Dosen
                if not (self._ip_in_subnet(src_ip, "192.168.10.64", 27) or
                       self._ip_in_subnet(src_ip, "192.168.10.96", 27) or
                       self._ip_in_subnet(src_ip, "192.168.10.32", 27)):
                    self.logger.info(f"BLOCKED: Akses ke zona Administrasi & Keuangan ditolak dari {src_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Akses ke zona Administrasi & Keuangan dari {src_ip}")

            # CONTROLLED: Ujian (192.168.10.128/27)
            elif self._ip_in_subnet(dst_ip, "192.168.10.128", 27):
                # Izinkan dari Dosen dan Pimpinan, blokir dari Mahasiswa
                if (self._ip_in_subnet(src_ip, "192.168.10.0", 27) or  # Ruang Kuliah
                    self._ip_in_subnet(src_ip, "192.168.10.128", 27)):  # Ujian zone sendiri
                    self.logger.info(f"BLOCKED: Mahasiswa tidak diizinkan ke zona Ujian dari {src_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Akses ke zona Ujian dari {src_ip}")

            # Educational zones (more permissive)
            elif (self._ip_in_subnet(src_ip, "192.168.10.0", 27) or     # Ruang Kuliah
                  self._ip_in_subnet(src_ip, "192.168.10.128", 27) or   # Mahasiswa
                  self._ip_in_subnet(src_ip, "172.16.21.0", 24)):       # Gedung G10
                # Batasi akses ke zona VERY HIGH (Pimpinan)
                if self._ip_in_subnet(dst_ip, "192.168.10.96", 27):
                    self.logger.info(f"BLOCKED: Educational zone access ke Pimpinan ditolak dari {src_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Educational zone traffic dari {src_ip} ke {dst_ip}")

            # Staff zones (Dosen)
            elif self._ip_in_subnet(src_ip, "192.168.10.32", 27):  # Dosen
                self.logger.info(f"ALLOWED: Dosen traffic dari {src_ip} ke {dst_ip}")

            # Lab zones
            elif (self._ip_in_subnet(src_ip, "192.168.10.160", 27) or   # Lab 1
                  self._ip_in_subnet(src_ip, "192.168.10.192", 27) or   # Lab 2
                  self._ip_in_subnet(src_ip, "192.168.10.224", 27)):    # Lab 3
                # Lab bisa mengakses zona educational terbatas
                if self._ip_in_subnet(dst_ip, "192.168.10.96", 27):      # Blok ke Pimpinan
                    self.logger.info(f"BLOCKED: Lab access ke Pimpinan ditolak dari {src_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Lab traffic dari {src_ip} ke {dst_ip}")

            # Default: log dan lanjutkan
            self.logger.info(f"PROCESSING: Traffic dari {src_ip} ke {dst_ip}")

            # Rules untuk GEDUNG G10 (172.16.21.0/24)
            # Subnet breakdown:
            # - 172.16.21.0/28: Lantai 1 (Ruang Kuliah + AP Mahasiswa)
            # - 172.16.21.16/29: Lantai 2 (Dosen + AP Mahasiswa + AP Aula)
            # - 172.16.21.32/26: Lantai 3 (Dosen + AP Mahasiswa)

            # Izinkan akses untuk mahasiswa melalui AP di Gedung G10
            # AP Mahasiswa memiliki IP: 172.16.21.1 (L1), 172.16.21.19 (L2), 172.16.21.35 (L3)
            ap_mahasiswa_ips = ["172.16.21.1", "172.16.21.19", "172.16.21.35"]
            ap_aula_ips = ["172.16.21.21"]

            # Check jika source adalah zona atau AP di Gedung G10
            is_mahasiswa_g10_ap = any(src_ip.startswith(ap_ip) for ap_ip in ap_mahasiswa_ips)
            is_aula_g10_ap = any(src_ip.startswith(ap_ip) for ap_ip in ap_aula_ips)

            # Rules untuk AP Mahasiswa Gedung G10
            if is_mahasiswa_g10_ap:
                # Mahasiswa di Gedung G10 bisa mengakses:
                # - Internal Gedung G10
                # - Lab dan zona mahasiswa di Gedung G9
                # - Tidak bisa akses zona sensitif (Admin, Pimpinan)
                if dst_ip.startswith("192.168.10.32") or dst_ip.startswith("192.168.10.64"):
                    self.logger.info(f"BLOCKED: Mahasiswa AP G10 tidak diizinkan akses zona sensitif dari {src_ip} ke {dst_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Mahasiswa AP G10 mengakses {dst_ip} dari {src_ip}")

            # Rules untuk AP Aula Gedung G10
            if is_aula_g10_ap:
                # AP Aula bisa mengakses lebih banyak zona untuk presentasi dan kegiatan
                # Tapi tetap dibatasi untuk zona very high-sensitivity
                if dst_ip.startswith("192.168.10.64"):  # Zona Pimpinan
                    self.logger.info(f"BLOCKED: AP Aula tidak diizinkan akses zona Pimpinan dari {src_ip} ke {dst_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: AP Aula mengakses {dst_ip} dari {src_ip}")

            # Rules untuk staf Gedung G10 (non-AP)
            if dst_ip.startswith("172.16.21."):
                if not (src_ip.startswith("172.16.21.") or
                         src_ip.startswith("192.168.10.96") or  # Dosen G9
                         src_ip.startswith("192.168.10.64") or  # Pimpinan G9
                         is_mahasiswa_g10_ap or is_aula_g10_ap):  # AP Mahasiswa & Aula G10
                    self.logger.info(f"BLOCKED: Akses ke Gedung G10 tidak diizinkan dari luar gedung dari {src_ip}")
                    return

            # Rules untuk SEMI-TRUSTED (Dosen - 192.168.10.96/27 dan 172.16.21.16/29)
            # Dosen dapat mengakses zona ujian dan mahasiswa dengan batasan
            if src_ip.startswith("192.168.10.96") and dst_ip.startswith("192.168.10.128"):
                self.logger.info(f"ALLOWED: Dosen mengakses Zona Ujian dari {src_ip} ke {dst_ip}")

            # Log semua traffic yang diperbolehkan untuk monitoring
            self.logger.info(f"ALLOWED: Traffic dari {src_ip} ke {dst_ip}")
        # --- END FIREWALL ---

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