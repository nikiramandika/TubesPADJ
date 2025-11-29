from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MedicalSimpleTopo(Topo):
    def build(self):
        # CORE & DISTRIBUTION
        s_core = self.addSwitch('s1', dpid='0000000000000001')
        s_dist_g9 = self.addSwitch('s2', dpid='0000000000000002')
        s_dist_g10 = self.addSwitch('s3', dpid='0000000000000003')
        
        self.addLink(s_core, s_dist_g9)
        self.addLink(s_core, s_dist_g10)

        # ================= GEDUNG G9 =================
        
        # --- G9 LANTAI 1 (Wireless: 192.168.1.0/22, Kabel: 192.168.10.0/27) ---
        sg9lt1m = self.addSwitch('s4')
        self.addLink(s_dist_g9, sg9lt1m)
        
        # Wireless G9 LT1
        sg9lt1w = self.addSwitch('s4a')
        self.addLink(sg9lt1m, sg9lt1w)
        hmhsg9lt11 = self.addHost('mhsg9lt11', ip='192.168.1.1/22')
        hmhsg9lt12 = self.addHost('mhsg9lt12', ip='192.168.1.2/22')
        hmhsg9lt13 = self.addHost('mhsg9lt13', ip='192.168.2.1/22')
        self.addLink(sg9lt1w, hmhsg9lt11)
        self.addLink(sg9lt1w, hmhsg9lt12)
        self.addLink(sg9lt1w, hmhsg9lt13)
        
        # Kabel G9 LT1
        sg9lt1k = self.addSwitch('s4b')
        self.addLink(sg9lt1m, sg9lt1k)
        hmhsg9lt1k1 = self.addHost('mhsg9lt1k1', ip='192.168.10.1/27')
        hmhsg9lt1k2 = self.addHost('mhsg9lt1k2', ip='192.168.10.2/27')
        self.addLink(sg9lt1k, hmhsg9lt1k1)
        self.addLink(sg9lt1k, hmhsg9lt1k2)

        # --- G9 LANTAI 2 (Wireless: 192.168.5.0/24, Kabel: 192.168.10.32/26) ---
        sg9lt2m = self.addSwitch('s5')
        self.addLink(s_dist_g9, sg9lt2m)
        
        # Wireless G9 LT2 - Admin/Secure
        sg9lt2w = self.addSwitch('s5a')
        self.addLink(sg9lt2m, sg9lt2w)
        hadmg9lt2w1 = self.addHost('admg9lt2w1', ip='192.168.5.1/24')
        hadmg9lt2w2 = self.addHost('admg9lt2w2', ip='192.168.5.2/24')
        hadmg9lt2w3 = self.addHost('admg9lt2w3', ip='192.168.5.3/24')
        self.addLink(sg9lt2w, hadmg9lt2w1)
        self.addLink(sg9lt2w, hadmg9lt2w2)
        self.addLink(sg9lt2w, hadmg9lt2w3)
        
        # Kabel G9 LT2 - Keuangan, Admin, Pimpinan, Ujian
        sg9lt2k = self.addSwitch('s5b')
        self.addLink(sg9lt2m, sg9lt2k)
        hkeug91 = self.addHost('keug91', ip='192.168.10.33/26')
        hkeug92 = self.addHost('keug92', ip='192.168.10.34/26')
        hdekan = self.addHost('dekan', ip='192.168.10.35/26')
        hsekre = self.addHost('sekre', ip='192.168.10.36/26')
        hujiag91 = self.addHost('ujiag91', ip='192.168.10.37/26')
        hujiag92 = self.addHost('ujiag92', ip='192.168.10.38/26')
        self.addLink(sg9lt2k, hkeug91)
        self.addLink(sg9lt2k, hkeug92)
        self.addLink(sg9lt2k, hdekan)
        self.addLink(sg9lt2k, hsekre)
        self.addLink(sg9lt2k, hujiag91)
        self.addLink(sg9lt2k, hujiag92)

        # --- G9 LANTAI 3 (Wireless: 192.168.6.0/22, Kabel: 192.168.10.96/25) ---
        sg9lt3m = self.addSwitch('s6')
        self.addLink(s_dist_g9, sg9lt3m)
        
        # Wireless G9 LT3 - Lab & Mahasiswa
        sg9lt3w = self.addSwitch('s6a')
        self.addLink(sg9lt3m, sg9lt3w)
        hlabg9lt3w1 = self.addHost('labg9lt3w1', ip='192.168.6.1/22')
        hlabg9lt3w2 = self.addHost('labg9lt3w2', ip='192.168.6.2/22')
        hlabg9lt3w3 = self.addHost('labg9lt3w3', ip='192.168.6.3/22')
        hlabg9lt3w4 = self.addHost('labg9lt3w4', ip='192.168.7.1/22')
        self.addLink(sg9lt3w, hlabg9lt3w1)
        self.addLink(sg9lt3w, hlabg9lt3w2)
        self.addLink(sg9lt3w, hlabg9lt3w3)
        self.addLink(sg9lt3w, hlabg9lt3w4)
        
        # Kabel G9 LT3 - Lab
        sg9lt3k = self.addSwitch('s6b')
        self.addLink(sg9lt3m, sg9lt3k)
        hlabg9lt3k1 = self.addHost('labg9lt3k1', ip='192.168.10.97/25')
        hlabg9lt3k2 = self.addHost('labg9lt3k2', ip='192.168.10.98/25')
        hlabg9lt3k3 = self.addHost('labg9lt3k3', ip='192.168.10.99/25')
        hlabg9lt3k4 = self.addHost('labg9lt3k4', ip='192.168.10.100/25')
        self.addLink(sg9lt3k, hlabg9lt3k1)
        self.addLink(sg9lt3k, hlabg9lt3k2)
        self.addLink(sg9lt3k, hlabg9lt3k3)
        self.addLink(sg9lt3k, hlabg9lt3k4)

        # ================= GEDUNG G10 =================
        
        # --- G10 LANTAI 1 (Wireless: 172.16.20.0/26, Kabel: 172.16.21.0/28) ---
        sg10lt1m = self.addSwitch('s7')
        self.addLink(s_dist_g10, sg10lt1m)
        
        # Wireless G10 LT1 - Admin
        sg10lt1w = self.addSwitch('s7a')
        self.addLink(sg10lt1m, sg10lt1w)
        hadmg10lt1w1 = self.addHost('admg10lt1w1', ip='172.16.20.1/26')
        hadmg10lt1w2 = self.addHost('admg10lt1w2', ip='172.16.20.2/26')
        self.addLink(sg10lt1w, hadmg10lt1w1)
        self.addLink(sg10lt1w, hadmg10lt1w2)
        
        # Kabel G10 LT1 - Admin
        sg10lt1k = self.addSwitch('s7b')
        self.addLink(sg10lt1m, sg10lt1k)
        hadmg10lt1k1 = self.addHost('admg10lt1k1', ip='172.16.21.1/28')
        hadmg10lt1k2 = self.addHost('admg10lt1k2', ip='172.16.21.2/28')
        self.addLink(sg10lt1k, hadmg10lt1k1)
        self.addLink(sg10lt1k, hadmg10lt1k2)

        # --- G10 LANTAI 2 (Wireless: 172.16.20.64/25, Kabel: 172.16.21.16/29) ---
        sg10lt2m = self.addSwitch('s8')
        self.addLink(s_dist_g10, sg10lt2m)
        
        # Wireless G10 LT2 - Dosen & Aula
        sg10lt2w = self.addSwitch('s8a')
        self.addLink(sg10lt2m, sg10lt2w)
        hdsng10lt2w1 = self.addHost('dsng10lt2w1', ip='172.16.20.65/25')
        hdsng10lt2w2 = self.addHost('dsng10lt2w2', ip='172.16.20.66/25')
        haulaw1 = self.addHost('aulaw1', ip='172.16.20.67/25')
        haulaw2 = self.addHost('aulaw2', ip='172.16.20.68/25')
        self.addLink(sg10lt2w, hdsng10lt2w1)
        self.addLink(sg10lt2w, hdsng10lt2w2)
        self.addLink(sg10lt2w, haulaw1)
        self.addLink(sg10lt2w, haulaw2)
        
        # Kabel G10 LT2 - Dosen
        sg10lt2k = self.addSwitch('s8b')
        self.addLink(sg10lt2m, sg10lt2k)
        hdsng10lt2k1 = self.addHost('dsng10lt2k1', ip='172.16.21.17/29')
        hdsng10lt2k2 = self.addHost('dsng10lt2k2', ip='172.16.21.18/29')
        self.addLink(sg10lt2k, hdsng10lt2k1)
        self.addLink(sg10lt2k, hdsng10lt2k2)

        # --- G10 LANTAI 3 (Wireless: 172.16.20.192/26, Kabel: 172.16.21.32/26) ---
        sg10lt3m = self.addSwitch('s9')
        self.addLink(s_dist_g10, sg10lt3m)
        
        # Wireless G10 LT3 - Dosen
        sg10lt3w = self.addSwitch('s9a')
        self.addLink(sg10lt3m, sg10lt3w)
        hdsng10lt3w1 = self.addHost('dsng10lt3w1', ip='172.16.20.193/26')
        hdsng10lt3w2 = self.addHost('dsng10lt3w2', ip='172.16.20.194/26')
        self.addLink(sg10lt3w, hdsng10lt3w1)
        self.addLink(sg10lt3w, hdsng10lt3w2)
        
        # Kabel G10 LT3 - Dosen
        sg10lt3k = self.addSwitch('s9b')
        self.addLink(sg10lt3m, sg10lt3k)
        hdsng10lt3k1 = self.addHost('dsng10lt3k1', ip='172.16.21.33/26')
        hdsng10lt3k2 = self.addHost('dsng10lt3k2', ip='172.16.21.34/26')
        self.addLink(sg10lt3k, hdsng10lt3k1)
        self.addLink(sg10lt3k, hdsng10lt3k2)

def run():
    topo = MedicalSimpleTopo()
    net = Mininet(topo=topo, controller=RemoteController, autoSetMacs=True)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()