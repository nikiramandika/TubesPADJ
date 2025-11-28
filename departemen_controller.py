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

    def ip_in_subnet(self, ip_str, subnet_str):
        """Check if IP is in subnet"""
        try:
            return ipaddress.ip_address(ip_str) in ipaddress.ip_network(subnet_str, strict=False)
        except:
            return False

    def check_firewall_rules(self, src_ip, dst_ip):
        """
        Return: True if ALLOWED, False if BLOCKED
        """
        # VERY HIGH-SENSITIVITY (Pimpinan & Sekretariat - 192.168.10.52/26)
        if self.ip_in_subnet(dst_ip, "192.168.10.52/26"):
            # Hanya Admin & Pimpinan sendiri
            if (self.ip_in_subnet(src_ip, "192.168.10.32/26") or 
                self.ip_in_subnet(src_ip, "192.168.10.52/26")):
                return True
            else:
                self.logger.info(f"BLOCKED: Akses tidak diizinkan ke Zona Pimpinan dari {src_ip}")
                return False

        # HIGH-SENSITIVITY (Administrasi & Keuangan - 192.168.10.42/26)
        if self.ip_in_subnet(dst_ip, "192.168.10.42/26"):
            if (self.ip_in_subnet(src_ip, "192.168.10.42/26") or 
                self.ip_in_subnet(src_ip, "192.168.10.52/26")):
                return True
            else:
                self.logger.info(f"BLOCKED: Akses tidak diizinkan ke Zona Admin dari {src_ip}")
                return False

        # CONTROLLED & ISOLATED (Ujian - 192.168.10.62/26)
        if self.ip_in_subnet(dst_ip, "192.168.10.62/26"):
            # Hanya Dosen dan zona ujian
            if (self.ip_in_subnet(src_ip, "192.168.10.32/26") or 
                self.ip_in_subnet(src_ip, "192.168.10.62/26")):
                return True
            else:
                self.logger.info(f"BLOCKED: Mahasiswa tidak boleh akses Zona Ujian dari {src_ip}")
                return False

        # Mahasiswa ke zona sensitif
        if (self.ip_in_subnet(src_ip, "192.168.10.0/27") or 
            self.ip_in_subnet(src_ip, "192.168.10.96/25") or
            self.ip_in_subnet(src_ip, "172.16.21.0/28")):
            if (self.ip_in_subnet(dst_ip, "192.168.10.42/26") or 
                self.ip_in_subnet(dst_ip, "192.168.10.52/26")):
                self.logger.info(f"BLOCKED: Mahasiswa/Lab tidak boleh akses zona sensitif dari {src_ip} ke {dst_ip}")
                return False

        # AP di G10 ke zona sensitif G9
        if (self.ip_in_subnet(src_ip, "172.16.21.19/29") or
            self.ip_in_subnet(src_ip, "172.16.21.35/26") or
            self.ip_in_subnet(src_ip, "172.16.21.21/29")):
            if (self.ip_in_subnet(dst_ip, "192.168.10.52/26") or
                self.ip_in_subnet(dst_ip, "192.168.10.42/26")):
                self.logger.info(f"BLOCKED: AP G10 tidak boleh akses zona sensitif G9 dari {src_ip}")
                return False

        # Default ALLOW untuk traffic yang tidak masuk rule blocking
        self.logger.info(f"ALLOWED: Traffic dari {src_ip} ke {dst_ip}")
        return True

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

        # Cek firewall rules jika ada IP packet
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            
            if not self.check_firewall_rules(src_ip, dst_ip):
                # Jika di-block, jangan forward
                return

        # Learning switch behavior - forward packet
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