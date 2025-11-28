from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DeptTopo(Topo):
    def build(self):
        # Core Switch
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

        # ========== GEDUNG G9 - FLOOR 1 (192.168.10.0/27) ==========
        # Ruang Kuliah + AP Mahasiswa
        ap9l1 = self.addHost('ap9l1', ip='192.168.10.1/27')
        rk9l1 = self.addHost('rk9l1', ip='192.168.10.2/27')

        # ========== GEDUNG G9 - FLOOR 2 ==========
        # Switch 1: Dosen (192.168.10.32/27)
        d9s1_1 = self.addHost('d9s1_1', ip='192.168.10.33/27')
        d9s1_2 = self.addHost('d9s1_2', ip='192.168.10.34/27')

        # Switch 2: Administrasi & Keuangan (192.168.10.64/27)
        ad9s2_1 = self.addHost('ad9s2_1', ip='192.168.10.65/27')
        ad9s2_2 = self.addHost('ad9s2_2', ip='192.168.10.66/27')

        # Switch 3: Pimpinan & Sekretariat (192.168.10.96/27)
        p9s3_1 = self.addHost('p9s3_1', ip='192.168.10.97/27')
        p9s3_2 = self.addHost('p9s3_2', ip='192.168.10.98/27')

        # Switch 4: Ujian & Mahasiswa (192.168.10.128/27)
        uj9s4_1 = self.addHost('uj9s4_1', ip='192.168.10.129/27')
        uj9s4_2 = self.addHost('uj9s4_2', ip='192.168.10.130/27')

        # ========== GEDUNG G9 - FLOOR 3 ==========
        # Switch 1: Lab 1 (192.168.10.160/27)
        lab1_1 = self.addHost('lab1_1', ip='192.168.10.161/27')
        lab1_2 = self.addHost('lab1_2', ip='192.168.10.162/27')

        # Switch 2: Lab 2 (192.168.10.192/27)
        lab2_1 = self.addHost('lab2_1', ip='192.168.10.193/27')
        lab2_2 = self.addHost('lab2_2', ip='192.168.10.194/27')

        # Switch 3: Lab 3 (192.168.10.224/27)
        lab3_1 = self.addHost('lab3_1', ip='192.168.10.225/27')
        lab3_2 = self.addHost('lab3_2', ip='192.168.10.226/27')

        # AP Switch: AP & Mahasiswa (192.168.10.240/28)
        ap9l3_1 = self.addHost('ap9l3_1', ip='192.168.10.241/28')
        ap9l3_2 = self.addHost('ap9l3_2', ip='192.168.10.242/28')
        ap9l3_3 = self.addHost('ap9l3_3', ip='192.168.10.243/28')

        # ========== GEDUNG G10 - FLOOR 1 (172.16.21.0/28) ==========
        # Ruang Kuliah + AP Mahasiswa
        ap10l1 = self.addHost('ap10l1', ip='172.16.21.1/28')
        rk10l1 = self.addHost('rk10l1', ip='172.16.21.2/28')

        # ========== GEDUNG G10 - FLOOR 2 (172.16.21.16/28) ==========
        # Dosen + AP Mahasiswa + AP Aula
        d10l2_1 = self.addHost('d10l2_1', ip='172.16.21.17/28')
        d10l2_2 = self.addHost('d10l2_2', ip='172.16.21.18/28')
        ap10l2 = self.addHost('ap10l2', ip='172.16.21.19/28')
        apaula = self.addHost('apaula', ip='172.16.21.21/28')

        # ========== GEDUNG G10 - FLOOR 3 (172.16.21.32/27) ==========
        # Dosen + AP Mahasiswa
        d10l3_1 = self.addHost('d10l3_1', ip='172.16.21.33/27')
        d10l3_2 = self.addHost('d10l3_2', ip='172.16.21.34/27')
        ap10l3 = self.addHost('ap10l3', ip='172.16.21.35/27')

        # ========== LINK CORE TO BUILDINGS ==========
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)

        # ========== GEDUNG G9 LINKS ==========
        # Building to Floor 1
        self.addLink(g9_switch, g9_l1_switch)
        
        # Floor 1 to Floor 2 switches (star topology - each floor 2 switch connects to floor 1)
        self.addLink(g9_l1_switch, g9_l2_s1)
        self.addLink(g9_l1_switch, g9_l2_s2)
        self.addLink(g9_l1_switch, g9_l2_s3)
        self.addLink(g9_l1_switch, g9_l2_s4)

        # Floor 1 to Floor 3 switches (star topology - each floor 3 switch connects to floor 1)
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

