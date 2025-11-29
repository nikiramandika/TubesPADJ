from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MedicalSimpleTopo(Topo):
    def build(self):
        # CORE & DISTRIBUTION
        s_core = self.addSwitch('s1', dpid='0000000000000001')
        s_dist_g9 = self.addSwitch('s2', dpid='0000000000000002')
        s_dist_g10 = self.addSwitch('s3', dpid='0000000000000003')
        
        self.addLink(s_core, s_dist_g9)
        self.addLink(s_core, s_dist_g10)

        # ================= GEDUNG G9 =================
        
        # --- G9 Lantai 1 (Access Point Mahasiswa) ---
        s_g9_lt1 = self.addSwitch('s4') 
        self.addLink(s_dist_g9, s_g9_lt1)
        
        h_mhs_wifi_1 = self.addHost('mhs1', ip='10.0.0.101/24')
        h_mhs_wifi_2 = self.addHost('mhs2', ip='10.0.0.102/24')
        self.addLink(s_g9_lt1, h_mhs_wifi_1)
        self.addLink(s_g9_lt1, h_mhs_wifi_2)

        # --- G9 Lantai 2 (Area Campuran) ---
        s_g9_lt2_agg = self.addSwitch('s5')
        self.addLink(s_dist_g9, s_g9_lt2_agg)

        # Keuangan
        s_adm_keu = self.addSwitch('s6')
        self.addLink(s_g9_lt2_agg, s_adm_keu)
        h_keu_1 = self.addHost('keu1', ip='10.0.0.11/24')
        h_keu_2 = self.addHost('keu2', ip='10.0.0.12/24')
        self.addLink(s_adm_keu, h_keu_1)
        self.addLink(s_adm_keu, h_keu_2)

        # Pimpinan
        s_pimpinan = self.addSwitch('s7')
        self.addLink(s_g9_lt2_agg, s_pimpinan)
        h_dekan = self.addHost('dekan', ip='10.0.0.21/24')
        h_sekre = self.addHost('sekre', ip='10.0.0.22/24')
        self.addLink(s_pimpinan, h_dekan)
        self.addLink(s_pimpinan, h_sekre)

        # Dosen Gedung G9
        s_dosen_g9 = self.addSwitch('s8')
        self.addLink(s_g9_lt2_agg, s_dosen_g9)
        h_dsn_g9_1 = self.addHost('dsn9a', ip='10.0.0.31/24')
        h_dsn_g9_2 = self.addHost('dsn9b', ip='10.0.0.32/24')
        self.addLink(s_dosen_g9, h_dsn_g9_1)
        self.addLink(s_dosen_g9, h_dsn_g9_2)

        # R.Ujian
        s_ujian = self.addSwitch('s9')
        self.addLink(s_g9_lt2_agg, s_ujian)
        h_ujian_1 = self.addHost('ujian1', ip='10.0.0.91/24')
        h_ujian_2 = self.addHost('ujian2', ip='10.0.0.92/24')
        self.addLink(s_ujian, h_ujian_1)
        self.addLink(s_ujian, h_ujian_2)

        # --- G9 Lantai 3 (Lab & AP Mahasiswa) ---
        # Switch Utama Lantai 3
        s_g9_lt3_main = self.addSwitch('s10')
        self.addLink(s_dist_g9, s_g9_lt3_main)

        # Lab 1 
        s_lab1 = self.addSwitch('s11')
        self.addLink(s_g9_lt3_main, s_lab1)
        h_lab1_a = self.addHost('lab1a', ip='10.0.0.51/24')
        h_lab1_b = self.addHost('lab1b', ip='10.0.0.52/24')
        self.addLink(s_lab1, h_lab1_a)
        self.addLink(s_lab1, h_lab1_b)

        # Lab 2 
        s_lab2 = self.addSwitch('s12')
        self.addLink(s_g9_lt3_main, s_lab2)
        h_lab2_a = self.addHost('lab2a', ip='10.0.0.53/24')
        h_lab2_b = self.addHost('lab2b', ip='10.0.0.54/24')
        self.addLink(s_lab2, h_lab2_a)
        self.addLink(s_lab2, h_lab2_b)

        # Lab 3 
        s_lab3 = self.addSwitch('s13')
        self.addLink(s_g9_lt3_main, s_lab3)
        h_lab3_a = self.addHost('lab3a', ip='10.0.0.55/24')
        h_lab3_b = self.addHost('lab3b', ip='10.0.0.56/24')
        self.addLink(s_lab3, h_lab3_a)
        self.addLink(s_lab3, h_lab3_b)

        # Access Point Mahasiswa Lt3
        h_mhs_3a = self.addHost('mhs3a', ip='10.0.0.103/24')
        h_mhs_3b = self.addHost('mhs3b', ip='10.0.0.104/24')
        self.addLink(s_g9_lt3_main, h_mhs_3a)
        self.addLink(s_g9_lt3_main, h_mhs_3b)


        # ================= GEDUNG G10 =================
        
        # Administrasi G10
        s_g10_lt1 = self.addSwitch('s14')
        self.addLink(s_dist_g10, s_g10_lt1)
        h_adm_g10_1 = self.addHost('adm10a', ip='10.0.0.13/24')
        h_adm_g10_2 = self.addHost('adm10b', ip='10.0.0.14/24')
        self.addLink(s_g10_lt1, h_adm_g10_1)
        self.addLink(s_g10_lt1, h_adm_g10_2)

        # Dosen G10 Lt2 & Aula
        s_g10_lt2 = self.addSwitch('s15')
        self.addLink(s_dist_g10, s_g10_lt2)
        h_dsn_10a_1 = self.addHost('dsn10a1', ip='10.0.0.33/24')
        h_dsn_10a_2 = self.addHost('dsn10a2', ip='10.0.0.34/24')
        h_aula_1 = self.addHost('aula1', ip='10.0.0.105/24')
        h_aula_2 = self.addHost('aula2', ip='10.0.0.106/24')
        self.addLink(s_g10_lt2, h_dsn_10a_1)
        self.addLink(s_g10_lt2, h_dsn_10a_2)
        self.addLink(s_g10_lt2, h_aula_1)
        self.addLink(s_g10_lt2, h_aula_2)

        # Dosen G10 Lt3
        s_g10_lt3 = self.addSwitch('s16')
        self.addLink(s_dist_g10, s_g10_lt3)
        h_dsn_10b_1 = self.addHost('dsn10b1', ip='10.0.0.35/24')
        h_dsn_10b_2 = self.addHost('dsn10b2', ip='10.0.0.36/24')
        self.addLink(s_g10_lt3, h_dsn_10b_1)
        self.addLink(s_g10_lt3, h_dsn_10b_2)

def run():
    topo = MedicalSimpleTopo()
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()