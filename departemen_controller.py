from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4

class MedicalSimpleController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MedicalSimpleController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        
        # DEFINISI ZONA BERDASARKAN IP ADDRESS (FLAT /24)
        
        self.zones = {
            # Mahasiswa: G9 AP Lt1 (.101, .102), G9 AP Lt3 (.103, .104), Aula (.105, .106)
            'MAHASISWA': [
                '10.0.0.101', '10.0.0.102', 
                '10.0.0.103', '10.0.0.104', 
                '10.0.0.105', '10.0.0.106'
            ],
            
            # Lab Komputer: Diperlakukan sama seperti Mahasiswa (Student Network)
            'LAB': [
                '10.0.0.51', '10.0.0.52', # Lab 1
                '10.0.0.53', '10.0.0.54', # Lab 2
                '10.0.0.55', '10.0.0.56'  # Lab 3
            ],
            
            # Secure: Keuangan, Admin, Pimpinan, Ujian
            'SECURE': [
                '10.0.0.11', '10.0.0.12', '10.0.0.13', '10.0.0.14', # Keuangan & Admin
                '10.0.0.21', '10.0.0.22', # Pimpinan
                '10.0.0.91', '10.0.0.92'  # Ujian
            ],
            
            # Dosen: G9 (.31, .32), G10 Lt2 (.33, .34), G10 Lt3 (.35, .36)
            'DOSEN': [
                '10.0.0.31', '10.0.0.32', 
                '10.0.0.33', '10.0.0.34', 
                '10.0.0.35', '10.0.0.36'
            ],
            
            # Sub-group khusus untuk rule spesifik
            'KEUANGAN':  ['10.0.0.11', '10.0.0.12', '10.0.0.13', '10.0.0.14'], 
            'DEKAN':     ['10.0.0.21', '10.0.0.22'],
            'UJIAN':     ['10.0.0.91', '10.0.0.92']
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
        if ip_addr in self.zones['LAB']:       return 'MAHASISWA' # Lab dianggap zona Mahasiswa
        if ip_addr in self.zones['SECURE']:    return 'SECURE'
        if ip_addr in self.zones['DOSEN']:     return 'DOSEN'
        return 'UNKNOWN'

    def check_security(self, src_ip, dst_ip):
        src_cat = self.get_zone_category(src_ip)
        dst_cat = self.get_zone_category(dst_ip)

        # RULE 1: Keuangan ke Dekan -> ALLOW (Izin Khusus Internal Secure)
        if src_ip in self.zones['KEUANGAN'] and dst_ip in self.zones['DEKAN']:
            return True, "ALLOW: Internal Report (Keuangan -> Dekan)"

        # RULE 2: Mahasiswa/Lab -> Secure (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'SECURE':
            return False, "BLOCK: Mahasiswa/Lab mencoba akses Zona Aman"

        # RULE 3: Mahasiswa/Lab -> Dosen (BLOCK)
        if src_cat == 'MAHASISWA' and dst_cat == 'DOSEN':
            return False, "BLOCK: Mahasiswa/Lab mencoba akses Dosen"

        # RULE 4: Dosen -> Ujian (BLOCK)
        if src_cat == 'DOSEN' and dst_ip in self.zones['UJIAN']:
            return False, "BLOCK: Dosen akses Server Ujian"

        return True, "ALLOW: Akses Diizinkan"

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

        # --- LOGIKA FIREWALL ---
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ipv4_pkt.src
            dst_ip = ipv4_pkt.dst
            
            allowed, reason = self.check_security(src_ip, dst_ip)
            
            if not allowed:
                self.logger.warning(f"{reason} | {src_ip} -> {dst_ip}")
                return # DROP (Paket dibuang, tidak diteruskan)
            else:
                self.logger.info(f"{reason} | {src_ip} -> {dst_ip}")

        # Standard L2 Switching (FLOOD / Forward)
        out_port = ofproto.OFPP_FLOOD
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            # FIX: Tambahkan eth_type agar flow rule spesifik (IPv6/ARP tidak meloloskan IPv4)
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=eth.ethertype)
            
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER: data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)