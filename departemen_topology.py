from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch, Host
from mininet.cli import CLI
from mininet.log import setLogLevel
import os

class Router(Host):
    """Custom Router class for routing between subnets"""
    def config(self, **params):
        super(Router, self).config(**params)
        # Enable IP forwarding
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        # Disable reverse path filtering
        self.cmd('sysctl -w net.ipv4.conf.all.rp_filter=0')
        self.cmd('sysctl -w net.ipv4.conf.default.rp_filter=0')

class DeptTopoFixed(Topo):
    def build(self):
        # Core Switch
        core_switch = self.addSwitch('s0')

        # Building Switches
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')

        # Building Routers untuk inter-subnet routing
        router_g9 = self.addNode('router_g9', cls=Router, ip='192.168.10.254/24')
        router_g10 = self.addNode('router_g10', cls=Router, ip='172.16.21.254/24')

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

        # ========== GEDUNG G9 - FLOOR 1 (192.168.10.0/27) ==========
        # Ruang Kuliah + AP Mahasiswa
        ap9l1 = self.addHost('ap9l1', ip='192.168.10.1/27', defaultRoute='via 192.168.10.254')
        rk9l1 = self.addHost('rk9l1', ip='192.168.10.2/27', defaultRoute='via 192.168.10.254')

        # ========== GEDUNG G9 - FLOOR 2 ==========
        # Switch 1: Dosen (192.168.10.32/27)
        d9s1_1 = self.addHost('d9s1_1', ip='192.168.10.33/27', defaultRoute='via 192.168.10.254')
        d9s1_2 = self.addHost('d9s1_2', ip='192.168.10.34/27', defaultRoute='via 192.168.10.254')

        # Switch 2: Administrasi & Keuangan (192.168.10.64/27)
        ad9s2_1 = self.addHost('ad9s2_1', ip='192.168.10.65/27', defaultRoute='via 192.168.10.254')
        ad9s2_2 = self.addHost('ad9s2_2', ip='192.168.10.66/27', defaultRoute='via 192.168.10.254')

        # Switch 3: Pimpinan & Sekretariat (192.168.10.96/27)
        p9s3_1 = self.addHost('p9s3_1', ip='192.168.10.97/27', defaultRoute='via 192.168.10.254')
        p9s3_2 = self.addHost('p9s3_2', ip='192.168.10.98/27', defaultRoute='via 192.168.10.254')

        # Switch 4: Ujian & Mahasiswa (192.168.10.128/27)
        uj9s4_1 = self.addHost('uj9s4_1', ip='192.168.10.129/27', defaultRoute='via 192.168.10.254')
        uj9s4_2 = self.addHost('uj9s4_2', ip='192.168.10.130/27', defaultRoute='via 192.168.10.254')

        # ========== GEDUNG G9 - FLOOR 3 ==========
        # Switch 1: Lab 1 (192.168.10.160/27)
        lab1_1 = self.addHost('lab1_1', ip='192.168.10.161/27', defaultRoute='via 192.168.10.254')
        lab1_2 = self.addHost('lab1_2', ip='192.168.10.162/27', defaultRoute='via 192.168.10.254')

        # Switch 2: Lab 2 (192.168.10.192/27)
        lab2_1 = self.addHost('lab2_1', ip='192.168.10.193/27', defaultRoute='via 192.168.10.254')
        lab2_2 = self.addHost('lab2_2', ip='192.168.10.194/27', defaultRoute='via 192.168.10.254')

        # Switch 3: Lab 3 (192.168.10.224/27)
        lab3_1 = self.addHost('lab3_1', ip='192.168.10.225/27', defaultRoute='via 192.168.10.254')
        lab3_2 = self.addHost('lab3_2', ip='192.168.10.226/27', defaultRoute='via 192.168.10.254')

        # AP Switch: AP & Mahasiswa (192.168.10.240/28)
        ap9l3_1 = self.addHost('ap9l3_1', ip='192.168.10.241/28', defaultRoute='via 192.168.10.254')
        ap9l3_2 = self.addHost('ap9l3_2', ip='192.168.10.242/28', defaultRoute='via 192.168.10.254')
        ap9l3_3 = self.addHost('ap9l3_3', ip='192.168.10.243/28', defaultRoute='via 192.168.10.254')

        # ========== GEDUNG G10 - FLOOR 1 (172.16.21.0/28) ==========
        # Ruang Kuliah + AP Mahasiswa
        ap10l1 = self.addHost('ap10l1', ip='172.16.21.1/28', defaultRoute='via 172.16.21.254')
        rk10l1 = self.addHost('rk10l1', ip='172.16.21.2/28', defaultRoute='via 172.16.21.254')

        # ========== GEDUNG G10 - FLOOR 2 (172.16.21.16/28) ==========
        # Dosen + AP Mahasiswa + AP Aula
        d10l2_1 = self.addHost('d10l2_1', ip='172.16.21.17/28', defaultRoute='via 172.16.21.254')
        d10l2_2 = self.addHost('d10l2_2', ip='172.16.21.18/28', defaultRoute='via 172.16.21.254')
        ap10l2 = self.addHost('ap10l2', ip='172.16.21.19/28', defaultRoute='via 172.16.21.254')
        apaula = self.addHost('apaula', ip='172.16.21.21/28', defaultRoute='via 172.16.21.254')

        # ========== GEDUNG G10 - FLOOR 3 (172.16.21.32/27) ==========
        # Dosen + AP Mahasiswa
        d10l3_1 = self.addHost('d10l3_1', ip='172.16.21.33/27', defaultRoute='via 172.16.21.254')
        d10l3_2 = self.addHost('d10l3_2', ip='172.16.21.34/27', defaultRoute='via 172.16.21.254')
        ap10l3 = self.addHost('ap10l3', ip='172.16.21.35/27', defaultRoute='via 172.16.21.254')

        # ========== LINK CORE TO BUILDINGS ==========
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)

        # ========== ROUTER CONNECTIONS ==========
        # Hubungkan router ke core switches
        self.addLink(router_g9, g9_switch)
        self.addLink(router_g10, g10_switch)

        # Inter-building router connection
        self.addLink(router_g9, router_g10)

        # ========== GEDUNG G9 LINKS ==========
        # Building to Floor 1
        self.addLink(g9_switch, g9_l1_switch)

        # Floor 1 to Floor 2 switches (star topology)
        self.addLink(g9_l1_switch, g9_l2_s1)
        self.addLink(g9_l1_switch, g9_l2_s2)
        self.addLink(g9_l1_switch, g9_l2_s3)
        self.addLink(g9_l1_switch, g9_l2_s4)

        # Floor 1 to Floor 3 switches (star topology)
        self.addLink(g9_l1_switch, g9_l3_s1)
        self.addLink(g9_l1_switch, g9_l3_s2)
        self.addLink(g9_l1_switch, g9_l3_s3)
        self.addLink(g9_l1_switch, g9_l3_ap)

        # ========== GEDUNG G10 LINKS ==========
        # Building to Floors
        self.addLink(g10_switch, g10_l1_switch)
        self.addLink(g10_l1_switch, g10_l2_switch)
        self.addLink(g10_l1_switch, g10_l3_switch)

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

        # Floor 3 - Switch 1 (Lab 1)
        self.addLink(lab1_1, g9_l3_s1)
        self.addLink(lab1_2, g9_l3_s1)

        # Floor 3 - Switch 2 (Lab 2)
        self.addLink(lab2_1, g9_l3_s2)
        self.addLink(lab2_2, g9_l3_s2)

        # Floor 3 - Switch 3 (Lab 3)
        self.addLink(lab3_1, g9_l3_s3)
        self.addLink(lab3_2, g9_l3_s3)

        # Floor 3 - AP & Mahasiswa
        self.addLink(ap9l3_1, g9_l3_ap)
        self.addLink(ap9l3_2, g9_l3_ap)
        self.addLink(ap9l3_3, g9_l3_ap)

        # ========== HOST CONNECTIONS G10 ==========
        # Floor 1
        self.addLink(ap10l1, g10_l1_switch)
        self.addLink(rk10l1, g10_l1_switch)

        # Floor 2
        self.addLink(d10l2_1, g10_l2_switch)
        self.addLink(d10l2_2, g10_l2_switch)
        self.addLink(ap10l2, g10_l2_switch)
        self.addLink(apaula, g10_l2_switch)

        # Floor 3
        self.addLink(d10l3_1, g10_l3_switch)
        self.addLink(d10l3_2, g10_l3_switch)
        self.addLink(ap10l3, g10_l3_switch)

