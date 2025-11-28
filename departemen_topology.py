from mininet.topo import Topo

class CampusTopo(Topo):
    def build(self):

        # ========= SWITCH LIST (FORMAT WAJIB: s1, s2, s3 ...) =========
        s1 = self.addSwitch('s1')   # G9 Lantai 1
        s2 = self.addSwitch('s2')   # G9 Lantai 2 Main
        s3 = self.addSwitch('s3')   # Administrasi
        s4 = self.addSwitch('s4')   # Pimpinan
        s5 = self.addSwitch('s5')   # Dosen G9 L2
        s6 = self.addSwitch('s6')   # Ujian
        s7 = self.addSwitch('s7')   # G9 Lantai 3
        s8 = self.addSwitch('s8')   # G10 Lantai 1
        s9 = self.addSwitch('s9')   # G10 Lantai 2
        s10 = self.addSwitch('s10') # G10 Lantai 3

        # ==============================================================
        # ----------------------- G9 LANTAI 1 ---------------------------
        # ==============================================================
        ap9l1 = self.addHost('ap9l1')
        m9l1a = self.addHost('m9l1a')
        m9l1b = self.addHost('m9l1b')

        self.addLink(s1, ap9l1)
        self.addLink(s1, m9l1a)
        self.addLink(s1, m9l1b)

        # ==============================================================
        # ----------------------- G9 LANTAI 2 ---------------------------
        # ==============================================================
        self.addLink(s2, s3)  # ke Administrasi
        self.addLink(s2, s4)  # ke Pimpinan
        self.addLink(s2, s5)  # ke Dosen
        self.addLink(s2, s6)  # ke Ujian

        # Admin
        ad9s1 = self.addHost('ad9s1')
        ad9s2 = self.addHost('ad9s2')
        self.addLink(s3, ad9s1)
        self.addLink(s3, ad9s2)

        # Pimpinan
        pk9s1 = self.addHost('pk9s1')
        pk9s2 = self.addHost('pk9s2')
        self.addLink(s4, pk9s1)
        self.addLink(s4, pk9s2)

        # Dosen
        ds9s1 = self.addHost('ds9s1')
        ds9s2 = self.addHost('ds9s2')
        self.addLink(s5, ds9s1)
        self.addLink(s5, ds9s2)

        # Ujian
        uj9s1 = self.addHost('uj9s1')
        uj9s2 = self.addHost('uj9s2')
        self.addLink(s6, uj9s1)
        self.addLink(s6, uj9s2)

        # ==============================================================
        # ----------------------- G9 LANTAI 3 ---------------------------
        # ==============================================================
        l9s3a = self.addHost('l9s3a')
        l9s3b = self.addHost('l9s3b')
        m9l3a = self.addHost('m9l3a')
        m9l3b = self.addHost('m9l3b')

        self.addLink(s7, l9s3a)
        self.addLink(s7, l9s3b)
        self.addLink(s7, m9l3a)
        self.addLink(s7, m9l3b)

        # ==============================================================
        # ----------------------- G10 LANTAI 1 --------------------------
        # ==============================================================
        adm10a = self.addHost('adm10a')
        adm10b = self.addHost('adm10b')

        self.addLink(s8, adm10a)
        self.addLink(s8, adm10b)

        # ==============================================================
        # ----------------------- G10 LANTAI 2 --------------------------
        # ==============================================================
        d10a = self.addHost('d10a')
        d10b = self.addHost('d10b')
        ap10l2 = self.addHost('ap10l2')

        self.addLink(s9, d10a)
        self.addLink(s9, d10b)
        self.addLink(s9, ap10l2)

        # ==============================================================
        # ----------------------- G10 LANTAI 3 --------------------------
        # ==============================================================
        d10a3 = self.addHost('d10a3')
        d10b3 = self.addHost('d10b3')
        ap10l3 = self.addHost('ap10l3')

        self.addLink(s10, d10a3)
        self.addLink(s10, d10b3)
        self.addLink(s10, ap10l3)

topos = {'campus': (lambda: CampusTopo())}
