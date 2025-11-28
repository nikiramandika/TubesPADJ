from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DeptTopo(Topo):
    def build(self):
        # Core Switch (tidak melakukan routing antar-gedung untuk opsi B)
        core_switch = self.addSwitch('s0')

        # Building Switches
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')

        # Gedung G9 - Floor 1
        g9_l1_switch = self.addSwitch('g9l1')

        # Gedung G9 - Floor 2 (4 switches for 4 zones)
        g9_l2_s1 = self.addSwitch('g9l2s1')  # Dosen
        g9_l2_s2 = self.addSwitch('g9l2s2')  # Administrasi & Keuangan
        g9_l2_s3 = self.addSwitch('g9l2s3')  # Pimpinan & Sekretariat
        g9_l2_s4 = self.addSwitch('g9l2s4')  # Ujian & Mahasiswa

        # Gedung G9 - Floor 3 (3 switches for 3 labs + 1 switch for AP)
        g9_l3_s1 = self.addSwitch('g9l3s1')  # Lab 1
        g9_l3_s2 = self.addSwitch('g9l3s2')  # Lab 2
        g9_l3_s3 = self.addSwitch('g9l3s3')  # Lab 3
        g9_l3_ap = self.addSwitch('g9l3ap')  # AP & Mahasiswa

        # Gedung G10 - 3 Floors
        g10_l1_switch = self.addSwitch('g10l1')
        g10_l2_switch = self.addSwitch('g10l2')
        g10_l3_switch = self.addSwitch('g10l3')

        # ========== GEDUNG G9 - HOSTS ==========
        ap9l1 = self.addHost('ap9l1', ip='192.168.10.1/27')
        rk9l1 = self.addHost('rk9l1', ip='192.168.10.2/27')

        d9s1_1 = self.addHost('d9s1_1', ip='192.168.10.33/27')
        d9s1_2 = self.addHost('d9s1_2', ip='192.168.10.34/27')

        ad9s2_1 = self.addHost('ad9s2_1', ip='192.168.10.65/27')
        ad9s2_2 = self.addHost('ad9s2_2', ip='192.168.10.66/27')

        p9s3_1 = self.addHost('p9s3_1', ip='192.168.10.97/27')
        p9s3_2 = self.addHost('p9s3_2', ip='192.168.10.98/27')

        uj9s4_1 = self.addHost('uj9s4_1', ip='192.168.10.129/27')
        uj9s4_2 = self.addHost('uj9s4_2', ip='192.168.10.130/27')

        lab1_1 = self.addHost('lab1_1', ip='192.168.10.161/27')
        lab1_2 = self.addHost('lab1_2', ip='192.168.10.162/27')

        lab2_1 = self.addHost('lab2_1', ip='192.168.10.193/27')
        lab2_2 = self.addHost('lab2_2', ip='192.168.10.194/27')

        lab3_1 = self.addHost('lab3_1', ip='192.168.10.225/27')
        lab3_2 = self.addHost('lab3_2', ip='192.168.10.226/27')

        ap9l3_1 = self.addHost('ap9l3_1', ip='192.168.10.241/28')
        ap9l3_2 = self.addHost('ap9l3_2', ip='192.168.10.242/28')
        ap9l3_3 = self.addHost('ap9l3_3', ip='192.168.10.243/28')

        # ========== GEDUNG G10 - HOSTS ==========
        ap10l1 = self.addHost('ap10l1', ip='172.16.21.1/28')
        rk10l1 = self.addHost('rk10l1', ip='172.16.21.2/28')

        d10l2_1 = self.addHost('d10l2_1', ip='172.16.21.17/28')
        d10l2_2 = self.addHost('d10l2_2', ip='172.16.21.18/28')
        ap10l2 = self.addHost('ap10l2', ip='172.16.21.19/28')
        apaula = self.addHost('apaula', ip='172.16.21.21/28')

        d10l3_1 = self.addHost('d10l3_1', ip='172.16.21.33/27')
        d10l3_2 = self.addHost('d10l3_2', ip='172.16.21.34/27')
        ap10l3 = self.addHost('ap10l3', ip='172.16.21.35/27')

        # ========== ROUTERS (per-building) ==========
        # Kita buat router sebagai host Linux (enable IP forwarding later)
        r_g9 = self.addHost('r_g9')   # router for G9
        r_g10 = self.addHost('r_g10') # router for G10

        # ========== LINKS CORE TO BUILDINGS ==========
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)

        # ========== GEDUNG G9 LINKS ==========
        # Building to Floor 1
        self.addLink(g9_switch, g9_l1_switch)

        # Floor 1 to Floor 2 and Floor 3 (star via g9_l1_switch)
        self.addLink(g9_l1_switch, g9_l2_s1)
        self.addLink(g9_l1_switch, g9_l2_s2)
        self.addLink(g9_l1_switch, g9_l2_s3)
        self.addLink(g9_l1_switch, g9_l2_s4)

        self.addLink(g9_l1_switch, g9_l3_s1)
        self.addLink(g9_l1_switch, g9_l3_s2)
        self.addLink(g9_l1_switch, g9_l3_s3)
        self.addLink(g9_l1_switch, g9_l3_ap)

        # Connect G9 router to each floor-switch so router has interface in every subnet
        self.addLink(r_g9, g9_l1_switch)   # eth0 -> g9 floor1 subnet gateway
        self.addLink(r_g9, g9_l2_s1)       # eth1 -> g9 floor2 s1 gateway
        self.addLink(r_g9, g9_l2_s2)       # eth2
        self.addLink(r_g9, g9_l2_s3)       # eth3
        self.addLink(r_g9, g9_l2_s4)       # eth4
        self.addLink(r_g9, g9_l3_s1)       # eth5
        self.addLink(r_g9, g9_l3_s2)       # eth6
        self.addLink(r_g9, g9_l3_s3)       # eth7
        self.addLink(r_g9, g9_l3_ap)       # eth8

        # ========== GEDUNG G10 LINKS ==========
        self.addLink(g10_switch, g10_l1_switch)
        self.addLink(g10_l1_switch, g10_l2_switch)
        self.addLink(g10_l1_switch, g10_l3_switch)

        # Connect G10 router to each floor switch in G10
        self.addLink(r_g10, g10_l1_switch)  # eth0 -> g10 floor1
        self.addLink(r_g10, g10_l2_switch)  # eth1 -> g10 floor2
        self.addLink(r_g10, g10_l3_switch)  # eth2 -> g10 floor3

        # ========== HOST CONNECTIONS G9 ==========
        # Floor 1
        self.addLink(ap9l1, g9_l1_switch)
        self.addLink(rk9l1, g9_l1_switch)

        # Floor 2 - Switch 1 (Dosen)
        self.addLink(d9s1_1, g9_l2_s1)
        self.addLink(d9s1_2, g9_l2_s1)

        # Floor 2 - Switch 2 (Admin & Keuangan)
        self.addLink(ad9s2_1, g9_l2_s2)
        self.addLink(ad9s2_2, g9_l2_s2)

        # Floor 2 - Switch 3 (Pimpinan)
        self.addLink(p9s3_1, g9_l2_s3)
        self.addLink(p9s3_2, g9_l2_s3)

        # Floor 2 - Switch 4 (Ujian)
        self.addLink(uj9s4_1, g9_l2_s4)
        self.addLink(uj9s4_2, g9_l2_s4)

        # Floor 3 - Lab 1
        self.addLink(lab1_1, g9_l3_s1)
        self.addLink(lab1_2, g9_l3_s1)

        # Floor 3 - Lab 2
        self.addLink(lab2_1, g9_l3_s2)
        self.addLink(lab2_2, g9_l3_s2)

        # Floor 3 - Lab 3
        self.addLink(lab3_1, g9_l3_s3)
        self.addLink(lab3_2, g9_l3_s3)

        # Floor 3 - AP & Mahasiswa
        self.addLink(ap9l3_1, g9_l3_ap)
        self.addLink(ap9l3_2, g9_l3_ap)
        self.addLink(ap9l3_3, g9_l3_ap)

        # ========== HOST CONNECTIONS G10 ==========
        self.addLink(ap10l1, g10_l1_switch)
        self.addLink(rk10l1, g10_l1_switch)

        self.addLink(d10l2_1, g10_l2_switch)
        self.addLink(d10l2_2, g10_l2_switch)
        self.addLink(ap10l2, g10_l2_switch)
        self.addLink(apaula, g10_l2_switch)

        self.addLink(d10l3_1, g10_l3_switch)
        self.addLink(d10l3_2, g10_l3_switch)
        self.addLink(ap10l3, g10_l3_switch)


