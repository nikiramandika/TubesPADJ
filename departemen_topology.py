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

        # G9 Lt1 Nirkabel: 192.168.1.0/22 (subnet mask 255.255.252.0)
        h_mhs_wifi_1 = self.addHost('mhs1', ip='192.168.1.10/22')
        h_mhs_wifi_2 = self.addHost('mhs2', ip='192.168.1.11/22')
        self.addLink(s_g9_lt1, h_mhs_wifi_1)
        self.addLink(s_g9_lt1, h_mhs_wifi_2)

        # --- G9 Lantai 2 (Area Campuran) ---
        s_g9_lt2_agg = self.addSwitch('s5')
        self.addLink(s_dist_g9, s_g9_lt2_agg)

        # Keuangan (G9 Lt1 Kabel: 192.168.10.0/27)
        s_adm_keu = self.addSwitch('s6')
        self.addLink(s_g9_lt2_agg, s_adm_keu)
        h_keu_1 = self.addHost('keu1', ip='192.168.10.11/27')
        h_keu_2 = self.addHost('keu2', ip='192.168.10.12/27')
        self.addLink(s_adm_keu, h_keu_1)
        self.addLink(s_adm_keu, h_keu_2)

        # Pimpinan (G9 Lt2 Kabel: 192.168.10.32/26)
        s_pimpinan = self.addSwitch('s7')
        self.addLink(s_g9_lt2_agg, s_pimpinan)
        h_dekan = self.addHost('dekan', ip='192.168.10.33/26')
        h_sekre = self.addHost('sekre', ip='192.168.10.34/26')
        self.addLink(s_pimpinan, h_dekan)
        self.addLink(s_pimpinan, h_sekre)

        # Dosen Gedung G9 (G9 Lt2 Kabel: 192.168.10.32/26)
        s_dosen_g9 = self.addSwitch('s8')
        self.addLink(s_g9_lt2_agg, s_dosen_g9)
        h_dsn_g9_1 = self.addHost('dsn9a', ip='192.168.10.35/26')
        h_dsn_g9_2 = self.addHost('dsn9b', ip='192.168.10.36/26')
        self.addLink(s_dosen_g9, h_dsn_g9_1)
        self.addLink(s_dosen_g9, h_dsn_g9_2)

        # R.Ujian (G9 Lt3 Kabel: 192.168.10.96/25)
        s_ujian = self.addSwitch('s9')
        self.addLink(s_g9_lt2_agg, s_ujian)
        h_ujian_1 = self.addHost('ujian1', ip='192.168.10.97/25')
        h_ujian_2 = self.addHost('ujian2', ip='192.168.10.98/25')
        self.addLink(s_ujian, h_ujian_1)
        self.addLink(s_ujian, h_ujian_2)

        # --- G9 Lantai 3 (Lab & AP Mahasiswa) ---
        # Switch Utama Lantai 3
        s_g9_lt3_main = self.addSwitch('s10')
        self.addLink(s_dist_g9, s_g9_lt3_main)

        # Lab 1 (G9 Lt3 Nirkabel: 192.168.6.0/22)
        s_lab1 = self.addSwitch('s11')
        self.addLink(s_g9_lt3_main, s_lab1)
        h_lab1_a = self.addHost('lab1a', ip='192.168.1.50/22')
        h_lab1_b = self.addHost('lab1b', ip='192.168.1.51/22')
        self.addLink(s_lab1, h_lab1_a)
        self.addLink(s_lab1, h_lab1_b)

        # Lab 2 (G9 Lt3 Nirkabel: 192.168.6.0/22)
        s_lab2 = self.addSwitch('s12')
        self.addLink(s_g9_lt3_main, s_lab2)
        h_lab2_a = self.addHost('lab2a', ip='192.168.2.50/22')
        h_lab2_b = self.addHost('lab2b', ip='192.168.2.51/22')
        self.addLink(s_lab2, h_lab2_a)
        self.addLink(s_lab2, h_lab2_b)

        # Lab 3 (G9 Lt3 Nirkabel: 192.168.6.0/22)
        s_lab3 = self.addSwitch('s13')
        self.addLink(s_g9_lt3_main, s_lab3)
        h_lab3_a = self.addHost('lab3a', ip='192.168.3.50/22')
        h_lab3_b = self.addHost('lab3b', ip='192.168.3.51/22')
        self.addLink(s_lab3, h_lab3_a)
        self.addLink(s_lab3, h_lab3_b)

        # Access Point Mahasiswa Lt3 (G9 Lt3 Nirkabel: 192.168.6.0/22)
        h_mhs_3a = self.addHost('mhs3a', ip='192.168.6.10/22')
        h_mhs_3b = self.addHost('mhs3b', ip='192.168.6.11/22')
        self.addLink(s_g9_lt3_main, h_mhs_3a)
        self.addLink(s_g9_lt3_main, h_mhs_3b)


        # ================= GEDUNG G10 =================
        
        # Administrasi G10 (G10 Lt1 Kabel: 172.16.21.0/28)
        s_g10_lt1 = self.addSwitch('s14')
        self.addLink(s_dist_g10, s_g10_lt1)
        h_adm_g10_1 = self.addHost('adm10a', ip='172.16.21.11/28')
        h_adm_g10_2 = self.addHost('adm10b', ip='172.16.21.12/28')
        self.addLink(s_g10_lt1, h_adm_g10_1)
        self.addLink(s_g10_lt1, h_adm_g10_2)

        # Dosen G10 Lt2 & Aula
        s_g10_lt2 = self.addSwitch('s15')
        self.addLink(s_dist_g10, s_g10_lt2)
        # Dosen (G10 Lt2 Nirkabel: 172.16.20.64/25)
        h_dsn_10a_1 = self.addHost('dsn10a1', ip='172.16.20.71/25')
        h_dsn_10a_2 = self.addHost('dsn10a2', ip='172.16.20.72/25')
        # Aula (G10 Lt2 Kabel: 172.16.21.16/29)
        h_aula_1 = self.addHost('aula1', ip='172.16.21.18/29')
        h_aula_2 = self.addHost('aula2', ip='172.16.21.19/29')
        self.addLink(s_g10_lt2, h_dsn_10a_1)
        self.addLink(s_g10_lt2, h_dsn_10a_2)
        self.addLink(s_g10_lt2, h_aula_1)
        self.addLink(s_g10_lt2, h_aula_2)

        # Dosen G10 Lt3 (G10 Lt3 Nirkabel: 172.16.20.192/26)
        s_g10_lt3 = self.addSwitch('s16')
        self.addLink(s_dist_g10, s_g10_lt3)
        h_dsn_10b_1 = self.addHost('dsn10b1', ip='172.16.20.201/26')
        h_dsn_10b_2 = self.addHost('dsn10b2', ip='172.16.20.202/26')
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