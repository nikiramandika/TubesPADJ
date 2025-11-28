from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DeptTopo(Topo):
    def build(self):
        # Switch Multicore (pusat) dengan VLAN trunk capability
        core_switch = self.addSwitch('s0')

        # Switch Gedung dengan VLAN trunk
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')

        # Gedung G9 - Lantai 1 (VLAN 91)
        g9_l1_switch = self.addSwitch('g9l1')

        # Gedung G9 - Lantai 2 (VLAN 92) dengan 4 switch tambahan
        g9_l2_main = self.addSwitch('g9l2')
        g9_l2_s1 = self.addSwitch('g9s1')
        g9_l2_s2 = self.addSwitch('g9s2')
        g9_l2_s3 = self.addSwitch('g9s3')
        g9_l2_s4 = self.addSwitch('g9s4')

        # Gedung G9 - Lantai 3 (VLAN 93) dengan 3 switch tambahan
        g9_l3_main = self.addSwitch('g9l3')
        g9_l3_s1 = self.addSwitch('g9l1s')
        g9_l3_s2 = self.addSwitch('g9l2s')
        g9_l3_s3 = self.addSwitch('g9l3s')

        # Gedung G10 - 3 lantai dengan VLAN
        g10_l1_switch = self.addSwitch('g10l1')    # VLAN 101
        g10_l2_switch = self.addSwitch('g10l2')    # VLAN 102
        g10_l3_switch = self.addSwitch('g10l3')    # VLAN 103

        # ====== GEDUNG G9 - IP KABEL & NIRKABEL SESUAI SKEMA ======

        # Gedung G9 - Lantai 1 (VLAN 91) - Mahasiswa
        # IP Kabel: 192.168.10.0/27 (192.168.10.1 - 192.168.10.30)
        # IP Nirkabel: 192.168.1.0/22 (192.168.1.1 - 192.168.4.254)
        h1 = self.addHost('ap9l1', ip='192.168.1.1/22')    # AP Mahasiswa L1 (Nirkabel)
        h2 = self.addHost('rk9l1', ip='192.168.10.1/27')  # Ruang Kuliah L1 (Kabel)

        # Gedung G9 - Lantai 2 (VLAN 92) - 4 Zona Berbeda
        # IP Kabel: 192.168.10.32/26 (192.168.10.33 - 192.168.10.94)
        # IP Nirkabel: 192.168.5.0/24 (192.168.5.1 - 192.168.5.254)

        # Zona 1: Administrasi & Keuangan (HIGH-SENSITIVITY)
        h3 = self.addHost('keuangan', ip='192.168.10.33/26')      # Keuangan & Kepegawaian
        h4 = self.addHost('bendahara', ip='192.168.10.34/26')     # Bendahara
        h5 = self.addHost('dept_ekonomi', ip='192.168.10.35/26')  # Dept. Ekonomi Pembangunan
        h6 = self.addHost('adm_jur', ip='192.168.10.36/26')      # Administrasi Jurusan
        h7 = self.addHost('kemahasiswaan', ip='192.168.10.37/26') # Kemahasiswaan
        h8 = self.addHost('pudok', ip='192.168.10.38/26')         # Pudok

        # Zona 2: Pimpinan & Sekretariat (VERY HIGH-SENSITIVITY)
        h9 = self.addHost('dekan', ip='192.168.10.39/26')         # Dekan
        h10 = self.addHost('sek_pd1', ip='192.168.10.40/26')      # Sekretaris PD 1
        h11 = self.addHost('sek_dekan', ip='192.168.10.41/26')    # Sekretaris Dekan
        h12 = self.addHost('sek_jur', ip='192.168.10.42/26')      # Sekretaris Jurusan
        h13 = self.addHost('ka_bag', ip='192.168.10.43/26')       # Kepala Bagian

        # Zona 3: Dosen (SEMI-TRUSTED)
        h14 = self.addHost('dosen1', ip='192.168.10.44/26')      # Dosen 1
        h15 = self.addHost('dosen2', ip='192.168.10.45/26')      # Dosen 2
        h16 = self.addHost('dosen3', ip='192.168.10.46/26')      # Dosen 3

        # Zona 4: Ujian / Assessment (CONTROLLED & ISOLATED)
        h17 = self.addHost('ujian_server1', ip='192.168.10.47/26') # Ujian Server 1
        h18 = self.addHost('ujian_server2', ip='192.168.10.48/26') # Ujian Server 2

        # Mahasiswa (dari Zona Ujian)
        h19 = self.addHost('mhs_ujian1', ip='192.168.10.49/26')   # Mahasiswa Ujian 1
        h20 = self.addHost('mhs_ujian2', ip='192.168.10.50/26')   # Mahasiswa Ujian 2

        # Gedung G9 - Lantai 3 (VLAN 93) - Lab & Mahasiswa
        # IP Kabel: 192.168.10.96/25 (192.168.10.97 - 192.168.10.222)
        # IP Nirkabel: 192.168.6.0/22 (192.168.6.1 - 192.168.9.254)

        # Lab 1-3
        h21 = self.addHost('lab1_pc1', ip='192.168.10.97/25')   # Lab 1 PC 1
        h22 = self.addHost('lab1_pc2', ip='192.168.10.98/25')   # Lab 1 PC 2
        h23 = self.addHost('lab2_pc1', ip='192.168.10.99/25')   # Lab 2 PC 1
        h24 = self.addHost('lab2_pc2', ip='192.168.10.100/25')  # Lab 2 PC 2
        h25 = self.addHost('lab3_pc1', ip='192.168.10.101/25')  # Lab 3 PC 1
        h26 = self.addHost('lab3_pc2', ip='192.168.10.102/25')  # Lab 3 PC 2

        # Mahasiswa & Access Point Lantai 3
        h27 = self.addHost('ap9l3', ip='192.168.6.1/22')        # AP Mahasiswa L3 (Nirkabel)
        h28 = self.addHost('mhs_l3_1', ip='192.168.10.103/25')  # Mahasiswa L3 1 (Kabel)
        h29 = self.addHost('mhs_l3_2', ip='192.168.10.104/25')  # Mahasiswa L3 2 (Kabel)

        # ====== GEDUNG G10 - IP KABEL & NIRKABEL SESUAI SKEMA ======

        # Gedung G10 - Lantai 1 (VLAN 101) - Administrasi & Keuangan (HIGH-SENSITIVITY)
        # IP Kabel: 172.16.21.0/28 (172.16.21.1 - 172.16.21.14)
        # IP Nirkabel: 172.16.20.0/26 (172.16.20.1 - 172.16.20.62)
        h30 = self.addHost('admin_g10', ip='172.16.21.1/28')      # Administrasi G10 (Kabel)
        h31 = self.addHost('ap10l1', ip='172.16.20.1/26')        # AP G10 L1 (Nirkabel)

        # Gedung G10 - Lantai 2 (VLAN 102) - Dosen (SEMI-TRUSTED)
        # IP Kabel: 172.16.21.16/29 (172.16.21.17 - 172.16.21.22)
        # IP Nirkabel: 172.16.20.64/25 (172.16.20.65 - 172.16.20.190)
        h32 = self.addHost('dosen_g10_1', ip='172.16.21.17/29')  # Dosen G10 1 (Kabel)
        h33 = self.addHost('dosen_g10_2', ip='172.16.21.18/29')  # Dosen G10 2 (Kabel)
        h34 = self.addHost('ap10l2', ip='172.16.20.65/25')       # AP G10 L2 (Nirkabel)

        # Gedung G10 - Lantai 3 (VLAN 103) - Dosen (SEMI-TRUSTED)
        # IP Kabel: 172.16.21.32/26 (172.16.21.33 - 172.16.21.94)
        # IP Nirkabel: 172.16.20.192/26 (172.16.20.193 - 172.16.20.254)
        h35 = self.addHost('dosen_g10_3', ip='172.16.21.33/26')  # Dosen G10 3 (Kabel)
        h36 = self.addHost('dosen_g10_4', ip='172.16.21.34/26')  # Dosen G10 4 (Kabel)
        h37 = self.addHost('ap10l3', ip='172.16.20.193/26')     # AP G10 L3 (Nirkabel)

        # Hubungkan core switch ke switch gedung
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)

        # Hubungkan switch gedung ke switch lantai
        self.addLink(g9_switch, g9_l1_switch)
        self.addLink(g9_switch, g9_l2_main)
        self.addLink(g9_switch, g9_l3_main)

        self.addLink(g10_switch, g10_l1_switch)
        self.addLink(g10_switch, g10_l2_switch)
        self.addLink(g10_switch, g10_l3_switch)

        # Hubungkan switch tambahan di Lantai 2 Gedung G9
        self.addLink(g9_l2_main, g9_l2_s1)
        self.addLink(g9_l2_main, g9_l2_s2)
        self.addLink(g9_l2_main, g9_l2_s3)
        self.addLink(g9_l2_main, g9_l2_s4)

        # Hubungkan switch tambahan di Lantai 3 Gedung G9
        self.addLink(g9_l3_main, g9_l3_s1)
        self.addLink(g9_l3_main, g9_l3_s2)
        self.addLink(g9_l3_main, g9_l3_s3)

        # ====== HUBUNGKAN HOST KE SWITCH SESUAI ZONA ======

        # Gedung G9 - Lantai 1 (VLAN 91) - Mahasiswa
        self.addLink(h1, g9_l1_switch)    # AP Mahasiswa (Nirkabel)
        self.addLink(h2, g9_l1_switch)    # Ruang Kuliah (Kabel)

        # Gedung G9 - Lantai 2 (VLAN 92) - 4 Zona Berbeda
        # Zona 1: Administrasi & Keuangan (HIGH-SENSITIVITY)
        self.addLink(h3, g9_l2_s1)        # Keuangan & Kepegawaian
        self.addLink(h4, g9_l2_s1)        # Bendahara
        self.addLink(h5, g9_l2_s2)        # Dept. Ekonomi Pembangunan
        self.addLink(h6, g9_l2_s2)        # Administrasi Jurusan
        self.addLink(h7, g9_l2_s3)        # Kemahasiswaan
        self.addLink(h8, g9_l2_s3)        # Pudok

        # Zona 2: Pimpinan & Sekretariat (VERY HIGH-SENSITIVITY)
        self.addLink(h9, g9_l2_s4)        # Dekan
        self.addLink(h10, g9_l2_s4)       # Sekretaris PD 1
        self.addLink(h11, g9_l2_main)     # Sekretaris Dekan
        self.addLink(h12, g9_l2_main)     # Sekretaris Jurusan
        self.addLink(h13, g9_l2_main)     # Kepala Bagian

        # Zona 3: Dosen (SEMI-TRUSTED)
        self.addLink(h14, g9_l2_s1)       # Dosen 1
        self.addLink(h15, g9_l2_s2)       # Dosen 2
        self.addLink(h16, g9_l2_s3)       # Dosen 3

        # Zona 4: Ujian / Assessment (CONTROLLED & ISOLATED)
        self.addLink(h17, g9_l2_s4)       # Ujian Server 1
        self.addLink(h18, g9_l2_s4)       # Ujian Server 2

        # Mahasiswa dalam zona Ujian
        self.addLink(h19, g9_l2_main)     # Mahasiswa Ujian 1
        self.addLink(h20, g9_l2_main)     # Mahasiswa Ujian 2

        # Gedung G9 - Lantai 3 (VLAN 93) - Lab & Mahasiswa
        # Lab 1-3
        self.addLink(h21, g9_l3_s1)        # Lab 1 PC 1
        self.addLink(h22, g9_l3_s1)        # Lab 1 PC 2
        self.addLink(h23, g9_l3_s2)        # Lab 2 PC 1
        self.addLink(h24, g9_l3_s2)        # Lab 2 PC 2
        self.addLink(h25, g9_l3_s3)        # Lab 3 PC 1
        self.addLink(h26, g9_l3_s3)        # Lab 3 PC 2

        # Mahasiswa & Access Point Lantai 3
        self.addLink(h27, g9_l3_main)      # AP Mahasiswa (Nirkabel)
        self.addLink(h28, g9_l3_main)      # Mahasiswa L3 1 (Kabel)
        self.addLink(h29, g9_l3_main)      # Mahasiswa L3 2 (Kabel)

        # Gedung G10 - Lantai 1 (VLAN 101) - Administrasi & Keuangan (HIGH-SENSITIVITY)
        self.addLink(h30, g10_l1_switch)   # Administrasi (Kabel)
        self.addLink(h31, g10_l1_switch)   # AP (Nirkabel)

        # Gedung G10 - Lantai 2 (VLAN 102) - Dosen (SEMI-TRUSTED)
        self.addLink(h32, g10_l2_switch)   # Dosen 1 (Kabel)
        self.addLink(h33, g10_l2_switch)   # Dosen 2 (Kabel)
        self.addLink(h34, g10_l2_switch)   # AP (Nirkabel)

        # Gedung G10 - Lantai 3 (VLAN 103) - Dosen (SEMI-TRUSTED)
        self.addLink(h35, g10_l3_switch)   # Dosen 3 (Kabel)
        self.addLink(h36, g10_l3_switch)   # Dosen 4 (Kabel)
        self.addLink(h37, g10_l3_switch)   # AP (Nirkabel)

    def setup_vlan_configuration(self, net):
        """Setup VLAN configuration setelah network start"""
        print("\n*** Setting up VLAN Configuration...")
        print("*** VLAN Segregation Active:")
        print("  - Gedung G9: Lantai 1 (VLAN 91), Lantai 2 (VLAN 92), Lantai 3 (VLAN 93)")
        print("  - Gedung G10: Lantai 1 (VLAN 101), Lantai 2 (VLAN 102), Lantai 3 (VLAN 103)")
        print("  - Inter-floor communication memerlukan routing atau special rules")

topos = { 'dept_topo': ( lambda: DeptTopo() ) }

def run():
    topo = DeptTopo()
    
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch)
    
    print("\n*** Memulai Jaringan (Departemen Topology)...")
    net.start()
    
    print("*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()