from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MedicalTopo2Host(Topo):
    def build(self):
        # ==========================================
        # 1. CORE LAYER
        # ==========================================
        s_core = self.addSwitch('s1', dpid='0000000000000001')

        # ==========================================
        # 2. DISTRIBUTION LAYER
        # ==========================================
        s_dist_g9 = self.addSwitch('s2', dpid='0000000000000002')
        s_dist_g10 = self.addSwitch('s3', dpid='0000000000000003')

        self.addLink(s_core, s_dist_g9)
        self.addLink(s_core, s_dist_g10)

        # ==========================================
        # 3. GEDUNG G9 (KIRI)
        # ==========================================
        
        # --- G9 Lantai 1 (Mahasiswa) ---
        s_g9_lt1 = self.addSwitch('s4')
        self.addLink(s_dist_g9, s_g9_lt1)
        
        # 2 Host Mahasiswa (Zone Public: 10.0.99.x)
        h_mhs_g9_1 = self.addHost('mhs_g9_1', ip='10.0.99.10/24')
        h_mhs_g9_2 = self.addHost('mhs_g9_2', ip='10.0.99.11/24')
        self.addLink(s_g9_lt1, h_mhs_g9_1)
        self.addLink(s_g9_lt1, h_mhs_g9_2)

        # --- G9 Lantai 2 (Complex Zones) ---
        s_g9_lt2_agg = self.addSwitch('s5') # Aggregator Switch4
        self.addLink(s_dist_g9, s_g9_lt2_agg)

        # a. Switch Adm & Keuangan (Zone High: 10.0.10.x)
        s_adm_keu = self.addSwitch('s6')
        self.addLink(s_g9_lt2_agg, s_adm_keu)
        
        h_keu_1 = self.addHost('keu_1', ip='10.0.10.10/24')
        h_keu_2 = self.addHost('keu_2', ip='10.0.10.11/24')
        self.addLink(s_adm_keu, h_keu_1)
        self.addLink(s_adm_keu, h_keu_2)

        # b. Switch Pimpinan (Zone Very High: 10.0.20.x)
        s_pimpinan = self.addSwitch('s7')
        self.addLink(s_g9_lt2_agg, s_pimpinan)
        
        h_dekan = self.addHost('dekan', ip='10.0.20.10/24')
        h_sekre = self.addHost('sekre', ip='10.0.20.11/24')
        self.addLink(s_pimpinan, h_dekan)
        self.addLink(s_pimpinan, h_sekre)

        # c. Switch Dosen G9 (Zone Semi: 10.0.30.x)
        s_dosen_g9 = self.addSwitch('s8')
        self.addLink(s_g9_lt2_agg, s_dosen_g9)
        
        h_dsn_g9_1 = self.addHost('dsn_g9_1', ip='10.0.30.10/24')
        h_dsn_g9_2 = self.addHost('dsn_g9_2', ip='10.0.30.11/24')
        self.addLink(s_dosen_g9, h_dsn_g9_1)
        self.addLink(s_dosen_g9, h_dsn_g9_2)

        # d. Switch Ujian (Zone Isolated: 10.0.40.x)
        s_ujian = self.addSwitch('s9')
        self.addLink(s_g9_lt2_agg, s_ujian)
        
        h_ujian_1 = self.addHost('ujian_1', ip='10.0.40.10/24')
        h_ujian_2 = self.addHost('ujian_2', ip='10.0.40.11/24')
        self.addLink(s_ujian, h_ujian_1)
        self.addLink(s_ujian, h_ujian_2)

        # --- G9 Lantai 3 (Labs) ---
        s_g9_lt3 = self.addSwitch('s10')
        self.addLink(s_dist_g9, s_g9_lt3)

        # Lab 1 (Zone Lab: 10.0.50.x)
        s_lab1 = self.addSwitch('s11')
        self.addLink(s_g9_lt3, s_lab1)
        
        h_lab1_1 = self.addHost('lab1_1', ip='10.0.50.10/24')
        h_lab1_2 = self.addHost('lab1_2', ip='10.0.50.11/24')
        self.addLink(s_lab1, h_lab1_1)
        self.addLink(s_lab1, h_lab1_2)

        # Kita skip switch lab 2/3 agar tidak terlalu penuh, tapi Access Point Mahasiswa ada di sini
        # Access Point Wireless G9 Lt3 (Zone Public: 10.0.99.x)
        h_mhs_g9_3_1 = self.addHost('mhs_g9_3a', ip='10.0.99.12/24')
        h_mhs_g9_3_2 = self.addHost('mhs_g9_3b', ip='10.0.99.13/24')
        self.addLink(s_g9_lt3, h_mhs_g9_3_1)
        self.addLink(s_g9_lt3, h_mhs_g9_3_2)

        # ==========================================
        # 4. GEDUNG G10 (KANAN)
        # ==========================================
        
        # --- G10 Lantai 1 (Admin) ---
        s_g10_lt1 = self.addSwitch('s14')
        self.addLink(s_dist_g10, s_g10_lt1)
        
        # Admin G10 (Zone High: 10.0.10.x) - Terhubung Logic dgn Keuangan G9
        h_adm_g10_1 = self.addHost('adm_g10_1', ip='10.0.10.20/24')
        h_adm_g10_2 = self.addHost('adm_g10_2', ip='10.0.10.21/24')
        self.addLink(s_g10_lt1, h_adm_g10_1)
        self.addLink(s_g10_lt1, h_adm_g10_2)

        # --- G10 Lantai 2 (Dosen & Aula) ---
        s_g10_lt2 = self.addSwitch('s15')
        self.addLink(s_dist_g10, s_g10_lt2)
        
        # Dosen G10 (Zone Semi: 10.0.30.x)
        h_dsn_g10_1 = self.addHost('dsn_g10_1', ip='10.0.30.20/24')
        h_dsn_g10_2 = self.addHost('dsn_g10_2', ip='10.0.30.21/24')
        self.addLink(s_g10_lt2, h_dsn_g10_1)
        self.addLink(s_g10_lt2, h_dsn_g10_2)
        
        # Aula (Zone Public: 10.0.99.x)
        h_aula_1 = self.addHost('aula_1', ip='10.0.99.20/24')
        h_aula_2 = self.addHost('aula_2', ip='10.0.99.21/24')
        self.addLink(s_g10_lt2, h_aula_1)
        self.addLink(s_g10_lt2, h_aula_2)

        # --- G10 Lantai 3 (Dosen) ---
        s_g10_lt3 = self.addSwitch('s16')
        self.addLink(s_dist_g10, s_g10_lt3)
        
        # Dosen G10 Lt3 (Zone Semi: 10.0.30.x)
        h_dsn_g10_3a = self.addHost('dsn_g10_3a', ip='10.0.30.30/24')
        h_dsn_g10_3b = self.addHost('dsn_g10_3b', ip='10.0.30.31/24')
        self.addLink(s_g10_lt3, h_dsn_g10_3a)
        self.addLink(s_g10_lt3, h_dsn_g10_3b)

def run():
    topo = MedicalTopo2Host()
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    print("[+] Topology Started: 2 Hosts per Zone.")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()