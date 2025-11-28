from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
import ipaddress

class DeptFirewall(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DeptFirewall, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def ip_in_subnet(self, ip_str, subnet_str):
        """Check if IP address is in subnet"""
        try:
            return ipaddress.ip_address(ip_str) in ipaddress.ip_network(subnet_str, strict=False)
        except:
            return False

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
        blocked = False
        
        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Define subnets properly
            RUANG_KULIAH_G9_L1 = "192.168.10.0/27"
            DOSEN_G9_L2 = "192.168.10.32/27"
            ADMIN_G9_L2 = "192.168.10.64/27"
            PIMPINAN_G9_L2 = "192.168.10.96/27"
            UJIAN_G9_L2 = "192.168.10.128/27"
            LAB1_G9_L3 = "192.168.10.160/27"
            LAB2_G9_L3 = "192.168.10.192/27"
            LAB3_G9_L3 = "192.168.10.224/27"
            MAHASISWA_G9_L3 = "192.168.10.240/28"
            
            RUANG_KULIAH_G10_L1 = "172.16.21.0/28"
            DOSEN_G10_L2 = "172.16.21.16/28"
            DOSEN_G10_L3 = "172.16.21.32/27"

            # Rules untuk VERY HIGH-SENSITIVITY (Pimpinan & Sekretariat - 192.168.10.96/27)
            # Blokir semua akses ke zona ini dari zona lain kecuali dari Administrasi & Keuangan
            if self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2):
                if not (self.ip_in_subnet(src_ip, ADMIN_G9_L2) or 
                        self.ip_in_subnet(src_ip, PIMPINAN_G9_L2)):
                    self.logger.info(f"*** BLOCKED: Akses tidak diizinkan ke Zona Pimpinan & Sekretariat dari {src_ip} ke {dst_ip}")
                    blocked = True

            # Rules untuk HIGH-SENSITIVITY (Administrasi & Keuangan - 192.168.10.64/27)
            # Hanya izinkan akses dari zona yang sama dan dari Pimpinan
            if self.ip_in_subnet(dst_ip, ADMIN_G9_L2):
                if not (self.ip_in_subnet(src_ip, ADMIN_G9_L2) or 
                        self.ip_in_subnet(src_ip, PIMPINAN_G9_L2)):
                    self.logger.info(f"*** BLOCKED: Akses tidak diizinkan ke Zona Administrasi & Keuangan dari {src_ip} ke {dst_ip}")
                    blocked = True

            # Rules untuk CONTROLLED & ISOLATED (Ujian - 192.168.10.128/27)
            # Blokir akses dari mahasiswa selama ujian, hanya izinkan dari dosen
            if self.ip_in_subnet(dst_ip, UJIAN_G9_L2):
                if (self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) or 
                    self.ip_in_subnet(src_ip, MAHASISWA_G9_L3)):  # Mahasiswa
                    self.logger.info(f"*** BLOCKED: Mahasiswa tidak diizinkan mengakses Zona Ujian dari {src_ip} ke {dst_ip}")
                    blocked = True

            # Rules untuk ZONA RUANG KULIAH & MAHASISWA
            # Batasi akses ke zona sensitif
            if (self.ip_in_subnet(src_ip, RUANG_KULIAH_G9_L1) or 
                self.ip_in_subnet(src_ip, RUANG_KULIAH_G10_L1) or 
                self.ip_in_subnet(src_ip, MAHASISWA_G9_L3)):
                if (self.ip_in_subnet(dst_ip, ADMIN_G9_L2) or 
                    self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2)):
                    self.logger.info(f"*** BLOCKED: Ruang Kuliah/Mahasiswa tidak diizinkan mengakses zona sensitif dari {src_ip} ke {dst_ip}")
                    blocked = True

            # Rules untuk Dosen yang mengakses Zona Ujian - ALLOWED
            if self.ip_in_subnet(src_ip, DOSEN_G9_L2) and self.ip_in_subnet(dst_ip, UJIAN_G9_L2):
                self.logger.info(f"ALLOWED: Dosen mengakses Zona Ujian dari {src_ip} ke {dst_ip}")

            # Rules untuk Dosen yang mengakses Ruang Kuliah - ALLOWED
            if self.ip_in_subnet(src_ip, DOSEN_G9_L2) and self.ip_in_subnet(dst_ip, RUANG_KULIAH_G9_L1):
                self.logger.info(f"ALLOWED: Dosen mengakses Ruang Kuliah dari {src_ip} ke {dst_ip}")

            # Rules untuk traffic dalam subnet/gedung yang sama
            src_network = None
            dst_network = None
            
            # Tentukan network dari IP
            if src_ip.startswith("192.168.10."):
                src_network = "G9"
            elif src_ip.startswith("172.16.21."):
                src_network = "G10"
            
            if dst_ip.startswith("192.168.10."):
                dst_network = "G9"
            elif dst_ip.startswith("172.16.21."):
                dst_network = "G10"

            # Traffic dalam gedung sama - ALLOWED
            if src_network == dst_network and src_network is not None:
                if not blocked:
                    self.logger.info(f"ALLOWED: Same building traffic dari {src_ip} ke {dst_ip}")

            # Traffic antar gedung - dengan batasan
            if src_network != dst_network and src_network is not None and dst_network is not None:
                # Hanya izinkan traffic antar gedung jika tidak ke zona sensitif
                if not (self.ip_in_subnet(dst_ip, ADMIN_G9_L2) or 
                        self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2)):
                    self.logger.info(f"ALLOWED: Inter-building traffic dari {src_ip} ke {dst_ip}")
                else:
                    if not blocked:
                        self.logger.info(f"*** BLOCKED: Inter-building traffic ke zona sensitif dari {src_ip} ke {dst_ip}")
                        blocked = True

            # AP-specific rules untuk Gedung G10
            AP_MAHASISWA_IPS = ["172.16.21.1", "172.16.21.19", "172.16.21.35"]
            AP_AULA_IPS = ["172.16.21.21"]
            
            is_mahasiswa_g10_ap = src_ip in AP_MAHASISWA_IPS
            is_aula_g10_ap = src_ip in AP_AULA_IPS

            # Rules untuk AP Mahasiswa Gedung G10
            if is_mahasiswa_g10_ap:
                if (self.ip_in_subnet(dst_ip, ADMIN_G9_L2) or 
                    self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2)):
                    self.logger.info(f"*** BLOCKED: Mahasiswa AP G10 tidak diizinkan akses zona sensitif dari {src_ip} ke {dst_ip}")
                    blocked = True
                else:
                    if not blocked:
                        self.logger.info(f"ALLOWED: Mahasiswa AP G10 mengakses {dst_ip} dari {src_ip}")

            # Rules untuk AP Aula Gedung G10
            if is_aula_g10_ap:
                if self.ip_in_subnet(dst_ip, PIMPINAN_G9_L2):
                    self.logger.info(f"*** BLOCKED: AP Aula tidak diizinkan akses zona Pimpinan dari {src_ip} ke {dst_ip}")
                    blocked = True
                else:
                    if not blocked:
                        self.logger.info(f"ALLOWED: AP Aula mengakses {dst_ip} dari {src_ip}")

        # --- END FIREWALL ---

        # Determine output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        # Tetap forward packet (blocked atau tidak)
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)