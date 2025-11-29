from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MedicalSimpleTopo(Topo):
    def build(self):
        # CORE & DISTRIBUTION
        s1 = self.addSwitch('s1', dpid='0000000000000001')
        s2 = self.addSwitch('s2', dpid='0000000000000002')
        s3 = self.addSwitch('s3', dpid='0000000000000003')
        
        self.addLink(s1, s2)
        self.addLink(s1, s3)

        # ================= GEDUNG G9 =================
        
        # --- G9 LANTAI 1 (Wireless: 192.168.1.0/22, Kabel: 192.168.10.0/27) ---
        s4 = self.addSwitch('s4')
        self.addLink(s2, s4)
        
        # Wireless G9 LT1
        s4a = self.addSwitch('s4a')
        self.addLink(s4, s4a)
        h1 = self.addHost('h1', ip='192.168.1.1/22')
        h2 = self.addHost('h2', ip='192.168.1.2/22')
        h3 = self.addHost('h3', ip='192.168.2.1/22')
        self.addLink(s4a, h1)
        self.addLink(s4a, h2)
        self.addLink(s4a, h3)
        
        # Kabel G9 LT1
        s4b = self.addSwitch('s4b')
        self.addLink(s4, s4b)
        h4 = self.addHost('h4', ip='192.168.10.1/27')
        h5 = self.addHost('h5', ip='192.168.10.2/27')
        self.addLink(s4b, h4)
        self.addLink(s4b, h5)

        # --- G9 LANTAI 2 (Wireless: 192.168.5.0/24, Kabel: 192.168.10.32/26) ---
        s5 = self.addSwitch('s5')
        self.addLink(s2, s5)
        
        # Wireless G9 LT2 - Admin/Secure
        s5a = self.addSwitch('s5a')
        self.addLink(s5, s5a)
        h6 = self.addHost('h6', ip='192.168.5.1/24')
        h7 = self.addHost('h7', ip='192.168.5.2/24')
        h8 = self.addHost('h8', ip='192.168.5.3/24')
        self.addLink(s5a, h6)
        self.addLink(s5a, h7)
        self.addLink(s5a, h8)
        
        # Kabel G9 LT2 - Keuangan, Admin, Pimpinan, Ujian
        s5b = self.addSwitch('s5b')
        self.addLink(s5, s5b)
        h9 = self.addHost('h9', ip='192.168.10.33/26')
        h10 = self.addHost('h10', ip='192.168.10.34/26')
        h11 = self.addHost('h11', ip='192.168.10.35/26')
        h12 = self.addHost('h12', ip='192.168.10.36/26')
        h13 = self.addHost('h13', ip='192.168.10.37/26')
        h14 = self.addHost('h14', ip='192.168.10.38/26')
        self.addLink(s5b, h9)
        self.addLink(s5b, h10)
        self.addLink(s5b, h11)
        self.addLink(s5b, h12)
        self.addLink(s5b, h13)
        self.addLink(s5b, h14)

        # --- G9 LANTAI 3 (Wireless: 192.168.6.0/22, Kabel: 192.168.10.96/25) ---
        s6 = self.addSwitch('s6')
        self.addLink(s2, s6)
        
        # Wireless G9 LT3 - Lab & Mahasiswa
        s6a = self.addSwitch('s6a')
        self.addLink(s6, s6a)
        h15 = self.addHost('h15', ip='192.168.6.1/22')
        h16 = self.addHost('h16', ip='192.168.6.2/22')
        h17 = self.addHost('h17', ip='192.168.6.3/22')
        h18 = self.addHost('h18', ip='192.168.7.1/22')
        self.addLink(s6a, h15)
        self.addLink(s6a, h16)
        self.addLink(s6a, h17)
        self.addLink(s6a, h18)
        
        # Kabel G9 LT3 - Lab
        s6b = self.addSwitch('s6b')
        self.addLink(s6, s6b)
        h19 = self.addHost('h19', ip='192.168.10.97/25')
        h20 = self.addHost('h20', ip='192.168.10.98/25')
        h21 = self.addHost('h21', ip='192.168.10.99/25')
        h22 = self.addHost('h22', ip='192.168.10.100/25')
        self.addLink(s6b, h19)
        self.addLink(s6b, h20)
        self.addLink(s6b, h21)
        self.addLink(s6b, h22)

        # ================= GEDUNG G10 =================
        
        # --- G10 LANTAI 1 (Wireless: 172.16.20.0/26, Kabel: 172.16.21.0/28) ---
        s7 = self.addSwitch('s7')
        self.addLink(s3, s7)
        
        # Wireless G10 LT1 - Admin
        s7a = self.addSwitch('s7a')
        self.addLink(s7, s7a)
        h23 = self.addHost('h23', ip='172.16.20.1/26')
        h24 = self.addHost('h24', ip='172.16.20.2/26')
        self.addLink(s7a, h23)
        self.addLink(s7a, h24)
        
        # Kabel G10 LT1 - Admin
        s7b = self.addSwitch('s7b')
        self.addLink(s7, s7b)
        h25 = self.addHost('h25', ip='172.16.21.1/28')
        h26 = self.addHost('h26', ip='172.16.21.2/28')
        self.addLink(s7b, h25)
        self.addLink(s7b, h26)

        # --- G10 LANTAI 2 (Wireless: 172.16.20.64/25, Kabel: 172.16.21.16/29) ---
        s8 = self.addSwitch('s8')
        self.addLink(s3, s8)
        
        # Wireless G10 LT2 - Dosen & Aula
        s8a = self.addSwitch('s8a')
        self.addLink(s8, s8a)
        h27 = self.addHost('h27', ip='172.16.20.65/25')
        h28 = self.addHost('h28', ip='172.16.20.66/25')
        h29 = self.addHost('h29', ip='172.16.20.67/25')
        h30 = self.addHost('h30', ip='172.16.20.68/25')
        self.addLink(s8a, h27)
        self.addLink(s8a, h28)
        self.addLink(s8a, h29)
        self.addLink(s8a, h30)
        
        # Kabel G10 LT2 - Dosen
        s8b = self.addSwitch('s8b')
        self.addLink(s8, s8b)
        h31 = self.addHost('h31', ip='172.16.21.17/29')
        h32 = self.addHost('h32', ip='172.16.21.18/29')
        self.addLink(s8b, h31)
        self.addLink(s8b, h32)

        # --- G10 LANTAI 3 (Wireless: 172.16.20.192/26, Kabel: 172.16.21.32/26) ---
        s9 = self.addSwitch('s9')
        self.addLink(s3, s9)
        
        # Wireless G10 LT3 - Dosen
        s9a = self.addSwitch('s9a')
        self.addLink(s9, s9a)
        h33 = self.addHost('h33', ip='172.16.20.193/26')
        h34 = self.addHost('h34', ip='172.16.20.194/26')
        self.addLink(s9a, h33)
        self.addLink(s9a, h34)
        
        # Kabel G10 LT3 - Dosen
        s9b = self.addSwitch('s9b')
        self.addLink(s9, s9b)
        h35 = self.addHost('h35', ip='172.16.21.33/26')
        h36 = self.addHost('h36', ip='172.16.21.34/26')
        self.addLink(s9b, h35)
        self.addLink(s9b, h36)

def run():
    topo = MedicalSimpleTopo()
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()