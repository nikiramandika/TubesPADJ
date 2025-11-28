import ipaddress
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, arp

class MedicalACLController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(MedicalACLController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

        # DEFINISI ZONA IP (DENGAN STRICT=FALSE AGAR TIDAK ERROR)
        self.zones = {
            # 192.168.1.0/22 sebenarnya start di 0.0, jadi butuh strict=False
            'MHS_G9_WIFI_L1': ipaddress.ip_network('192.168.1.0/22', strict=False),
            
            'MHS_G9_KABEL_L1': ipaddress.ip_network('192.168.10.0/27', strict=False),
            
            # 192.168.6.0/22 sebenarnya start di 4.0, jadi butuh strict=False
            'MHS_G9_WIFI_L3': ipaddress.ip_network('192.168.6.0/22', strict=False),
            
            'LAB_G9_L3':      ipaddress.ip_network('192.168.10.96/25', strict=False),
            'AULA_WIFI':      ipaddress.ip_network('172.16.20.64/25', strict=False),
            
            # Area Sensitif (List Host Spesifik - Tidak perlu strict=False karena ini ip_address)
            'G9_KEUANGAN':    [ipaddress.ip_address('192.168.10.33'), ipaddress.ip_address('192.168.10.34')],
            'G9_DEKAN':       [ipaddress.ip_address('192.168.10.50')],
            'G9_UJIAN':       [ipaddress.ip_address('192.168.10.90')],
            'G9_DOSEN':       [ipaddress.ip_address('192.168.10.70')],
            
            'G10_ADMIN':      ipaddress.ip_network('172.16.21.0/28', strict=False),
            'G10_DOSEN_L2':   ipaddress.ip_network('172.16.21.16/29', strict=False),
            
            # 172.16.21.32 bukan awal blok /26 (awal bloknya 0), jadi butuh strict=False
            'G10_DOSEN_L3':   ipaddress.ip_network('172.16.21.32/26', strict=False)
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

    # Fungsi untuk cek apakah IP ada dalam list/network tertentu
    def is_in_zone(self, ip_str, zone_key):
        ip = ipaddress.ip_address(ip_str)
        target = self.zones[zone_key]
        
        # Jika target adalah List IP (Spesifik host)
        if isinstance(target, list):
            return ip in target
        # Jika target adalah Network Subnet
        else:
            return ip in target

    def check_security(self, src_ip, dst_ip):
        # LOGIKA KEAMANAN / FIREWALL (REVISED ORDER)
        # PRINSIP: Cek Izin Khusus (Whitelist) DULU, baru Cek Larangan (Blacklist)

        # 1. IZIN KHUSUS: KEUANGAN KE DEKAN (WHITELIST)
        # Aturan ini harus paling atas agar tidak kena blokir aturan Mahasiswa
        if self.is_in_zone(src_ip, 'G9_KEUANGAN') and self.is_in_zone(dst_ip, 'G9_DEKAN'):
             return True, "ALLOW: Keuangan to Dekan (Special Access)"

        # 2. BLOKIR MAHASISWA/PUBLIC KE KEUANGAN/DEKAN/ADMIN (BLACKLIST)
        mhs_zones = ['MHS_G9_WIFI_L1', 'MHS_G9_KABEL_L1', 'MHS_G9_WIFI_L3', 'AULA_WIFI', 'LAB_G9_L3']
        secure_zones = ['G9_KEUANGAN', 'G9_DEKAN', 'G10_ADMIN']
        
        is_src_mhs = any(self.is_in_zone(src_ip, z) for z in mhs_zones)
        is_dst_secure = any(self.is_in_zone(dst_ip, z) for z in secure_zones)
        
        if is_src_mhs and is_dst_secure:
            return False, "BLOCK: Mahasiswa to Secure Zone"

        # 3. BLOKIR ANTAR DEPARTEMEN SENSITIF LAINNYA
        # Contoh: Dosen G9 tidak boleh akses Server Ujian
        if self.is_in_zone(src_ip, 'G9_DOSEN') and self.is_in_zone(dst_ip, 'G9_UJIAN'):
            return False, "BLOCK: Dosen to Ujian"

        # 4. Default: ALLOW jika tidak ada rule blokir
        return True, "ALLOW: Default"
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

        # --- SECURITY CHECK ---
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst
            
            allowed, reason = self.check_security(src_ip, dst_ip)
            
            if not allowed:
                self.logger.warning(f"SECURITY: {src_ip} -> {dst_ip} : {reason}")
                return # DROP PACKET
            else:
                self.logger.info(f"TRAFFIC: {src_ip} -> {dst_ip} : {reason}")

        # L2 Switching standard
        out_port = ofproto.OFPP_FLOOD
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)