# Topo dict
topos = { 'dept_topo': ( lambda: DeptTopo() ) }

def configure_routing(net):
    """Configure per-building routing: router per building that routes among floors.
       No inter-building routing (G9 <-> G10) for option B.
    """
    print("Configuring per-building routing (G9 and G10 routers)...")

    # Subnet/gateway mapping
    gateways = {
        # G9
        'g9_f1': '192.168.10.1',
        'g9_f2s1': '192.168.10.33',
        'g9_f2s2': '192.168.10.65',
        'g9_f2s3': '192.168.10.97',
        'g9_f2s4': '192.168.10.129',
        'g9_f3s1': '192.168.10.161',
        'g9_f3s2': '192.168.10.193',
        'g9_f3s3': '192.168.10.225',
        'g9_f3ap': '192.168.10.241',

        # G10
        'g10_f1': '172.16.21.1',
        'g10_f2': '172.16.21.17',
        'g10_f3': '172.16.21.33',
    }

    # Assign IPs to router interfaces. We assume the order of links added in build() -> eth0, eth1, ...
    # For r_g9 we added links in this order: g9_l1_switch, g9_l2_s1, g9_l2_s2, g9_l2_s3, g9_l2_s4, g9_l3_s1, g9_l3_s2, g9_l3_s3, g9_l3_ap
    if 'r_g9' in net:
        r_g9 = net['r_g9']
        r_g9.cmd('sysctl -w net.ipv4.ip_forward=1')
        print("  ✓ IP forwarding enabled on r_g9")

        r_g9.cmd('ifconfig r_g9-eth0 192.168.10.1/27')   # floor1 gateway
        r_g9.cmd('ifconfig r_g9-eth1 192.168.10.33/27')  # f2 s1
        r_g9.cmd('ifconfig r_g9-eth2 192.168.10.65/27')  # f2 s2
        r_g9.cmd('ifconfig r_g9-eth3 192.168.10.97/27')  # f2 s3
        r_g9.cmd('ifconfig r_g9-eth4 192.168.10.129/27') # f2 s4
        r_g9.cmd('ifconfig r_g9-eth5 192.168.10.161/27') # f3 s1
        r_g9.cmd('ifconfig r_g9-eth6 192.168.10.193/27') # f3 s2
        r_g9.cmd('ifconfig r_g9-eth7 192.168.10.225/27') # f3 s3
        r_g9.cmd('ifconfig r_g9-eth8 192.168.10.241/28') # f3 ap

        print("  ✓ r_g9 interfaces configured")

    # For r_g10 we added links in this order: g10_l1_switch, g10_l2_switch, g10_l3_switch
    if 'r_g10' in net:
        r_g10 = net['r_g10']
        r_g10.cmd('sysctl -w net.ipv4.ip_forward=1')
        print("  ✓ IP forwarding enabled on r_g10")

        r_g10.cmd('ifconfig r_g10-eth0 172.16.21.1/28')  # floor1
        r_g10.cmd('ifconfig r_g10-eth1 172.16.21.17/28') # floor2
        r_g10.cmd('ifconfig r_g10-eth2 172.16.21.33/27') # floor3

        print("  ✓ r_g10 interfaces configured")

    # Set default gateway on each host to the router IP of its building/subnet.
    host_to_gw = {
        # G9 floor1
        'ap9l1': '192.168.10.1',
        'rk9l1': '192.168.10.1',

        # G9 floor2 s1
        'd9s1_1': '192.168.10.33',
        'd9s1_2': '192.168.10.33',

        # G9 floor2 s2
        'ad9s2_1': '192.168.10.65',
        'ad9s2_2': '192.168.10.65',

        # G9 floor2 s3
        'p9s3_1': '192.168.10.97',
        'p9s3_2': '192.168.10.97',

        # G9 floor2 s4
        'uj9s4_1': '192.168.10.129',
        'uj9s4_2': '192.168.10.129',

        # G9 floor3 labs & ap
        'lab1_1': '192.168.10.161',
        'lab1_2': '192.168.10.161',
        'lab2_1': '192.168.10.193',
        'lab2_2': '192.168.10.193',
        'lab3_1': '192.168.10.225',
        'lab3_2': '192.168.10.225',
        'ap9l3_1': '192.168.10.241',
        'ap9l3_2': '192.168.10.241',
        'ap9l3_3': '192.168.10.241',

        # G10
        'ap10l1': '172.16.21.1',
        'rk10l1': '172.16.21.1',

        'd10l2_1': '172.16.21.17',
        'd10l2_2': '172.16.21.17',
        'ap10l2': '172.16.21.17',
        'apaula': '172.16.21.17',

        'd10l3_1': '172.16.21.33',
        'd10l3_2': '172.16.21.33',
        'ap10l3': '172.16.21.33',
    }

    for host_name, gw in host_to_gw.items():
        if host_name in net:
            h = net[host_name]
            # flush any existing default route to avoid duplicates
            h.cmd('ip route del default || true')
            h.cmd(f'ip route add default via {gw}')
            print(f"  ✓ {host_name}: default via {gw}")

    print("  ✓ Per-building routing configured (no inter-building routes).")