topos = { 'dept_topo_fixed': ( lambda: DeptTopoFixed() ) }

def configure_routing(net):
    """Configure routing between routers and buildings"""
    print("Mengkonfigurasi routing antar gedung...")

    # Configure router interfaces
    router_g9 = net['router_g9']
    router_g10 = net['router_g10']

    # Get router interface names
    router_g9_intfs = router_g9.intfNames()
    router_g10_intfs = router_g10.intfNames()

    # Configure additional router interfaces for inter-building routing
    # Router G9 ke G10
    router_g9.cmd('ip addr add 10.0.0.1/24 dev router_g9-eth1')
    router_g10.cmd('ip addr add 10.0.0.2/24 dev router_g10-eth1')

    # Add routing tables
    # Router G9: route ke G10 network via router_g10
    router_g9.cmd('ip route add 172.16.21.0/16 via 10.0.0.2 dev router_g9-eth1')

    # Router G10: route ke G9 network via router_g9
    router_g10.cmd('ip route add 192.168.10.0/24 via 10.0.0.1 dev router_g10-eth1')

    print("  ✓ Router G9: 192.168.10.0/24 -> local, 172.16.21.0/16 via 10.0.0.2")
    print("  ✓ Router G10: 172.16.21.0/16 -> local, 192.168.10.0/24 via 10.0.0.1")

    print("  ✓ Routing configuration completed")

