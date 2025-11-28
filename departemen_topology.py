from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DeptTopo(Topo):
    def build(self):
        # Switch Multicore (pusat)
        core_switch = self.addSwitch('s0')

        # Switch Gedung
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')

        # Gedung G9 - Lantai 1
        g9_l1_switch = self.addSwitch('g9l1')

        # Gedung G9 - Lantai 2 (dengan 4 switch tambahan)
        g9_l2_main = self.addSwitch('g9l2')
        g9_l2_s1 = self.addSwitch('g9s1')
        g9_l2_s2 = self.addSwitch('g9s2')
        g9_l2_s3 = self.addSwitch('g9s3')
        g9_l2_s4 = self.addSwitch('g9s4')

        # Gedung G9 - Lantai 3 (dengan 3 switch tambahan)
        g9_l3_main = self.addSwitch('g9l3')
        g9_l3_s1 = self.addSwitch('g9l1s')
        g9_l3_s2 = self.addSwitch('g9l2s')
        g9_l3_s3 = self.addSwitch('g9l3s')

        # Gedung G10 - 3 lantai
        g10_l1_switch = self.addSwitch('g10l1')
        g10_l2_switch = self.addSwitch('g10l2')
        g10_l3_switch = self.addSwitch('g10l3')

        # Gedung G9 - Lantai 1 (IP : 192.168.10.0/27) - Ruang Kuliah + AP Mahasiswa
        h1 = self.addHost('ap9l1', ip='192.168.10.1/27')  # AP Mahasiswa Lantai 1
        h2 = self.addHost('rk9l1', ip='192.168.10.2/27')  # Host Ruang Kuliah Lantai 1

        # Gedung G9 - Lantai 2 - Switch 1 (subnet dari 192.168.10.32/27) - Dosen
        h3 = self.addHost('d9s1', ip='192.168.10.33/27')
        h4 = self.addHost('d9s1b', ip='192.168.10.34/27')

        # Gedung G9 - Lantai 2 - Switch 2 (subnet dari 192.168.10.64/27) - Administrasi & Keuangan
        h5 = self.addHost('ad9s2', ip='192.168.10.65/27')
        h6 = self.addHost('ad9s2b', ip='192.168.10.66/27')

        # Gedung G9 - Lantai 2 - Switch 3 (subnet dari 192.168.10.96/27) - Pimpinan & Kesekretariatan
        h7 = self.addHost('p9s3', ip='192.168.10.97/27')
        h8 = self.addHost('p9s3b', ip='192.168.10.98/27')

        # Gedung G9 - Lantai 2 - Switch 4 (subnet dari 192.168.10.128/27) - Ujian & Mahasiswa
        h9 = self.addHost('uj9s4', ip='192.168.10.129/27')
        h10 = self.addHost('uj9s4b', ip='192.168.10.130/27')

        # Gedung G9 - Lantai 3 - Switch 1 (subnet dari 192.168.10.160/27) - Lab 1
        h11 = self.addHost('lab1', ip='192.168.10.161/27')
        h12 = self.addHost('lab1b', ip='192.168.10.162/27')

        # Gedung G9 - Lantai 3 - Switch 2 (subnet dari 192.168.10.192/27) - Lab 2
        h13 = self.addHost('lab2', ip='192.168.10.193/27')
        h14 = self.addHost('lab2b', ip='192.168.10.194/27')

        # Gedung G9 - Lantai 3 - Switch 3 (subnet dari 192.168.10.224/27) - Lab 3
        h15 = self.addHost('lab3', ip='192.168.10.225/27')
        h16 = self.addHost('lab3b', ip='192.168.10.226/27')

        # Gedung G9 - Lantai 3 - Access Point dan Host (subnet dari 192.168.10.128/27) - Mahasiswa
        h17 = self.addHost('ap9l3', ip='192.168.10.129/27')  # Access Point
        h18 = self.addHost('m9l3a', ip='192.168.10.130/27')  # Host 1
        h19 = self.addHost('m9l3b', ip='192.168.10.131/27')  # Host 2

        # Gedung G10 - Lantai 1 (IP Kabel: 172.16.21.0/28) - Ruang Kuliah + AP Mahasiswa
        h21 = self.addHost('ap10l1', ip='172.16.21.1/28')  # AP Mahasiswa Lantai 1
        h22 = self.addHost('rk10l1', ip='172.16.21.2/28')  # Host Ruang Kuliah Lantai 1

        # Gedung G10 - Lantai 2 (IP Kabel: 172.16.21.16/29) - Dosen
        h23 = self.addHost('d10l2', ip='172.16.21.17/29')
        h24 = self.addHost('d10l2b', ip='172.16.21.18/29')

        # Gedung G10 - Lantai 3 (IP Kabel: 172.16.21.32/26) - Dosen
        h25 = self.addHost('d10l3', ip='172.16.21.33/26')
        h26 = self.addHost('d10l3b', ip='172.16.21.34/26')

        # Access Point Tambahan Gedung G10
        # AP Mahasiswa Gedung G10 Lantai 2
        h27 = self.addHost('ap10l2', ip='172.16.21.19/29')  # AP Mahasiswa L2
        h28 = self.addHost('m10l2a', ip='172.16.21.20/29')  # Host tambahan AP L2

        # AP Aula Gedung G10 Lantai 2
        h29 = self.addHost('apaula', ip='172.16.21.21/29')  # AP Aula Khusus L2
        h30 = self.addHost('aulab', ip='172.16.21.22/29')  # Host tambahan AP Aula

        # AP Mahasiswa Gedung G10 Lantai 3
        h31 = self.addHost('ap10l3', ip='172.16.21.35/26')  # AP Mahasiswa L3
        h32 = self.addHost('m10l3a', ip='172.16.21.36/26')  # Host tambahan AP L3

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

        # Hubungkan host kabel ke switch (2 host per switch)
        # Gedung G9 - Lantai 1 (sg9-l1) - Ruang Kuliah + AP
        self.addLink(h1, g9_l1_switch)  # AP Mahasiswa
        self.addLink(h2, g9_l1_switch)  # Host Ruang Kuliah

        # Gedung G9 - Lantai 2 - Switch 1 (sg9-l2-s1)
        self.addLink(h3, g9_l2_s1)
        self.addLink(h4, g9_l2_s1)

        # Gedung G9 - Lantai 2 - Switch 2 (sg9-l2-s2)
        self.addLink(h5, g9_l2_s2)
        self.addLink(h6, g9_l2_s2)

        # Gedung G9 - Lantai 2 - Switch 3 (sg9-l2-s3)
        self.addLink(h7, g9_l2_s3)
        self.addLink(h8, g9_l2_s3)

        # Gedung G9 - Lantai 2 - Switch 4 (sg9-l2-s4)
        self.addLink(h9, g9_l2_s4)
        self.addLink(h10, g9_l2_s4)

        # Main switch lantai 2 tidak memiliki host langsung, hanya menghubungkan 4 switch tambahan

        # Gedung G9 - Lantai 3 - Switch 1 (sg9-l3-s1)
        self.addLink(h11, g9_l3_s1)
        self.addLink(h12, g9_l3_s1)

        # Gedung G9 - Lantai 3 - Switch 2 (sg9-l3-s2)
        self.addLink(h13, g9_l3_s2)
        self.addLink(h14, g9_l3_s2)

        # Gedung G9 - Lantai 3 - Switch 3 (sg9-l3-s3)
        self.addLink(h15, g9_l3_s3)
        self.addLink(h16, g9_l3_s3)

        # Main switch lantai 3 sekarang memiliki Access Point dan 2 host langsung
        # Access Point dan 2 host terhubung langsung ke main switch lantai 3
        self.addLink(h17, g9_l3_main)  # Access Point
        self.addLink(h18, g9_l3_main)  # Host 1
        self.addLink(h19, g9_l3_main)  # Host 2

        # Gedung G10 - Lantai 1 (sg10-l1) - Ruang Kuliah + AP
        self.addLink(h21, g10_l1_switch)  # AP Mahasiswa
        self.addLink(h22, g10_l1_switch)  # Host Ruang Kuliah

        # Gedung G10 - Lantai 2 (sg10-l2) - Dosen
        self.addLink(h23, g10_l2_switch)
        self.addLink(h24, g10_l2_switch)

        # Gedung G10 - Lantai 3 (sg10-l3) - Dosen
        self.addLink(h25, g10_l3_switch)
        self.addLink(h26, g10_l3_switch)

        # Hubungkan Access Point Mahasiswa Gedung G10 ke switch masing-masing lantai
        # AP Mahasiswa Gedung G10 Lantai 2 (sg10-l2)
        self.addLink(h27, g10_l2_switch)  # AP Mahasiswa L2
        self.addLink(h28, g10_l2_switch)  # Host tambahan AP L2

        # AP Aula Gedung G10 Lantai 2 (sg10-l2)
        self.addLink(h29, g10_l2_switch)  # AP Aula Khusus L2
        self.addLink(h30, g10_l2_switch)  # Host tambahan AP Aula

        # AP Mahasiswa Gedung G10 Lantai 3 (sg10-l3)
        self.addLink(h31, g10_l3_switch)  # AP Mahasiswa L3
        self.addLink(h32, g10_l3_switch)  # Host tambahan AP L3

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