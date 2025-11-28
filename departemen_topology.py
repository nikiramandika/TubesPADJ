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
        # Mahasiswa (IP 100+)
        s_g9_lt1 = self.addSwitch('s4')
        self.addLink(s_dist_g9, s_g9_lt1)
        h_mhs_1 = self.addHost('mhs1', ip='10.0.0.101/24')
        h_mhs_2 = self.addHost('mhs2', ip='10.0.0.102/24')
        self.addLink(s_g9_lt1, h_mhs_1)
        self.addLink(s_g9_lt1, h_mhs_2)

        # Lantai 2 (Area Campuran)
        s_g9_lt2_agg = self.addSwitch('s5')
        self.addLink(s_dist_g9, s_g9_lt2_agg)

        # Keuangan (IP 10-19)
        s_adm_keu = self.addSwitch('s6')
        self.addLink(s_g9_lt2_agg, s_adm_keu)
        h_keu_1 = self.addHost('keu1', ip='10.0.0.11/24')
        h_keu_2 = self.addHost('keu2', ip='10.0.0.12/24')
        self.addLink(s_adm_keu, h_keu_1)
        self.addLink(s_adm_keu, h_keu_2)

        # Pimpinan (IP 20-29)
        s_pimpinan = self.addSwitch('s7')
        self.addLink(s_g9_lt2_agg, s_pimpinan)
        h_dekan = self.addHost('dekan', ip='10.0.0.21/24')
        self.addLink(s_pimpinan, h_dekan)

        # Dosen G9 (IP 30-39)
        s_dosen_g9 = self.addSwitch('s8')
        self.addLink(s_g9_lt2_agg, s_dosen_g9)
        h_dsn_g9 = self.addHost('dsn9', ip='10.0.0.31/24')
        self.addLink(s_dosen_g9, h_dsn_g9)

        # Ujian (IP 90-99)
        s_ujian = self.addSwitch('s9')
        self.addLink(s_g9_lt2_agg, s_ujian)
        h_ujian = self.addHost('ujian', ip='10.0.0.91/24')
        self.addLink(s_ujian, h_ujian)

        # Lantai 3 (Lab & Mahasiswa)
        s_g9_lt3 = self.addSwitch('s10')
        self.addLink(s_dist_g9, s_g9_lt3)
        h_mhs_3 = self.addHost('mhs3', ip='10.0.0.103/24') # Mhs Wifi Lt3
        self.addLink(s_g9_lt3, h_mhs_3)


        # ================= GEDUNG G10 =================
        # Admin G10 (IP 10-19, sama kayak keuangan levelnya)
        s_g10_lt1 = self.addSwitch('s14')
        self.addLink(s_dist_g10, s_g10_lt1)
        h_adm_g10 = self.addHost('adm10', ip='10.0.0.13/24')
        self.addLink(s_g10_lt1, h_adm_g10)

        # Dosen G10 (IP 30-39)
        s_g10_lt2 = self.addSwitch('s15')
        self.addLink(s_dist_g10, s_g10_lt2)
        h_dsn_10a = self.addHost('dsn10a', ip='10.0.0.32/24')
        h_aula = self.addHost('aula', ip='10.0.0.104/24') # Aula = Public/Mhs
        self.addLink(s_g10_lt2, h_dsn_10a)
        self.addLink(s_g10_lt2, h_aula)

        s_g10_lt3 = self.addSwitch('s16')
        self.addLink(s_dist_g10, s_g10_lt3)
        h_dsn_10b = self.addHost('dsn10b', ip='10.0.0.33/24')
        self.addLink(s_g10_lt3, h_dsn_10b)

def run():
    topo = MedicalSimpleTopo()
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    print("[+] Simple Flat Topology Started (10.0.0.x/24).")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()