from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MedicalFinalTopo(Topo):
    def build(self):
        # ==========================================
        # CORE & DISTRIBUTION LAYER
        # ==========================================
        s_core = self.addSwitch('s1', dpid='0000000000000001')

        s_dist_g9 = self.addSwitch('s2', dpid='0000000000000002')
        s_dist_g10 = self.addSwitch('s3', dpid='0000000000000003')
        
        self.addLink(s_core, s_dist_g9)
        self.addLink(s_core, s_dist_g10)

        # ==========================================
        # GEDUNG G9
        # ==========================================
        
        # --- G9 LT 1 ---
        s_g9_lt1 = self.addSwitch('s4')
        self.addLink(s_dist_g9, s_g9_lt1)
        
        # Wireless (192.168.1.0/22) -> Gateway: 192.168.1.1
        h_mhs_wifi_1 = self.addHost('mhs_w1', ip='192.168.1.10/22', 
                                    defaultRoute='via 192.168.1.1')
        self.addLink(s_g9_lt1, h_mhs_wifi_1)
        
        # Kabel (192.168.10.0/27) -> Gateway: 192.168.10.1
        h_mhs_kabel_1 = self.addHost('mhs_k1', ip='192.168.10.2/27', 
                                     defaultRoute='via 192.168.10.1')
        self.addLink(s_g9_lt1, h_mhs_kabel_1)

        # --- G9 LT 2 ---
        # Subnet Kabel G9 Lt2: 192.168.10.32/26
        # Range Usable: .33 - .94
        # Gateway Virtual: 192.168.10.33 (IP Pertama)
        
        s_g9_lt2_agg = self.addSwitch('s5')
        self.addLink(s_dist_g9, s_g9_lt2_agg)

        # a. Keuangan (High)
        s_adm_keu = self.addSwitch('s6')
        self.addLink(s_g9_lt2_agg, s_adm_keu)
        
        # Host mulai dari .34 karena .33 dipakai Gateway
        h_keu_1 = self.addHost('keu_1', ip='192.168.10.34/26', defaultRoute='via 192.168.10.33')
        h_keu_2 = self.addHost('keu_2', ip='192.168.10.35/26', defaultRoute='via 192.168.10.33')
        self.addLink(s_adm_keu, h_keu_1)
        self.addLink(s_adm_keu, h_keu_2)

        # b. Pimpinan (Very High)
        s_pimpinan = self.addSwitch('s7')
        self.addLink(s_g9_lt2_agg, s_pimpinan)
        h_dekan = self.addHost('dekan', ip='192.168.10.50/26', defaultRoute='via 192.168.10.33')
        self.addLink(s_pimpinan, h_dekan)

        # c. Dosen G9 (Semi Trusted)
        s_dosen_g9 = self.addSwitch('s8')
        self.addLink(s_g9_lt2_agg, s_dosen_g9)
        h_dsn_g9 = self.addHost('dsn_g9', ip='192.168.10.70/26', defaultRoute='via 192.168.10.33')
        self.addLink(s_dosen_g9, h_dsn_g9)

        # d. Ujian (Isolated)
        s_ujian = self.addSwitch('s9')
        self.addLink(s_g9_lt2_agg, s_ujian)
        h_ujian = self.addHost('ujian', ip='192.168.10.90/26', defaultRoute='via 192.168.10.33')
        self.addLink(s_ujian, h_ujian)

        # --- G9 LT 3 ---
        s_g9_lt3 = self.addSwitch('s10')
        self.addLink(s_dist_g9, s_g9_lt3)
        
        # Lab (Kabel 192.168.10.96/25) -> Gateway: 192.168.10.97
        s_lab1 = self.addSwitch('s11')
        self.addLink(s_g9_lt3, s_lab1)
        h_lab = self.addHost('lab1', ip='192.168.10.100/25', defaultRoute='via 192.168.10.97')
        self.addLink(s_lab1, h_lab)
        
        # Wifi Lt 3 (192.168.6.0/22) -> Gateway: 192.168.6.1
        h_mhs_wifi_3 = self.addHost('mhs_w3', ip='192.168.6.10/22', 
                                    defaultRoute='via 192.168.6.1')
        self.addLink(s_g9_lt3, h_mhs_wifi_3)


        # ==========================================
        # GEDUNG G10
        # ==========================================

        # --- G10 LT 1 (Admin) ---
        # Kabel (172.16.21.0/28) -> Gateway: 172.16.21.1
        s_g10_lt1 = self.addSwitch('s14')
        self.addLink(s_dist_g10, s_g10_lt1)
        
        h_adm_g10 = self.addHost('adm_g10', ip='172.16.21.2/28', 
                                 defaultRoute='via 172.16.21.1')
        self.addLink(s_g10_lt1, h_adm_g10)

        # --- G10 LT 2 (Dosen & Aula) ---
        s_g10_lt2 = self.addSwitch('s15')
        self.addLink(s_dist_g10, s_g10_lt2)
        
        # Dosen Kabel (172.16.21.16/29) -> Gateway: 172.16.21.17
        h_dsn_g10_2 = self.addHost('dsn_g10_2', ip='172.16.21.18/29', 
                                   defaultRoute='via 172.16.21.17')
        
        # Aula Wireless (172.16.20.64/25) -> Gateway: 172.16.20.65
        h_aula_wifi = self.addHost('aula', ip='172.16.20.70/25', 
                                   defaultRoute='via 172.16.20.65')
                                   
        self.addLink(s_g10_lt2, h_dsn_g10_2)
        self.addLink(s_g10_lt2, h_aula_wifi)

        # --- G10 LT 3 (Dosen) ---
        # Kabel (172.16.21.32/26) -> Gateway: 172.16.21.33
        s_g10_lt3 = self.addSwitch('s16')
        self.addLink(s_dist_g10, s_g10_lt3)
        
        h_dsn_g10_3 = self.addHost('dsn_g10_3', ip='172.16.21.35/26', 
                                   defaultRoute='via 172.16.21.33')
        self.addLink(s_g10_lt3, h_dsn_g10_3)

def run():
    topo = MedicalFinalTopo()
    # Menggunakan remote controller, autoSetMacs untuk kemudahan
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    print("[+] Topology Started with Full defaultRoute configuration.")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()