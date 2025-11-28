from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from functools import partial # PENTING: Untuk memaksa OF 1.3

class DeptTopo(Topo):
    def build(self):
        # Switch Multicore (pusat)
        core_switch = self.addSwitch('s0')
        g9_switch = self.addSwitch('g9')
        g10_switch = self.addSwitch('g10')
        
        g9_l1_switch = self.addSwitch('g9l1')
        g9_l2_main = self.addSwitch('g9l2')
        g9_l2_s1 = self.addSwitch('g9s1')
        g9_l2_s2 = self.addSwitch('g9s2')
        g9_l2_s3 = self.addSwitch('g9s3')
        g9_l2_s4 = self.addSwitch('g9s4')
        
        g9_l3_main = self.addSwitch('g9l3')
        g9_l3_s1 = self.addSwitch('g9l1s')
        g9_l3_s2 = self.addSwitch('g9l2s')
        g9_l3_s3 = self.addSwitch('g9l3s')
        
        g10_l1_switch = self.addSwitch('g10l1')
        g10_l2_switch = self.addSwitch('g10l2')
        g10_l3_switch = self.addSwitch('g10l3')

        # --- HOST DEFINITION (Gunakan /24 agar ARP Broadcast jalan) ---
        # Gedung G9
        h1 = self.addHost('ap9l1', ip='192.168.10.1/24') 
        h2 = self.addHost('rk9l1', ip='192.168.10.2/24') 

        h3 = self.addHost('d9s1', ip='192.168.10.33/24')
        h4 = self.addHost('d9s1b', ip='192.168.10.34/24')

        h5 = self.addHost('ad9s2', ip='192.168.10.43/24')
        h6 = self.addHost('ad9s2b', ip='192.168.10.44/24')

        h7 = self.addHost('p9s3', ip='192.168.10.53/24')
        h8 = self.addHost('p9s3b', ip='192.168.10.54/24')

        h9 = self.addHost('uj9s4', ip='192.168.10.63/24')
        h10 = self.addHost('uj9s4b', ip='192.168.10.64/24')

        h11 = self.addHost('lab1', ip='192.168.10.97/24')
        h12 = self.addHost('lab1b', ip='192.168.10.98/24')

        h13 = self.addHost('lab2', ip='192.168.10.130/24')
        h14 = self.addHost('lab2b', ip='192.168.10.131/24')

        h15 = self.addHost('lab3', ip='192.168.10.160/24')
        h16 = self.addHost('lab3b', ip='192.168.10.161/24')

        h17 = self.addHost('ap9l3', ip='192.168.10.162/24')
        h18 = self.addHost('m9l3a', ip='192.168.10.163/24')
        h19 = self.addHost('m9l3b', ip='192.168.10.164/24')

        # Gedung G10
        h21 = self.addHost('ap10l1', ip='172.16.21.1/24') 
        h22 = self.addHost('rk10l1', ip='172.16.21.2/24') 

        h23 = self.addHost('d10l2', ip='172.16.21.17/24')
        h24 = self.addHost('d10l2b', ip='172.16.21.18/24')

        h25 = self.addHost('d10l3', ip='172.16.21.33/24')
        h26 = self.addHost('d10l3b', ip='172.16.21.34/24')

        h27 = self.addHost('ap10l2', ip='172.16.21.19/24')
        h28 = self.addHost('m10l2a', ip='172.16.21.20/24')

        h29 = self.addHost('apaula', ip='172.16.21.21/24')
        h30 = self.addHost('aulab', ip='172.16.21.22/24')

        h31 = self.addHost('ap10l3', ip='172.16.21.35/24')
        h32 = self.addHost('m10l3a', ip='172.16.21.36/24')

        # -- Links --
        self.addLink(core_switch, g9_switch)
        self.addLink(core_switch, g10_switch)
        self.addLink(g9_switch, g9_l1_switch)
        self.addLink(g9_switch, g9_l2_main)
        self.addLink(g9_switch, g9_l3_main)
        self.addLink(g10_switch, g10_l1_switch)
        self.addLink(g10_switch, g10_l2_switch)
        self.addLink(g10_switch, g10_l3_switch)

        self.addLink(g9_l2_main, g9_l2_s1)
        self.addLink(g9_l2_main, g9_l2_s2)
        self.addLink(g9_l2_main, g9_l2_s3)
        self.addLink(g9_l2_main, g9_l2_s4)

        self.addLink(g9_l3_main, g9_l3_s1)
        self.addLink(g9_l3_main, g9_l3_s2)
        self.addLink(g9_l3_main, g9_l3_s3)

        self.addLink(h1, g9_l1_switch)
        self.addLink(h2, g9_l1_switch)
        self.addLink(h3, g9_l2_s1)
        self.addLink(h4, g9_l2_s1)
        self.addLink(h5, g9_l2_s2)
        self.addLink(h6, g9_l2_s2)
        self.addLink(h7, g9_l2_s3)
        self.addLink(h8, g9_l2_s3)
        self.addLink(h9, g9_l2_s4)
        self.addLink(h10, g9_l2_s4)
        self.addLink(h11, g9_l3_s1)
        self.addLink(h12, g9_l3_s1)
        self.addLink(h13, g9_l3_s2)
        self.addLink(h14, g9_l3_s2)
        self.addLink(h15, g9_l3_s3)
        self.addLink(h16, g9_l3_s3)
        self.addLink(h17, g9_l3_main)
        self.addLink(h18, g9_l3_main)
        self.addLink(h19, g9_l3_main)
        self.addLink(h21, g10_l1_switch)
        self.addLink(h22, g10_l1_switch)
        self.addLink(h23, g10_l2_switch)
        self.addLink(h24, g10_l2_switch)
        self.addLink(h25, g10_l3_switch)
        self.addLink(h26, g10_l3_switch)
        self.addLink(h27, g10_l2_switch)
        self.addLink(h28, g10_l2_switch)
        self.addLink(h29, g10_l2_switch)
        self.addLink(h30, g10_l2_switch)
        self.addLink(h31, g10_l3_switch)
        self.addLink(h32, g10_l3_switch)

topos = { 'dept_topo': ( lambda: DeptTopo() ) }

def run():
    topo = DeptTopo()
    
    # === BAGIAN PENTING: protocols='OpenFlow13' ===
    # Kita menggunakan partial untuk membuat custom Switch class
    # yang default-nya menggunakan OpenFlow 1.3
    ovs_v13 = partial(OVSKernelSwitch, protocols='OpenFlow13')
    
    net = Mininet(topo=topo,
                  controller=RemoteController(name='c0', ip='127.0.0.1'),
                  switch=ovs_v13) # Gunakan switch custom tadi
    
    print("\n*** Memulai Jaringan (OF 1.3)...")
    net.start()
    
    print("*** Masuk ke CLI. Ketik 'exit' untuk keluar.")
    CLI(net)
    
    print("*** Mematikan Jaringan...")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()