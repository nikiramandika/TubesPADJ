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
    # Enable IP forwarding pada semua switch yang bertindak sebagai router
    router_switches = ['g9', 'g10', 'g9l1', 'g9l2s1', 'g9l2s2', 'g9l2s3', 'g9l2s4',
                       'g9l3s1', 'g9l3s2', 'g9l3s3', 'g9l3ap', 'g10l1', 'g10l2', 'g10l3', 's0']

    for switch_name in router_switches:
        if switch_name in net:
            switch = net[switch_name]
            switch.cmd('sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1')

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

    print("\n*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()