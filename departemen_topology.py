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


def run():
    topo = DeptTopo()
    
    net = Mininet(topo=topo, 
                  controller=RemoteController(name='c0', ip='127.0.0.1'), 
                  switch=OVSKernelSwitch,
                  autoSetMacs=True)
    
    print("\n*** Memulai Jaringan (Departemen Topology)...")
    net.start()
    
    print("*** Menjalankan Ping Test...")
    # Simple ping test to verify connectivity
    print("Ping: ap9l1 -> rk9l1")
    net.pingPair((net['ap9l1'], net['rk9l1']))
    
    print("\n*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()