def test_connectivity(net):
    """Simple connectivity tests (ping same-building across floors)."""
    print("\n=== TEST CONNECTIVITY (per-building) ===")

    tests = [
        # G9 internal: hop across floors using router
        ('ap9l1', 'd9s1_1'),
        ('d9s1_1', 'lab1_1'),
        ('lab2_1', 'ap9l3_1'),
        # G10 internal
        ('ap10l1', 'd10l2_1'),
        ('d10l3_1', 'rk10l1'),
        # cross-building (should fail or be unreachable by design)
        ('ap9l1', 'ap10l1'),
    ]

    for h1_name, h2_name in tests:
        if h1_name in net and h2_name in net:
            h1 = net[h1_name]
            h2 = net[h2_name]
            print(f"\nTesting: {h1_name} -> {h2_name} ({h2.IP()})")
            result = h1.cmd('ping -c 3 -W 2 %s' % h2.IP())
            if '0% packet loss' in result or '1 packets received' in result:
                print(f"  ✓ SUCCESS: {h1_name} can reach {h2_name}")
            else:
                print(f"  ✗ FAILED / BLOCKED: {h1_name} cannot reach {h2_name}")
                # print brief ping output
                print(result.splitlines()[:4])

    print("\n=== CONNECTIVITY TESTING DONE ===")

def run():
    topo = DeptTopo()
    net = Mininet(topo=topo,
                  controller=RemoteController(name='c0', ip='127.0.0.1'),
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)

    print("\n*** Starting network (Dept topology)...")
    net.start()

    print("*** Configuring routing (per-building routers)...")
    configure_routing(net)

    print("*** Running connectivity tests...")
    test_connectivity(net)

    print("\n*** Entering CLI (type 'exit' to stop)...")
    CLI(net)

    print("*** Stopping network...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
