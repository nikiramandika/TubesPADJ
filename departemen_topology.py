from mininet.topo import Topo

class CampusTopo(Topo):
    def build(self):

        # ---------------- CORE SWITCH ----------------
        core = self.addSwitch("s1", dpid="0000000000000001")

        # ---------------- G9 Lantai 1 ----------------
        g9l1 = self.addSwitch("s2", dpid="0000000000000002")
        self.addLink(core, g9l1)

        ap9l1 = self.addHost("ap9l1", ip="192.168.10.1/24")
        rk9l1 = self.addHost("rk9l1", ip="192.168.10.2/24")
        self.addLink(ap9l1, g9l1)
        self.addLink(rk9l1, g9l1)

        # ---------------- G9 Lantai 2 ----------------
        g9l2 = self.addSwitch("s3", dpid="0000000000000003")
        self.addLink(core, g9l2)

        ad9s1 = self.addHost("ad9s1", ip="192.168.10.11/24")
        ad9s2 = self.addHost("ad9s2", ip="192.168.10.12/24")
        pk9s1 = self.addHost("pk9s1", ip="192.168.10.21/24")
        pk9s2 = self.addHost("pk9s2", ip="192.168.10.22/24")
        ds9s1 = self.addHost("ds9s1", ip="192.168.10.31/24")
        ds9s2 = self.addHost("ds9s2", ip="192.168.10.32/24")
        uj9s1 = self.addHost("uj9s1", ip="192.168.10.41/24")
        uj9s2 = self.addHost("uj9s2", ip="192.168.10.42/24")

        self.addLink(ad9s1, g9l2)
        self.addLink(ad9s2, g9l2)
        self.addLink(pk9s1, g9l2)
        self.addLink(pk9s2, g9l2)
        self.addLink(ds9s1, g9l2)
        self.addLink(ds9s2, g9l2)
        self.addLink(uj9s1, g9l2)
        self.addLink(uj9s2, g9l2)

        # ---------------- G9 Lantai 3 ----------------
        g9l3 = self.addSwitch("s4", dpid="0000000000000004")
        self.addLink(core, g9l3)

        m9l3a = self.addHost("m9l3a", ip="192.168.10.51/24")
        m9l3b = self.addHost("m9l3b", ip="192.168.10.52/24")
        l9s3a = self.addHost("l9s3a", ip="192.168.10.61/24")
        l9s3b = self.addHost("l9s3b", ip="192.168.10.62/24")

        self.addLink(m9l3a, g9l3)
        self.addLink(m9l3b, g9l3)
        self.addLink(l9s3a, g9l3)
        self.addLink(l9s3b, g9l3)

        # ---------------- G10 Lantai 1 ----------------
        g10l1 = self.addSwitch("s5", dpid="0000000000000005")
        self.addLink(core, g10l1)

        adm10a = self.addHost("adm10a", ip="192.168.10.71/24")
        adm10b = self.addHost("adm10b", ip="192.168.10.72/24")
        self.addLink(adm10a, g10l1)
        self.addLink(adm10b, g10l1)

        # ---------------- G10 Lantai 2 ----------------
        g10l2 = self.addSwitch("s6", dpid="0000000000000006")
        self.addLink(core, g10l2)

        d10a = self.addHost("d10a", ip="192.168.10.81/24")
        d10b = self.addHost("d10b", ip="192.168.10.82/24")
        self.addLink(d10a, g10l2)
        self.addLink(d10b, g10l2)

topos = {"campus": (lambda: CampusTopo())}
