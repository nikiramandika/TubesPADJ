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

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

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

            # Gedung G9 - Lantai 1: Ruang Kuliah + AP Mahasiswa (192.168.10.0/27) - h1, h2
            # Gedung G9 - Lantai 2 - Switch 1: Dosen (192.168.10.32/27) - h3, h4
            # Gedung G9 - Lantai 2 - Switch 2: Administrasi & Keuangan (192.168.10.64/27) - h5, h6 - HIGH-SENSITIVITY
            # Gedung G9 - Lantai 2 - Switch 3: Pimpinan & Sekretariat (192.168.10.96/27) - h7, h8 - VERY HIGH-SENSITIVITY
            # Gedung G9 - Lantai 2 - Switch 4: Ujian & Mahasiswa (192.168.10.128/27) - h9, h10 - CONTROLLED & ISOLATED
            # Gedung G9 - Lantai 3 - Lab 1 (192.168.10.160/27) - h11, h12
            # Gedung G9 - Lantai 3 - Lab 2 (192.168.10.192/27) - h13, h14
            # Gedung G9 - Lantai 3 - Lab 3 (192.168.10.224/27) - h15, h16
            # Gedung G9 - Lantai 3 - AP + Mahasiswa (192.168.10.240/28) - h17, h18, h19
            # Gedung G10 Lantai 1: Ruang Kuliah + AP Mahasiswa (172.16.21.0/28) - h21, h22
            # Gedung G10 Lantai 2: Dosen (172.16.21.16/28) - h23, h24
            # Gedung G10 Lantai 3: Dosen (172.16.21.32/27) - h25, h26
            # AP Tambahan Gedung G10: L2 (172.16.21.19/28) h27,h28, Aula (172.16.21.21/28) h29,h30, L3 (172.16.21.35/27) h31,h32

            # Rules untuk VERY HIGH-SENSITIVITY (Pimpinan & Sekretariat - 192.168.10.96/27)
            # Blokir semua akses ke zona ini dari zona lain kecuali dari Administrasi & Keuangan
            if (dst_ip.startswith("192.168.10.96") and
                not (src_ip.startswith("192.168.10.64") or src_ip.startswith("192.168.10.96"))):
                self.logger.info(f"BLOCKED: Akses tidak diizinkan ke Zona Pimpinan & Sekretariat dari {src_ip}")
                return

            # Rules untuk HIGH-SENSITIVITY (Administrasi & Keuangan - 192.168.10.64/27)
            # Hanya izinkan akses dari zona yang sama dan dari Pimpinan
            if (dst_ip.startswith("192.168.10.64") and
                not (src_ip.startswith("192.168.10.64") or src_ip.startswith("192.168.10.96"))):
                self.logger.info(f"BLOCKED: Akses tidak diizinkan ke Zona Administrasi & Keuangan dari {src_ip}")
                return

            # Rules untuk CONTROLLED & ISOLATED (Ujian - 192.168.10.128/27)
            # Blokir akses dari mahasiswa selama ujian, hanya izinkan dari dosen
            if (dst_ip.startswith("192.168.10.128") and
                (src_ip.startswith("192.168.10.0") or src_ip.startswith("192.168.10.240"))):  # Mahasiswa
                self.logger.info(f"BLOCKED: Mahasiswa tidak diizinkan mengakses Zona Ujian dari {src_ip}")
                return

            # Rules untuk ZONA RUANG KULIAH & MAHASISWA
            # Gedung G9 Lantai 1: Ruang Kuliah + AP (192.168.10.0/27)
            # Gedung G10 Lantai 1: Ruang Kuliah + AP (172.16.21.0/28)
            # Batasi akses ke zona sensitif
            if (src_ip.startswith("192.168.10.0") or      # Ruang Kuliah G9 L1
                src_ip.startswith("172.16.21.0") or      # Ruang Kuliah G10 L1
                src_ip.startswith("192.168.10.240")):     # AP & Mahasiswa G9 L3
                if (dst_ip.startswith("192.168.10.64") or   # Admin & Keuangan
                    dst_ip.startswith("192.168.10.96")):    # Pimpinan & Sekretariat
                    self.logger.info(f"BLOCKED: Ruang Kuliah/Mahasiswa tidak diizinkan mengakses zona sensitif dari {src_ip} ke {dst_ip}")
                    return

                # Izinkan akses ke zona pendidikan lainnya
                self.logger.info(f"ALLOWED: Ruang Kuliah/Mahasiswa mengakses zona edukasi {dst_ip} dari {src_ip}")

            # Rules untuk Dosen yang mencoba mengakses zona lain
            if src_ip.startswith("192.168.10.32") and dst_ip.startswith("192.168.10.0"):  # Dosen -> Ruang Kuliah
                self.logger.info(f"ALLOWED: Dosen mengakses Ruang Kuliah dari {src_ip} ke {dst_ip}")

            # Rules untuk traffic antar gedung (bypass untuk testing)
            if (src_ip.startswith("192.168.10.") and dst_ip.startswith("172.16.21.")) or \
               (src_ip.startswith("172.16.21.") and dst_ip.startswith("192.168.10.")):
                self.logger.info(f"ALLOWED: Antara gedung traffic dari {src_ip} ke {dst_ip}")
                return

            # Rules untuk traffic dalam subnet yang sama (allow untuk testing)
            if (src_ip.startswith("192.168.10.") and dst_ip.startswith("192.168.10.")) or \
               (src_ip.startswith("172.16.21.") and dst_ip.startswith("172.16.21.")):
                self.logger.info(f"ALLOWED: Same subnet traffic dari {src_ip} ke {dst_ip}")
                return

            # Rules untuk GEDUNG G10 (172.16.21.0/24)
            # Subnet breakdown:
            # - 172.16.21.0/28: Lantai 1 (Ruang Kuliah + AP Mahasiswa)
            # - 172.16.21.16/28: Lantai 2 (Dosen + AP Mahasiswa + AP Aula)
            # - 172.16.21.32/27: Lantai 3 (Dosen + AP Mahasiswa)

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
                if (dst_ip.startswith("192.168.10.64") or   # Admin & Keuangan
                    dst_ip.startswith("192.168.10.96")):    # Pimpinan
                    self.logger.info(f"BLOCKED: Mahasiswa AP G10 tidak diizinkan akses zona sensitif dari {src_ip} ke {dst_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: Mahasiswa AP G10 mengakses {dst_ip} dari {src_ip}")

            # Rules untuk AP Aula Gedung G10
            if is_aula_g10_ap:
                # AP Aula bisa mengakses lebih banyak zona untuk presentasi dan kegiatan
                # Tapi tetap dibatasi untuk zona very high-sensitivity
                if dst_ip.startswith("192.168.10.96"):  # Zona Pimpinan
                    self.logger.info(f"BLOCKED: AP Aula tidak diizinkan akses zona Pimpinan dari {src_ip} ke {dst_ip}")
                    return
                else:
                    self.logger.info(f"ALLOWED: AP Aula mengakses {dst_ip} dari {src_ip}")

            # Rules untuk staf Gedung G10 (non-AP)
            if dst_ip.startswith("172.16.21."):
                if not (src_ip.startswith("172.16.21.") or
                         src_ip.startswith("192.168.10.32") or  # Dosen G9
                         src_ip.startswith("192.168.10.96") or  # Pimpinan G9
                         is_mahasiswa_g10_ap or is_aula_g10_ap):  # AP Mahasiswa & Aula G10
                    self.logger.info(f"BLOCKED: Akses ke Gedung G10 tidak diizinkan dari luar gedung dari {src_ip}")
                    return

            # Rules untuk SEMI-TRUSTED (Dosen - 192.168.10.32/27 dan 172.16.21.16/28)
            # Dosen dapat mengakses zona ujian dan mahasiswa dengan batasan
            if src_ip.startswith("192.168.10.32") and dst_ip.startswith("192.168.10.128"):
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