def test_connectivity(net):
    """Test basic connectivity between key hosts"""
    print("\n=== BASIC CONNECTIVITY TESTING ===")

    test_cases = [
        ("Same Subnet G9", "d9s1_1", "d9s1_2"),
        ("Same Subnet G10", "d10l2_1", "d10l2_2"),
        ("Cross Subnet G9", "d9s1_1", "rk9l1"),
        ("Cross Building G9->G10", "d9s1_1", "d10l2_1"),
        ("Ping Gateway G9", "d9s1_1", "192.168.10.254"),
        ("Ping Gateway G10", "d10l2_1", "172.16.21.254")
    ]

    for test_name, host_name, target in test_cases:
        if host_name in net:
            host = net[host_name]

            if target.replace('.', '').isdigit():  # IP address
                print(f"\n{test_name}: {host_name} -> {target}")
                result = host.cmd(f'ping -c 2 -W 2 {target}')
            else:  # hostname
                if target in net:
                    target_host = net[target]
                    target_ip = target_host.IP()
                    print(f"\n{test_name}: {host_name} -> {target} ({target_ip})")
                    result = host.cmd(f'ping -c 2 -W 2 {target_ip}')
                else:
                    print(f"\n{test_name}: {host_name} -> {target} (target not found)")
                    continue

            if "0% packet loss" in result or "2 packets received" in result or "1 packets received" in result:
                print(f"  ✓ SUCCESS")
            else:
                print(f"  ✗ FAILED")
                # Show routing info for debugging
                routes = host.cmd('ip route')
                print(f"    Routes: {len(routes.split())} routes configured")
        else:
            print(f"\n{test_name}: {host_name} not found")

def run():
    topo = DeptTopoFixed()

    net = Mininet(topo=topo,
                  controller=RemoteController(name='c0', ip='127.0.0.1'),
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)

    print("\n*** Memulai Jaringan (Departemen Topology Fixed with Router)...")
    net.start()

    print("*** Konfigurasi routing...")
    configure_routing(net)

    print("*** Testing koneksi dasar...")
    test_connectivity(net)

    print("\n*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    print("\nCommands to try:")
    print("  d9s1_1 ping rk9l1")
    print("  d9s1_1 ping d10l2_1")
    print("  d10l2_1 ping rk9l1")
    print("  ip route show")
    CLI(net)

    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()