from mininet.topo import Topo
from mininet.node import OVSKernelSwitch
from mininet.link import TCLink

class CampusTopo(Topo):
    def build(self):

        #
        # ============================
        #  G9 LANTAI 1
        # ============================
        #
        s_g9_l1 = self.addSwitch('s_g9_l1', protocols='OpenFlow13')

        # Mahasiswa (Access Point + 2 host)
        ap9l1 = self.addHost('ap9l1', ip='192.168.10.1/24')   # AP mahasiswa G9 L1
        m9l1a = self.addHost('m9l1a', ip='192.168.10.2/24')   # Mahasiswa 1
        m9l1b = self.addHost('m9l1b', ip='192.168.10.3/24')   # Mahasiswa 2

        self.addLink(s_g9_l1, ap9l1)
        self.addLink(s_g9_l1, m9l1a)
        self.addLink(s_g9_l1, m9l1b)

        #
        # ============================
        #  G9 LANTAI 2
        # ============================
        #
        s_g9_l2_main = self.addSwitch('s_g9_l2m', protocols='OpenFlow13')

        # 4 Switch zona di bawah lantai 2
        s_adm = self.addSwitch('s_adm', protocols='OpenFlow13')   # Administrasi & Keuangan
        s_pimp = self.addSwitch('s_pimp', protocols='OpenFlow13') # Zona Pimpinan & Sekretariat
        s_dosen9 = self.addSwitch('s_dosen9', protocols='OpenFlow13') # Zona Dosen
        s_ujian = self.addSwitch('s_ujian', protocols='OpenFlow13')   # Zona Ujian / Assessment

        # Connect sub-switch ke switch utama
        self.addLink(s_g9_l2_main, s_adm)
        self.addLink(s_g9_l2_main, s_pimp)
        self.addLink(s_g9_l2_main, s_dosen9)
        self.addLink(s_g9_l2_main, s_ujian)

        # --- Administrasi & Keuangan (high-sensitivity)
        ad9s1 = self.addHost('ad9s1', ip='192.168.20.1/24')
        ad9s2 = self.addHost('ad9s2', ip='192.168.20.2/24')
        self.addLink(s_adm, ad9s1)
        self.addLink(s_adm, ad9s2)

        # --- Zona Pimpinan (very high-sensitivity)
        pk9s1 = self.addHost('pk9s1', ip='192.168.21.1/24')
        pk9s2 = self.addHost('pk9s2', ip='192.168.21.2/24')
        self.addLink(s_pimp, pk9s1)
        self.addLink(s_pimp, pk9s2)

        # --- Zona Dosen
        ds9s1 = self.addHost('ds9s1', ip='192.168.22.1/24')
        ds9s2 = self.addHost('ds9s2', ip='192.168.22.2/24')
        self.addLink(s_dosen9, ds9s1)
        self.addLink(s_dosen9, ds9s2)

        # --- Zona Ujian (Isolated)
        uj9s1 = self.addHost('uj9s1', ip='192.168.23.1/24')
        uj9s2 = self.addHost('uj9s2', ip='192.168.23.2/24')
        self.addLink(s_ujian, uj9s1)
        self.addLink(s_ujian, uj9s2)

        #
        # ============================
        #  G9 LANTAI 3
        # ============================
        #
        s_g9_l3 = self.addSwitch('s_g9_l3', protocols='OpenFlow13')

        # 3 lab
        l9s3a = self.addHost('l9s3a', ip='192.168.30.1/24')  # Lab 1-3 host 1
        l9s3b = self.addHost('l9s3b', ip='192.168.30.2/24')  # Lab 1-3 host 2
        m9l3a = self.addHost('m9l3a', ip='192.168.31.1/24')  # Mahasiswa AP
        m9l3b = self.addHost('m9l3b', ip='192.168.31.2/24')  # Mahasiswa AP

        self.addLink(s_g9_l3, l9s3a)
        self.addLink(s_g9_l3, l9s3b)
        self.addLink(s_g9_l3, m9l3a)
        self.addLink(s_g9_l3, m9l3b)

        #
        # ============================
        #  G10 LANTAI 1
        # ============================
        #
        s_g10_l1 = self.addSwitch('s_g10_l1', protocols='OpenFlow13')

        adm10a = self.addHost('adm10a', ip='192.168.40.1/24')  # Administrasi
        adm10b = self.addHost('adm10b', ip='192.168.40.2/24')

        self.addLink(s_g10_l1, adm10a)
        self.addLink(s_g10_l1, adm10b)

        #
        # ============================
        #  G10 LANTAI 2
        # ============================
        #
        s_g10_l2 = self.addSwitch('s_g10_l2', protocols='OpenFlow13')

        d10a = self.addHost('d10a', ip='192.168.41.1/24')   # Dosen
        d10b = self.addHost('d10b', ip='192.168.41.2/24')   # Dosen
        ap10l2 = self.addHost('ap10l2', ip='192.168.42.1/24')  # AP Aula

        self.addLink(s_g10_l2, d10a)
        self.addLink(s_g10_l2, d10b)
        self.addLink(s_g10_l2, ap10l2)

        #
        # ============================
        #  G10 LANTAI 3
        # ============================
        #
        s_g10_l3 = self.addSwitch('s_g10_l3', protocols='OpenFlow13')

        d10a3 = self.addHost('d10a3', ip='192.168.43.1/24') # Dosen G10 L3
        d10b3 = self.addHost('d10b3', ip='192.168.43.2/24')
        ap10l3 = self.addHost('ap10l3', ip='192.168.44.1/24') # AP mahasiswa

        self.addLink(s_g10_l3, d10a3)
        self.addLink(s_g10_l3, d10b3)
        self.addLink(s_g10_l3, ap10l3)


topos = { 'campus': (lambda: CampusTopo()) }
