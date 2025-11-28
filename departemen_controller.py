from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4, arp # TAMBAHKAN ARP
from ryu.lib.packet import ether_types
import ipaddress

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
        
        # LOG INI PENTING UNTUK MENANDAKAN KONEKSI BERHASIL
        self.logger.info(f"*** Switch Terhubung: {datapath.id} ***")

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def is_in_subnet(self, ip_str, subnet_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            net = ipaddress.ip_network(subnet_str, strict=False)
            return ip in net
        except ValueError:
            return False

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

        # --- LOGIKA FIREWALL ---
        
        # 1. IZINKAN ARP (Sangat Penting agar Ping bisa jalan)
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            # ARP diperbolehkan lewat agar host bisa saling kenal MAC Address
            # Lanjut ke logika switching di bawah
            pass 
            
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            
            # CEK LOGIKA BLOCKING
            
            # Blokir akses ke Pimpinan (High Security)
            if self.is_in_subnet(dst_ip, "192.168.10.52/30") or dst_ip in ['192.168.10.53', '192.168.10.54']: 
                # Hanya boleh dari Admin (.43, .44) atau sesama Pimpinan
                if not (self.is_in_subnet(src_ip, "192.168.10.42/26") or self.is_in_subnet(src_ip, "192.168.10.52/26")):
                    self.logger.info(f"BLOCKED: {src_ip} mencoba akses PIMPINAN {dst_ip}")
                    return # DROP

            # Blokir akses ke Admin
            if self.is_in_subnet(dst_ip, "192.168.10.42/28"): 
                if not (self.is_in_subnet(src_ip, "192.168.10.42/26") or self.is_in_subnet(src_ip, "192.168.10.52/26")):
                    self.logger.info(f"BLOCKED: {src_ip} mencoba akses ADMIN {dst_ip}")
                    return # DROP

            # Blokir Mahasiswa Masuk Zona Ujian
            if self.is_in_subnet(dst_ip, "192.168.10.62/28"): 
                # Cek IP Mahasiswa (G9 dan G10)
                mahasiswa_subnets = ["192.168.10.0/27", "192.168.10.159/25", "172.16.21.0/28", "172.16.21.19/29", "172.16.21.35/26"]
                if any(self.is_in_subnet(src_ip, net) for net in mahasiswa_subnets):
                    self.logger.info(f"BLOCKED: Mahasiswa {src_ip} dilarang akses ZONA UJIAN")
                    return # DROP
                    
            # Jika lolos semua filter di atas, kita log allowed (opsional)
            # self.logger.info(f"ALLOWED: {src_ip} -> {dst_ip}")

        # --- END FIREWALL ---

        # L2 Switching Logic (Normal Forwarding)
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