topos = { 'dept_topo': ( lambda: DeptTopo() ) }

def configure_routing(net):
    """Configure comprehensive static routing between different subnets"""
    print("Mengkonfigurasi routing lengkap untuk seluruh topology...")

    # Enable IP forwarding pada semua switch yang bertindak sebagai router
    print("1. Enable IP forwarding pada switch...")
    router_switches = ['g9', 'g10', 'g9l1', 'g9l2s1', 'g9l2s2', 'g9l2s3', 'g9l2s4',
                       'g9l3s1', 'g9l3s2', 'g9l3s3', 'g9l3ap', 'g10l1', 'g10l2', 'g10l3', 's0']

    for switch_name in router_switches:
        if switch_name in net:
            switch = net[switch_name]
            switch.cmd('sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1')
            print(f"  ✓ IP forwarding enabled on {switch_name}")

    # Konfigurasi routing untuk semua host
    print("2. Mengkonfigurasi static routing untuk setiap host...")

    # Complete subnet mapping
    all_subnets = {
        # G9 Building subnets
        'g9_f1': '192.168.10.0/27',     # Floor 1
        'g9_f2s1': '192.168.10.32/27',   # Floor 2 Switch 1 (Dosen)
        'g9_f2s2': '192.168.10.64/27',   # Floor 2 Switch 2 (Admin & Keuangan)
        'g9_f2s3': '192.168.10.96/27',   # Floor 2 Switch 3 (Pimpinan)
        'g9_f2s4': '192.168.10.128/27',  # Floor 2 Switch 4 (Ujian)
        'g9_f3s1': '192.168.10.160/27',  # Floor 3 Switch 1 (Lab 1)
        'g9_f3s2': '192.168.10.192/27',  # Floor 3 Switch 2 (Lab 2)
        'g9_f3s3': '192.168.10.224/27',  # Floor 3 Switch 3 (Lab 3)
        'g9_f3ap': '192.168.10.240/28',  # Floor 3 AP & Mahasiswa

        # G10 Building subnets
        'g10_f1': '172.16.21.0/28',      # Floor 1
        'g10_f2': '172.16.21.16/28',     # Floor 2
        'g10_f3': '172.16.21.32/27',     # Floor 3
    }

    # Gateway addresses untuk setiap subnet (host pertama dalam subnet)
    gateways = {
        'g9_f1': '192.168.10.1',         # ap9l1
        'g9_f2s1': '192.168.10.33',      # d9s1_1
        'g9_f2s2': '192.168.10.65',      # ad9s2_1
        'g9_f2s3': '192.168.10.97',      # p9s3_1
        'g9_f2s4': '192.168.10.129',     # uj9s4_1
        'g9_f3s1': '192.168.10.161',     # lab1_1
        'g9_f3s2': '192.168.10.193',     # lab2_1
        'g9_f3s3': '192.168.10.225',     # lab3_1
        'g9_f3ap': '192.168.10.241',     # ap9l3_1

        'g10_f1': '172.16.21.1',         # ap10l1
        'g10_f2': '172.16.21.17',        # d10l2_1
        'g10_f3': '172.16.21.33',        # d10l3_1
    }

    # Host configuration berdasarkan lokasi dan subnet
    host_configs = {
        # G9 Floor 1 hosts (192.168.10.0/27)
        'ap9l1': {
            'subnet': 'g9_f1',
            'gateway': '192.168.10.1',
            'interface': 'ap9l1-eth0'
        },
        'rk9l1': {
            'subnet': 'g9_f1',
            'gateway': '192.168.10.2',
            'interface': 'rk9l1-eth0'
        },

        # G9 Floor 2 Switch 1 hosts (192.168.10.32/27) - Dosen
        'd9s1_1': {
            'subnet': 'g9_f2s1',
            'gateway': '192.168.10.33',
            'interface': 'd9s1_1-eth0'
        },
        'd9s1_2': {
            'subnet': 'g9_f2s1',
            'gateway': '192.168.10.34',
            'interface': 'd9s1_2-eth0'
        },

        # G9 Floor 2 Switch 2 hosts (192.168.10.64/27) - Administrasi & Keuangan
        'ad9s2_1': {
            'subnet': 'g9_f2s2',
            'gateway': '192.168.10.65',
            'interface': 'ad9s2_1-eth0'
        },
        'ad9s2_2': {
            'subnet': 'g9_f2s2',
            'gateway': '192.168.10.66',
            'interface': 'ad9s2_2-eth0'
        },

        # G9 Floor 2 Switch 3 hosts (192.168.10.96/27) - Pimpinan & Sekretariat
        'p9s3_1': {
            'subnet': 'g9_f2s3',
            'gateway': '192.168.10.97',
            'interface': 'p9s3_1-eth0'
        },
        'p9s3_2': {
            'subnet': 'g9_f2s3',
            'gateway': '192.168.10.98',
            'interface': 'p9s3_2-eth0'
        },

        # G9 Floor 2 Switch 4 hosts (192.168.10.128/27) - Ujian & Mahasiswa
        'uj9s4_1': {
            'subnet': 'g9_f2s4',
            'gateway': '192.168.10.129',
            'interface': 'uj9s4_1-eth0'
        },
        'uj9s4_2': {
            'subnet': 'g9_f2s4',
            'gateway': '192.168.10.130',
            'interface': 'uj9s4_2-eth0'
        },

        # G9 Floor 3 Lab 1 hosts (192.168.10.160/27)
        'lab1_1': {
            'subnet': 'g9_f3s1',
            'gateway': '192.168.10.161',
            'interface': 'lab1_1-eth0'
        },
        'lab1_2': {
            'subnet': 'g9_f3s1',
            'gateway': '192.168.10.162',
            'interface': 'lab1_2-eth0'
        },

        # G9 Floor 3 Lab 2 hosts (192.168.10.192/27)
        'lab2_1': {
            'subnet': 'g9_f3s2',
            'gateway': '192.168.10.193',
            'interface': 'lab2_1-eth0'
        },
        'lab2_2': {
            'subnet': 'g9_f3s2',
            'gateway': '192.168.10.194',
            'interface': 'lab2_2-eth0'
        },

        # G9 Floor 3 Lab 3 hosts (192.168.10.224/27)
        'lab3_1': {
            'subnet': 'g9_f3s3',
            'gateway': '192.168.10.225',
            'interface': 'lab3_1-eth0'
        },
        'lab3_2': {
            'subnet': 'g9_f3s3',
            'gateway': '192.168.10.226',
            'interface': 'lab3_2-eth0'
        },

        # G9 Floor 3 AP hosts (192.168.10.240/28)
        'ap9l3_1': {
            'subnet': 'g9_f3ap',
            'gateway': '192.168.10.241',
            'interface': 'ap9l3_1-eth0'
        },
        'ap9l3_2': {
            'subnet': 'g9_f3ap',
            'gateway': '192.168.10.242',
            'interface': 'ap9l3_2-eth0'
        },
        'ap9l3_3': {
            'subnet': 'g9_f3ap',
            'gateway': '192.168.10.243',
            'interface': 'ap9l3_3-eth0'
        },

        # G10 Floor 1 hosts (172.16.21.0/28)
        'ap10l1': {
            'subnet': 'g10_f1',
            'gateway': '172.16.21.1',
            'interface': 'ap10l1-eth0'
        },
        'rk10l1': {
            'subnet': 'g10_f1',
            'gateway': '172.16.21.2',
            'interface': 'rk10l1-eth0'
        },

        # G10 Floor 2 hosts (172.16.21.16/28)
        'd10l2_1': {
            'subnet': 'g10_f2',
            'gateway': '172.16.21.17',
            'interface': 'd10l2_1-eth0'
        },
        'd10l2_2': {
            'subnet': 'g10_f2',
            'gateway': '172.16.21.18',
            'interface': 'd10l2_2-eth0'
        },
        'ap10l2': {
            'subnet': 'g10_f2',
            'gateway': '172.16.21.19',
            'interface': 'ap10l2-eth0'
        },
        'apaula': {
            'subnet': 'g10_f2',
            'gateway': '172.16.21.21',
            'interface': 'apaula-eth0'
        },

        # G10 Floor 3 hosts (172.16.21.32/27)
        'd10l3_1': {
            'subnet': 'g10_f3',
            'gateway': '172.16.21.33',
            'interface': 'd10l3_1-eth0'
        },
        'd10l3_2': {
            'subnet': 'g10_f3',
            'gateway': '172.16.21.34',
            'interface': 'd10l3_2-eth0'
        },
        'ap10l3': {
            'subnet': 'g10_f3',
            'gateway': '172.16.21.35',
            'interface': 'ap10l3-eth0'
        },
    }

    # Apply routing configuration untuk setiap host
    for host_name, config in host_configs.items():
        if host_name in net:
            host = net[host_name]
            current_subnet = config['subnet']
            interface = config['interface']

            # Enable IP forwarding pada host
            host.cmd('sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1')

            # Tambahkan routes ke semua subnet lainnya
            for subnet_key, subnet_cidr in all_subnets.items():
                if subnet_key != current_subnet:
                    if subnet_key.startswith('g9_') and current_subnet.startswith('g9_'):
                        # G9 internal routing via gateway
                        gateway = gateways[current_subnet] if host_name.endswith('_1') else config['gateway']
                        cmd = f'ip route add {subnet_cidr} via {gateway} dev {interface}'
                    elif subnet_key.startswith('g10_') and current_subnet.startswith('g10_'):
                        # G10 internal routing via gateway
                        gateway = gateways[current_subnet] if host_name.endswith('_1') else config['gateway']
                        cmd = f'ip route add {subnet_cidr} via {gateway} dev {interface}'
                    else:
                        # Inter-building routing
                        if current_subnet.startswith('g9_'):
                            # G9 to G10 routing via core switches
                            cmd = f'ip route add {subnet_cidr} dev {interface}'
                        else:
                            # G10 to G9 routing via core switches
                            cmd = f'ip route add {subnet_cidr} dev {interface}'

                    result = host.cmd(cmd)
                    print(f"  ✓ {host_name}: route {subnet_cidr}")

    print("  ✓ Routing configuration completed untuk semua host")

    """Comprehensive test connectivity between all subnets and buildings"""
    print("\n=== KOMPREHENSIF CONNECTIVITY TESTING ===")

    # Test matrix untuk berbagai skenario koneksi
    test_scenarios = {
        "SAME SUBNET - G9 FLOOR 1": [('ap9l1', 'rk9l1')],
        "SAME SUBNET - G9 FLOOR 2 DOSEN": [('d9s1_1', 'd9s1_2')],
        "SAME SUBNET - G9 FLOOR 2 ADMIN": [('ad9s2_1', 'ad9s2_2')],
        "SAME SUBNET - G9 FLOOR 2 PIMPINAN": [('p9s3_1', 'p9s3_2')],
        "SAME SUBNET - G9 FLOOR 2 UJIAN": [('uj9s4_1', 'uj9s4_2')],
        "SAME SUBNET - G9 FLOOR 3 LAB 1": [('lab1_1', 'lab1_2')],
        "SAME SUBNET - G9 FLOOR 3 LAB 2": [('lab2_1', 'lab2_2')],
        "SAME SUBNET - G9 FLOOR 3 LAB 3": [('lab3_1', 'lab3_2')],
        "SAME SUBNET - G9 FLOOR 3 AP": [('ap9l3_1', 'ap9l3_2')],

        "SAME SUBNET - G10 FLOOR 1": [('ap10l1', 'rk10l1')],
        "SAME SUBNET - G10 FLOOR 2": [('d10l2_1', 'd10l2_2')],
        "SAME SUBNET - G10 FLOOR 3": [('d10l3_1', 'd10l3_2')],

        "CROSS SUBNET - G9 INTERNAL": [
            ('ap9l1', 'ad9s2_1'),      # Floor 1 -> Floor 2 Admin
            ('rk9l1', 'd9s1_1'),       # Floor 1 -> Floor 2 Dosen
            ('ad9s2_1', 'p9s3_1'),     # Floor 2 Admin -> Floor 2 Pimpinan
            ('d9s1_1', 'lab1_1'),      # Floor 2 Dosen -> Floor 3 Lab 1
            ('lab1_1', 'ap9l3_1'),     # Floor 3 Lab -> Floor 3 AP
        ],

        "CROSS BUILDING - G9 TO G10": [
            ('ap9l1', 'ap10l1'),       # G9 Floor 1 -> G10 Floor 1
            ('ad9s2_1', 'd10l2_1'),    # G9 Floor 2 Admin -> G10 Floor 2 Dosen
            ('lab1_1', 'd10l3_1'),     # G9 Floor 3 Lab -> G10 Floor 3 Dosen
        ]
    }

    total_tests = 0
    successful_tests = 0

    for scenario_name, test_pairs in test_scenarios.items():
        print(f"\n--- {scenario_name} ---")

        for host1_name, host2_name in test_pairs:
            if host1_name in net and host2_name in net:
                host1 = net[host1_name]
                host2 = net[host2_name]
                target_ip = host2.IP()

                print(f"\nTesting: {host1_name} -> {host2_name} ({target_ip})")

                # Cek routing table host1
                print(f"  {host1_name} routing table:")
                routes = host1.cmd('ip route | grep -E "(192.168|172.16)"')
                if routes.strip():
                    for line in routes.split('\n'):
                        if line.strip():
                            print(f"    {line}")
                else:
                    print("    No specific routes found")

                # Lakukan ping test
                total_tests += 1
                ping_result = host1.cmd(f'ping -c 3 -W 2 {target_ip}')

                if "0% packet loss" in ping_result or "1 packets received" in ping_result:
                    print(f"  ✓ SUCCESS: {host1_name} can reach {host2_name}")
                    successful_tests += 1
                elif "100% packet loss" in ping_result:
                    print(f"  ✗ FAILED: {host1_name} cannot reach {host2_name}")
                else:
                    print(f"  ? PARTIAL: {host1_name} -> {host2_name}")
                    print(f"    {ping_result.split(chr(10))[0] if chr(10) in ping_result else ping_result}")
            else:
                missing_hosts = []
                if host1_name not in net:
                    missing_hosts.append(host1_name)
                if host2_name not in net:
                    missing_hosts.append(host2_name)
                print(f"  ⚠ Skipping {host1_name} -> {host2_name} (missing: {', '.join(missing_hosts)})")

    print(f"\n=== CONNECTIVITY SUMMARY ===")
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")

    # Advanced testing: Check if hosts can resolve each other's names
    print(f"\n=== ADVANCED TESTING ===")
    print("Testing host name resolution...")

    name_test_pairs = [
        ('ap9l1', 'ad9s2_1'),
        ('lab1_1', 'ap10l1'),
        ('d10l2_1', 'p9s3_1')
    ]

    for host1_name, host2_name in name_test_pairs:
        if host1_name in net and host2_name in net:
            host1 = net[host1_name]
            host2 = net[host2_name]

            print(f"\nName resolution: {host1_name} trying to reach {host2_name}")

            # Coba ping dengan hostname
            try:
                name_result = host1.cmd(f'ping -c 1 -W 1 {host2_name}')
                if "1 packets received" in name_result:
                    print(f"  ✓ Name resolution successful")
                else:
                    print(f"  ⚠ Name resolution failed, trying IP...")
                    ip_result = host1.cmd(f'ping -c 1 -W 1 {host2.IP()}')
                    if "1 packets received" in ip_result:
                        print(f"  ✓ IP resolution successful")
                    else:
                        print(f"  ✗ IP resolution failed")
            except:
                print(f"  ✗ Name resolution error")

    print(f"\n=== NETWORK DIAGNOSTICS ===")
    print("Checking network interfaces and ARP tables...")

    diagnostic_hosts = ['ap9l1', 'ad9s2_1', 'ap10l1', 'lab1_1']

    for host_name in diagnostic_hosts:
        if host_name in net:
            host = net[host_name]
            print(f"\n{host_name} diagnostics:")

            # Interface information
            interfaces = host.cmd('ip addr show')
            print(f"  Interfaces: {len([line for line in interfaces.split('\n') if 'inet' in line])} active")

            # ARP table
            arp_table = host.cmd('arp -n')
            arp_entries = len([line for line in arp_table.split('\n') if line.strip() and not line.startswith('Address')])
            print(f"  ARP entries: {arp_entries}")

            # Default gateway
            gateway = host.cmd('ip route | grep default')
            if gateway.strip():
                print(f"  Default gateway: {gateway.strip()}")

    print(f"\n=== TESTING COMPLETED ===")


def run():
    topo = DeptTopo()
    
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)
    
    print("\n*** Memulai Jaringan (Departemen Topology)...")
    net.start()

    print("*** Konfigurasi routing untuk antar subnet...")
    configure_routing(net)

    print("*** Testing koneksi...")
    test_connectivity(net)

    print("\n*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()