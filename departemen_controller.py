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

            # Fungsi helper untuk menentukan zona dengan lebih presisi
            def get_zone(ip):
                try:
                    # Konversi IP ke integer untuk perbandingan range yang lebih akurat
                    ip_parts = list(map(int, ip.split('.')))
                    if ip_parts[0] == 192 and ip_parts[1] == 168 and ip_parts[2] == 10:
                        last_octet = ip_parts[3]
                        if 0 <= last_octet <= 31:
                            return "RUANG_KULIAH_G9_L1"
                        elif 32 <= last_octet <= 63:
                            return "DOSEN_G9_L2"
                        elif 64 <= last_octet <= 95:
                            return "ADMIN_G9_L2"
                        elif 96 <= last_octet <= 127:
                            return "PEIMPINAN_G9_L2"
                        elif 128 <= last_octet <= 159:
                            return "UJIAN_G9_L2"
                        elif 160 <= last_octet <= 191:
                            return "LAB1_G9_L3"
                        elif 192 <= last_octet <= 223:
                            return "LAB2_G9_L3"
                        elif 224 <= last_octet <= 255:
                            return "LAB3_MAHASISWA_G9_L3"

                    elif ip_parts[0] == 172 and ip_parts[1] == 16 and ip_parts[2] == 21:
                        last_octet = ip_parts[3]
                        if 0 <= last_octet <= 15:
                            return "RUANG_KULIAH_G10_L1"
                        elif 16 <= last_octet <= 23:
                            return "DOSEN_G10_L2"
                        elif 24 <= last_octet <= 31:
                            return "AP_AULA_G10_L2"
                        elif 32 <= last_octet <= 63:
                            return "DOSEN_G10_L3"
                        elif 64 <= last_octet <= 95:
                            return "AP_MAHASISWA_G10_L3"
                except:
                    pass
                return "UNKNOWN"

            src_zone = get_zone(src_ip)
            dst_zone = get_zone(dst_ip)

            self.logger.info(f"Traffic: {src_ip} ({src_zone}) -> {dst_ip} ({dst_zone})")

            # 1. VERY HIGH SECURITY - Zona Pimpinan (192.168.10.96-127)
            # Hanya bisa diakses dari zona Administrasi dan Pimpinan itu sendiri
            if dst_zone == "PEIMPINAN_G9_L2":
                if src_zone not in ["ADMIN_G9_L2", "PEIMPINAN_G9_L2"]:
                    self.logger.info(f"BLOCKED: Akses ke zona Pimpinan hanya dari Admin/Pimpinan")
                    return
                else:
                    self.logger.info(f"ALLOWED: Akses ke zona Pimpinan dari {src_zone}")

            # 2. HIGH SECURITY - Zona Administrasi (192.168.10.64-95)
            # Hanya bisa diakses dari zona Dosen, Admin, dan Pimpinan
            elif dst_zone == "ADMIN_G9_L2":
                if src_zone not in ["DOSEN_G9_L2", "ADMIN_G9_L2", "PEIMPINAN_G9_L2"]:
                    self.logger.info(f"BLOCKED: Akses ke zona Admin hanya dari Dosen/Admin/Pimpinan")
                    return
                else:
                    self.logger.info(f"ALLOWED: Akses ke zona Admin dari {src_zone}")

            # 3. Zona Mahasiswa tidak bisa akses zona sensitif (Admin, Pimpinan)
            elif src_zone in ["RUANG_KULIAH_G9_L1", "RUANG_KULIAH_G10_L1", "LAB3_MAHASISWA_G9_L3", "AP_MAHASISWA_G10_L3"]:
                if dst_zone in ["ADMIN_G9_L2", "PEIMPINAN_G9_L2"]:
                    self.logger.info(f"BLOCKED: Mahasiswa ({src_zone}) tidak boleh akses zona sensitif ({dst_zone})")
                    return

            # 4. Traffic dalam subnet yang sama diizinkan
            if (src_ip.startswith("192.168.10.") and dst_ip.startswith("192.168.10.")) or \
               (src_ip.startswith("172.16.21.") and dst_ip.startswith("172.16.21.")):
                self.logger.info(f"ALLOWED: Same subnet traffic")

            # 5. Traffic antar gedung diizinkan dengan batasan
            elif ((src_ip.startswith("192.168.10.") and dst_ip.startswith("172.16.21.")) or
                  (src_ip.startswith("172.16.21.") and dst_ip.startswith("192.168.10."))):
                # Cegah mahasiswa G10 akses zona sensitif G9
                if src_zone in ["RUANG_KULIAH_G10_L1", "AP_MAHASISWA_G10_L3"] and dst_zone in ["ADMIN_G9_L2", "PEIMPINAN_G9_L2"]:
                    self.logger.info(f"BLOCKED: Mahasiswa G10 tidak boleh akses zona sensitif G9")
                    return
                else:
                    self.logger.info(f"ALLOWED: Inter-building traffic dengan batasan")

            else:
                self.logger.info(f"ALLOWED: Default allow")
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