from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DeptTopo(Topo):
    def build(self):
        # Switch Core (pusat)
        core_switch = self.addSwitch('s0')

        # Switch Gedung Utama
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')

        # Switch Lantai Gedung G9
        g9_l1_switch = self.addSwitch('g9l1')
        g9_l2_switch = self.addSwitch('g9l2')
        g9_l3_switch = self.addSwitch('g9l3')

        # Switch Lantai Gedung G10
        g10_l1_switch = self.addSwitch('g10l1')
        g10_l2_switch = self.addSwitch('g10l2')
        g10_l3_switch = self.addSwitch('g10l3')

        # === GEDUNG G9 ===
        # Lantai 1: Ruang Kuliah + AP Mahasiswa (192.168.10.0/27)
        h1 = self.addHost('ap9l1', ip='192.168.10.1/27', defaultRoute='via 192.168.10.30')
        h2 = self.addHost('rk9l1', ip='192.168.10.2/27', defaultRoute='via 192.168.10.30')

        # Lantai 2: Dosen (192.168.10.32/27)
        h3 = self.addHost('d9s1', ip='192.168.10.33/27', defaultRoute='via 192.168.10.62')
        h4 = self.addHost('d9s1b', ip='192.168.10.34/27', defaultRoute='via 192.168.10.62')

        # Lantai 2: Administrasi & Keuangan (192.168.10.64/27)
        h5 = self.addHost('ad9s2', ip='192.168.10.65/27', defaultRoute='via 192.168.10.94')
        h6 = self.addHost('ad9s2b', ip='192.168.10.66/27', defaultRoute='via 192.168.10.94')

        # Lantai 2: Pimpinan & Sekretariat (192.168.10.96/27)
        h7 = self.addHost('p9s3', ip='192.168.10.97/27', defaultRoute='via 192.168.10.126')
        h8 = self.addHost('p9s3b', ip='192.168.10.98/27', defaultRoute='via 192.168.10.126')

        # Lantai 2: Ujian & Mahasiswa (192.168.10.128/27)
        h9 = self.addHost('uj9s4', ip='192.168.10.129/27', defaultRoute='via 192.168.10.158')
        h10 = self.addHost('uj9s4b', ip='192.168.10.130/27', defaultRoute='via 192.168.10.158')

        # Lantai 3: Lab 1 (192.168.10.160/27)
        h11 = self.addHost('lab1', ip='192.168.10.161/27', defaultRoute='via 192.168.10.190')
        h12 = self.addHost('lab1b', ip='192.168.10.162/27', defaultRoute='via 192.168.10.190')

        # Lantai 3: Lab 2 (192.168.10.192/27)
        h13 = self.addHost('lab2', ip='192.168.10.193/27', defaultRoute='via 192.168.10.222')
        h14 = self.addHost('lab2b', ip='192.168.10.194/27', defaultRoute='via 192.168.10.222')

        # Lantai 3: Lab 3 + AP + Mahasiswa (192.168.10.224/27)
        h15 = self.addHost('lab3', ip='192.168.10.225/27', defaultRoute='via 192.168.10.254')
        h16 = self.addHost('lab3b', ip='192.168.10.226/27', defaultRoute='via 192.168.10.254')
        h17 = self.addHost('ap9l3', ip='192.168.10.227/27', defaultRoute='via 192.168.10.254')
        h18 = self.addHost('m9l3a', ip='192.168.10.228/27', defaultRoute='via 192.168.10.254')
        h19 = self.addHost('m9l3b', ip='192.168.10.229/27', defaultRoute='via 192.168.10.254')

        # === GEDUNG G10 ===
        # Lantai 1: Ruang Kuliah + AP Mahasiswa (172.16.21.0/28)
        h21 = self.addHost('ap10l1', ip='172.16.21.1/28', defaultRoute='via 172.16.21.14')
        h22 = self.addHost('rk10l1', ip='172.16.21.2/28', defaultRoute='via 172.16.21.14')

        # Lantai 2: Dosen (172.16.21.16/29)
        h23 = self.addHost('d10l2', ip='172.16.21.17/29', defaultRoute='via 172.16.21.30')
        h24 = self.addHost('d10l2b', ip='172.16.21.18/29', defaultRoute='via 172.16.21.30')

        # Lantai 2: AP Mahasiswa & Aula (172.16.21.24/29)
        h25 = self.addHost('ap10l2', ip='172.16.21.25/29', defaultRoute='via 172.16.21.30')
        h26 = self.addHost('apaula', ip='172.16.21.26/29', defaultRoute='via 172.16.21.30')

        # Lantai 3: Dosen (172.16.21.32/27)
        h27 = self.addHost('d10l3', ip='172.16.21.33/27', defaultRoute='via 172.16.21.62')
        h28 = self.addHost('d10l3b', ip='172.16.21.34/27', defaultRoute='via 172.16.21.62')

        # Lantai 3: AP Mahasiswa (172.16.21.64/27)
        h29 = self.addHost('ap10l3', ip='172.16.21.65/27', defaultRoute='via 172.16.21.94')
        h30 = self.addHost('m10l3a', ip='172.16.21.66/27', defaultRoute='via 172.16.21.94')

        # === HUBUNGAN SWITCH ===
        # Core ke Building Switches
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)

        # G9 Building ke Floor Switches
        self.addLink(g9_switch, g9_l1_switch)
        self.addLink(g9_switch, g9_l2_switch)
        self.addLink(g9_switch, g9_l3_switch)

        # G10 Building ke Floor Switches
        self.addLink(g10_switch, g10_l1_switch)
        self.addLink(g10_switch, g10_l2_switch)
        self.addLink(g10_switch, g10_l3_switch)

        # === HUBUNGAN HOST KE SWITCH ===
        # Gedung G9
        self.addLink(h1, g9_l1_switch)   # AP Mahasiswa L1
        self.addLink(h2, g9_l1_switch)   # Ruang Kuliah L1

        self.addLink(h3, g9_l2_switch)   # Dosen L2-1
        self.addLink(h4, g9_l2_switch)   # Dosen L2-2
        self.addLink(h5, g9_l2_switch)   # Admin L2-1
        self.addLink(h6, g9_l2_switch)   # Admin L2-2
        self.addLink(h7, g9_l2_switch)   # Pimpinan L2-1
        self.addLink(h8, g9_l2_switch)   # Pimpinan L2-2
        self.addLink(h9, g9_l2_switch)   # Ujian L2-1
        self.addLink(h10, g9_l2_switch)  # Ujian L2-2

        self.addLink(h11, g9_l3_switch)  # Lab1 L3-1
        self.addLink(h12, g9_l3_switch)  # Lab1 L3-2
        self.addLink(h13, g9_l3_switch)  # Lab2 L3-1
        self.addLink(h14, g9_l3_switch)  # Lab2 L3-2
        self.addLink(h15, g9_l3_switch)  # Lab3 L3-1
        self.addLink(h16, g9_l3_switch)  # Lab3 L3-2
        self.addLink(h17, g9_l3_switch)  # AP L3
        self.addLink(h18, g9_l3_switch)  # Mahasiswa L3-1
        self.addLink(h19, g9_l3_switch)  # Mahasiswa L3-2

        # Gedung G10
        self.addLink(h21, g10_l1_switch) # AP Mahasiswa G10 L1
        self.addLink(h22, g10_l1_switch) # Ruang Kuliah G10 L1

        self.addLink(h23, g10_l2_switch) # Dosen G10 L2-1
        self.addLink(h24, g10_l2_switch) # Dosen G10 L2-2
        self.addLink(h25, g10_l2_switch) # AP G10 L2
        self.addLink(h26, g10_l2_switch) # Aula G10

        self.addLink(h27, g10_l3_switch) # Dosen G10 L3-1
        self.addLink(h28, g10_l3_switch) # Dosen G10 L3-2
        self.addLink(h29, g10_l3_switch) # AP G10 L3
        self.addLink(h30, g10_l3_switch) # Mahasiswa G10 L3

topos = { 'dept_topo': ( lambda: DeptTopo() ) }

def run():
    topo = DeptTopo()

    net = Mininet(topo=topo,
                  controller=RemoteController(name='c0', ip='127.0.0.1'),
                  switch=OVSKernelSwitch)

    print("\n*** Memulai Jaringan (Departemen Topology - Fixed)...")
    net.start()

    # Test connectivity
    print("\n*** Testing basic connectivity...")
    net.pingAll()

    print("\n*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)

    print("\n*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()