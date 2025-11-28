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
        # VLAN mapping untuk floor identification
        self.vlan_map = {
            91: 'G9-L1',   # Gedung 9 Lantai 1
            92: 'G9-L2',   # Gedung 9 Lantai 2
            93: 'G9-L3',   # Gedung 9 Lantai 3
            101: 'G10-L1', # Gedung 10 Lantai 1
            102: 'G10-L2', # Gedung 10 Lantai 2
            103: 'G10-L3'  # Gedung 10 Lantai 3
        }

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

        # ====== VLAN DETECTION ======
        vlan_id = self._detect_vlan(dpid, in_port)
        vlan_zone = self.vlan_map.get(vlan_id, 'UNKNOWN')

        self.logger.info(f"Packet dari {src} (VLAN {vlan_id}: {vlan_zone}) ke {dst}")

        # --- LOGIKA FIREWALL BERDASARKAN VLAN & ZONA SENSITIVITAS ---
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # ====== VLAN-BASED SECURITY POLICY ======
            if not self._check_vlan_security(vlan_id, vlan_zone, src_ip, dst_ip):
                self.logger.warning(f"BLOCKED: Akses tidak diizinkan dari VLAN {vlan_id} ke zone tujuan")
                return

            # ====== APPLY FIREWALL RULES WITH VLAN CONTEXT ======
            self._apply_vlan_firewall_rules(vlan_id, vlan_zone, src_ip, dst_ip)

        # --- END FIREWALL ---

        # Learning switch logic
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

    def _detect_vlan(self, dpid, in_port):
        """Detect VLAN based on switch DPID and port"""
        # Core switch (DPID 1) - Mapping VLAN berdasarkan port
        if dpid == 1:
            port_vlan_map = {
                1: 91,   # G9 L1
                2: 92,   # G9 L2
                3: 93,   # G9 L3
                4: 101,  # G10 L1
                5: 102,  # G10 L2
                6: 103   # G10 L3
            }
            return port_vlan_map.get(in_port, 0)

        # Building switches (DPID 2-3) - Detect based on connected floor
        elif dpid == 2:  # G9 switch
            building_ports = {2: 91, 3: 92, 4: 93}  # L1, L2, L3
            return building_ports.get(in_port, 0)
        elif dpid == 3:  # G10 switch
            building_ports = {2: 101, 3: 102, 4: 103}  # L1, L2, L3
            return building_ports.get(in_port, 0)

        # Floor switches (DPID 4-9) - Return specific VLAN
        floor_vlans = {
            4: 91,   5: 92,   6: 93,   # G9 L1, L2, L3
            7: 101,  8: 102,  9: 103    # G10 L1, L2, L3
        }
        return floor_vlans.get(dpid, 0)

    def _check_vlan_security(self, vlan_id, vlan_zone, src_ip, dst_ip):
        """VLAN-based security policy check sesuai zona baru"""
        dst_vlan_id = self._get_vlan_by_ip(dst_ip)

        # === GEDUNG 9 - LANTAI 2 (VLAN 92) - 4 ZONA ===
        if vlan_id == 92:  # G9 L2
            # Zona 1: Administrasi & Keuangan (HIGH-SENSITIVITY)
            # IP: 192.168.10.33-38
            if dst_ip.startswith('192.168.10.3') and int(dst_ip.split('.')[-1]) in [33, 34, 35, 36, 37, 38]:
                if not (src_ip.startswith('192.168.10.39') or src_ip.startswith('192.168.10.4') or src_ip.startswith('192.168.10.44')):
                    self.logger.warning(f"G9 L2: Admin zone access denied from {src_ip} to {dst_ip}")
                    return False

            # Zona 2: Pimpinan & Sekretariat (VERY HIGH-SENSITIVITY)
            # IP: 192.168.10.39-43
            elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [39, 40, 41, 42, 43]:
                if not (src_ip.startswith('192.168.10.3') and int(src_ip.split('.')[-1]) in [33, 34, 35, 36, 37, 38]):
                    self.logger.warning(f"G9 L2: Pimpinan zone access denied from {src_ip} to {dst_ip}")
                    return False

            # Zona 3: Dosen (SEMI-TRUSTED)
            # IP: 192.168.10.44-46
            elif dst_ip.startswith('192.168.10.44') or dst_ip.startswith('192.168.10.45') or dst_ip.startswith('192.168.10.46'):
                # Dosen bisa akses dari zona semi-trusted yang sama
                pass  # Allow

            # Zona 4: Ujian / Assessment (CONTROLLED & ISOLATED)
            # IP: 192.168.10.47-50
            elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [47, 48]:
                if vlan_id in [91, 93]:  # L1 atau L3 (mahasiswa zone)
                    self.logger.warning(f"G9 L2: Ujian zone blocked from student VLAN {vlan_id}")
                    return False
                # Mahasiswa di zona ujian hanya bisa akses server ujian
                if src_ip.startswith('192.168.10.49') or src_ip.startswith('192.168.10.50'):
                    pass  # Allow mahasiswa dalam zona ujian
                else:
                    self.logger.warning(f"G9 L2: Ujian zone access denied from outside {src_ip}")
                    return False

        # === GEDUNG 9 - LANTAI 1 & 3 (MAHASISWA ZONES - VLAN 91 & 93) ===
        elif vlan_id in [91, 93]:  # G9 L1 & L3
            # Blokir akses ke zona sensitif G9 L2
            if dst_ip.startswith('192.168.10.3') and int(dst_ip.split('.')[-1]) in [33, 34, 35, 36, 37, 38]:  # Admin zone
                self.logger.warning(f"G9 L1/L3: Admin zone access denied from {src_ip}")
                return False
            elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [39, 40, 41, 42, 43]:  # Pimpinan zone
                self.logger.warning(f"G9 L1/L3: Pimpinan zone access denied from {src_ip}")
                return False
            elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [47, 48]:  # Ujian zone
                self.logger.warning(f"G9 L1/L3: Ujian zone access denied from {src_ip}")
                return False

        # === GEDUNG 10 - LANTAI 1 (VLAN 101) - ADMIN ZONE ===
        elif vlan_id == 101:  # G10 L1
            # Administrasi & Keuangan (HIGH-SENSITIVITY)
            if dst_ip.startswith('172.16.21.1'):  # G10 L1 admin
                # Hanya izinkan dari zona semi-trusted
                if not (src_ip.startswith('172.16.21.1') or src_ip.startswith('172.16.21.3')):
                    self.logger.warning(f"G10 L1: Admin zone access denied from {src_ip}")
                    return False

        # === GEDUNG 10 - LANTAI 2 & 3 (VLAN 102 & 103) - DOSEN ZONES ===
        elif vlan_id in [102, 103]:  # G10 L2 & L3
            # Dosen zones semi-trusted, izinkan akses ke zona mahasiswa untuk monitoring
            if dst_vlan_id in [91, 93]:  # G9 L1/L3 mahasiswa zones
                pass  # Allow untuk monitoring
            elif dst_ip.startswith('172.16.21.1'):  # G10 L1 admin
                self.logger.warning(f"G10 L2/L3: Admin zone access denied from {src_ip}")
                return False

        # === INTER-VLAN COMMUNICATION RESTRICTIONS ===
        if vlan_id != dst_vlan_id and dst_vlan_id != 0:
            if self._is_allowed_inter_vlan(vlan_id, dst_vlan_id, src_ip, dst_ip):
                self.logger.info(f"ALLOWED: Special inter-VLAN access from {vlan_zone} to VLAN {dst_vlan_id}")
                return True
            else:
                self.logger.warning(f"BLOCKED: Inter-VLAN communication from VLAN {vlan_id} to VLAN {dst_vlan_id}")
                return False

        return True

    def _get_vlan_by_ip(self, ip):
        """Get VLAN ID based on IP address sesuai skema baru"""
        # Gedung G9
        if ip.startswith('192.168.1.'): return 91      # G9 L1 Nirkabel
        elif ip.startswith('192.168.10.'): return 91    # G9 L1 Kabel
        elif ip.startswith('192.168.5.'): return 92     # G9 L2 Nirkabel
        elif ip.startswith('192.168.10.3'): return 92  # G9 L2 Kabel
        elif ip.startswith('192.168.10.4'): return 92  # G9 L2 Kabel
        elif ip.startswith('192.168.6.'): return 93      # G9 L3 Nirkabel
        elif ip.startswith('192.168.10.9'): return 93  # G9 L3 Kabel
        elif ip.startswith('192.168.10.10'): return 93 # G9 L3 Kabel

        # Gedung G10
        elif ip.startswith('172.16.20.0'): return 101   # G10 L1 Nirkabel
        elif ip.startswith('172.16.21.0'): return 101  # G10 L1 Kabel
        elif ip.startswith('172.16.20.6'): return 102  # G10 L2 Nirkabel
        elif ip.startswith('172.16.21.1'): return 102  # G10 L2 Kabel
        elif ip.startswith('172.16.20.19'): return 103 # G10 L3 Nirkabel
        elif ip.startswith('172.16.21.3'): return 103  # G10 L3 Kabel

        return 0

    def _is_allowed_inter_vlan(self, src_vlan, dst_vlan, src_ip, dst_ip):
        """Check if inter-VLAN communication is allowed"""
        # G9 L3 (VLAN 93) ke G9 L2 (VLAN 92) untuk presentasi
        if src_vlan == 93 and dst_vlan == 92:
            if src_ip.startswith('192.168.6.'):  # AP L3 untuk presentasi
                return True

        # G10 L2 (VLAN 102) ke G9 zones untuk event khusus
        if src_vlan == 102 and dst_vlan in [91, 92, 93]:
            if src_ip.startswith('172.16.20.65'):  # AP L2 untuk event
                return True

        # Dosen zones ke mahasiswa zones untuk monitoring
        if src_vlan in [92, 102] and dst_vlan in [91, 93]:
            return True

        return False

    def _apply_vlan_firewall_rules(self, vlan_id, vlan_zone, src_ip, dst_ip):
        """Apply VLAN-based firewall rules"""
        self.logger.info(f"ALLOWED: Traffic dari {src_ip} (VLAN {vlan_id}) ke {dst_ip}")

        # Log khusus untuk zona sensitif
        if dst_ip.startswith('192.168.10.3') and int(dst_ip.split('.')[-1]) in [33, 34, 35, 36, 37, 38]:
            self.logger.info(f"HIGH-SENSITIVITY: Admin zone access from {vlan_zone}")
        elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [39, 40, 41, 42, 43]:
            self.logger.info(f"VERY HIGH-SENSITIVITY: Pimpinan zone access from {vlan_zone}")
        elif dst_ip.startswith('192.168.10.4') and int(dst_ip.split('.')[-1]) in [47, 48]:
            self.logger.info(f"CONTROLLED: Ujian zone access from {vlan_zone}")
        elif dst_ip.startswith('172.16.20.65'):  # AP G10 L2
            self.logger.info(f"SPECIAL ACCESS: AP G10 L2 communication from {vlan_zone}")