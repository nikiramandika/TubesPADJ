"""
departemen_topology.py
Topologi Mininet untuk Departemen (Gedung G9 & G10)
- Hierarki: core switch (s0) -> gedung switch (g9, g10) -> lantai utama -> subswitch (lab/zone)
- Host dan IP address disesuaikan dengan skema yang dibicarakan
- Pastikan menjalankan Mininet dengan: --switch ovsk,protocols=OpenFlow13
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel


class DeptTopo(Topo):
    def build(self):
        # ------------------------------------
        # Core
        # ------------------------------------
        core = self.addSwitch('s0')

        # ------------------------------------
        # Gedung switches (per gedung)
        # ------------------------------------
        g9 = self.addSwitch('g9')   # gedung 9 (hub untuk lantai)
        g10 = self.addSwitch('g10') # gedung 10 (hub untuk lantai)

        # ------------------------------------
        # Gedung G9 lantai switches
        # ------------------------------------
        g9_l1 = self.addSwitch('g9l1')   # Lantai 1 utama
        g9_l2 = self.addSwitch('g9l2')   # Lantai 2 utama (menghubungkan 4 subswitch)
        g9_l3 = self.addSwitch('g9l3')   # Lantai 3 utama (menghubungkan 3 lab switch)

        # Subswitch L2 (4 zone)
        g9s1 = self.addSwitch('g9s1')  # Zona Dosen (semi-trusted)
        g9s2 = self.addSwitch('g9s2')  # Administrasi & Keuangan (high-sensitivity)
        g9s3 = self.addSwitch('g9s3')  # Pimpinan & Sekretariat (very-high)
        g9s4 = self.addSwitch('g9s4')  # Zona Ujian (controlled & isolated)

        # Subswitch L3 (3 lab switch)
        g9l1s = self.addSwitch('g9l1s')  # Lab1
        g9l2s = self.addSwitch('g9l2s')  # Lab2
        g9l3s = self.addSwitch('g9l3s')  # Lab3

        # ------------------------------------
        # Gedung G10 lantai switches
        # ------------------------------------
        g10_l1 = self.addSwitch('g10l1')  # G10 L1
        g10_l2 = self.addSwitch('g10l2')  # G10 L2
        g10_l3 = self.addSwitch('g10l3')  # G10 L3

        # ------------------------------------
        # Hosts (menggunakan IP yang sama seperti percobaanmu)
        # ------------------------------------
        # G9 - L1: Mahasiswa (AP + 1 host ruang kuliah)
        ap9l1 = self.addHost('ap9l1', ip='192.168.10.1/27')
        rk9l1 = self.addHost('rk9l1', ip='192.168.10.2/27')

        # G9 - L2 subswitch 1: Dosen (192.168.10.32/27)
        d9s1 = self.addHost('d9s1', ip='192.168.10.33/27')
        d9s1b = self.addHost('d9s1b', ip='192.168.10.34/27')

        # G9 - L2 subswitch 2: Administrasi & Keuangan (192.168.10.64/27)
        ad9s2 = self.addHost('ad9s2', ip='192.168.10.65/27')
        ad9s2b = self.addHost('ad9s2b', ip='192.168.10.66/27')

        # G9 - L2 subswitch 3: Pimpinan & Sekretariat (192.168.10.96/27)
        p9s3 = self.addHost('p9s3', ip='192.168.10.97/27')
        p9s3b = self.addHost('p9s3b', ip='192.168.10.98/27')

        # G9 - L2 subswitch 4: Ujian & Mahasiswa (192.168.10.128/27)
        uj9s4 = self.addHost('uj9s4', ip='192.168.10.129/27')
        uj9s4b = self.addHost('uj9s4b', ip='192.168.10.130/27')

        # G9 - L3 labs (192.168.10.160/27, .192/27, .224/27)
        lab1 = self.addHost('lab1', ip='192.168.10.161/27')
        lab1b = self.addHost('lab1b', ip='192.168.10.162/27')

        lab2 = self.addHost('lab2', ip='192.168.10.193/27')
        lab2b = self.addHost('lab2b', ip='192.168.10.194/27')

        lab3 = self.addHost('lab3', ip='192.168.10.225/27')
        lab3b = self.addHost('lab3b', ip='192.168.10.226/27')

        # G9 - L3 Mahasiswa AP + 2 hosts (192.168.10.240/28)
        ap9l3 = self.addHost('ap9l3', ip='192.168.10.241/28')
        m9l3a = self.addHost('m9l3a', ip='192.168.10.242/28')
        m9l3b = self.addHost('m9l3b', ip='192.168.10.243/28')

        # G10 - L1 (172.16.21.0/28)
        ap10l1 = self.addHost('ap10l1', ip='172.16.21.1/28')
        rk10l1 = self.addHost('rk10l1', ip='172.16.21.2/28')

        # G10 - L2 (172.16.21.16/28)
        d10l2 = self.addHost('d10l2', ip='172.16.21.17/28')
        d10l2b = self.addHost('d10l2b', ip='172.16.21.18/28')

        # G10 - L3 (172.16.21.32/27)
        d10l3 = self.addHost('d10l3', ip='172.16.21.33/27')
        d10l3b = self.addHost('d10l3b', ip='172.16.21.34/27')

        # G10 additional APs/hosts
        ap10l2 = self.addHost('ap10l2', ip='172.16.21.19/28')
        m10l2a = self.addHost('m10l2a', ip='172.16.21.20/28')

        apaula = self.addHost('apaula', ip='172.16.21.21/28')
        aulab = self.addHost('aulab', ip='172.16.21.22/28')

        ap10l3 = self.addHost('ap10l3', ip='172.16.21.35/27')
        m10l3a = self.addHost('m10l3a', ip='172.16.21.36/27')

        # ------------------------------------
        # Links: core <-> gedung
        # ------------------------------------
        self.addLink(core, g9)
        self.addLink(core, g10)

        # ------------------------------------
        # G9 hierarchy
        # core -> g9 -> g9_l1, g9_l2, g9_l3
        # ------------------------------------
        self.addLink(g9, g9_l1)
        self.addLink(g9, g9_l2)
        self.addLink(g9, g9_l3)

        # connect g9_l1 to subs (l2, l3) as aggregator (as you had)
        self.addLink(g9_l1, g9_l2)
        self.addLink(g9_l1, g9_l3)

        # connect g9_l2 to its 4 zone switches
        self.addLink(g9_l2, g9s1)
        self.addLink(g9_l2, g9s2)
        self.addLink(g9_l2, g9s3)
        self.addLink(g9_l2, g9s4)

        # connect g9_l3 main to lab switches
        self.addLink(g9_l3, g9l1s)
        self.addLink(g9_l3, g9l2s)
        self.addLink(g9_l3, g9l3s)

        # ------------------------------------
        # Attach hosts to switches (2 hosts per subswitch typically)
        # ------------------------------------
        # G9 L1
        self.addLink(ap9l1, g9_l1)
        self.addLink(rk9l1, g9_l1)

        # G9 L2 zones
        self.addLink(d9s1, g9s1)
        self.addLink(d9s1b, g9s1)

        self.addLink(ad9s2, g9s2)
        self.addLink(ad9s2b, g9s2)

        self.addLink(p9s3, g9s3)
        self.addLink(p9s3b, g9s3)

        self.addLink(uj9s4, g9s4)
        self.addLink(uj9s4b, g9s4)

        # G9 L3 labs
        self.addLink(lab1, g9l1s)
        self.addLink(lab1b, g9l1s)

        self.addLink(lab2, g9l2s)
        self.addLink(lab2b, g9l2s)

        self.addLink(lab3, g9l3s)
        self.addLink(lab3b, g9l3s)

        # G9 L3 main: AP + mahasiswa
        self.addLink(ap9l3, g9_l3)
        self.addLink(m9l3a, g9_l3)
        self.addLink(m9l3b, g9_l3)

        # ------------------------------------
        # G10 hierarchy + hosts
        # ------------------------------------
        self.addLink(g10, g10_l1)
        self.addLink(g10_l1, g10_l2)
        self.addLink(g10_l1, g10_l3)

        self.addLink(ap10l1, g10_l1)
        self.addLink(rk10l1, g10_l1)

        self.addLink(d10l2, g10_l2)
        self.addLink(d10l2b, g10_l2)

        self.addLink(d10l3, g10_l3)
        self.addLink(d10l3b, g10_l3)

        # AP & aula attachments
        self.addLink(ap10l2, g10_l2)
        self.addLink(m10l2a, g10_l2)
        self.addLink(apaula, g10_l2)
        self.addLink(aulab, g10_l2)

        self.addLink(ap10l3, g10_l3)
        self.addLink(m10l3a, g10_l3)


# Create topo mapping so we can use --topo option
topos = {'dept_topo': (lambda: DeptTopo())}


def run():
    "Optional: start Mininet directly from this file"
    topo = DeptTopo()
    net = Mininet(topo=topo,
                  controller=RemoteController('c0', ip='127.0.0.1'),
                  switch=OVSKernelSwitch)
    print("*** Starting network")
    net.start()
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
