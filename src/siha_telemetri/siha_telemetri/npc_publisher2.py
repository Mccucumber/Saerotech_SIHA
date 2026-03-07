import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import random
import math
import time
from datetime import datetime

class NpcUavPublisher(Node):
    def __init__(self):
        super().__init__('npc_uav_publisher')
        self.publisher_ = self.create_publisher(String, '/sunucu_telemetri', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)

        # Haberlesme dokumanindaki ornek koordinatlara (Samsun civari) yaklastirildi
        self.ref_lat = 41.51
        self.ref_lon = 36.11
        self.npc_list = []

        for i in range(1, 16):
            npc = {
                "takim_numarasi": i,
                "iha_enlem": self.ref_lat + random.uniform(-0.01, 0.01),
                "iha_boylam": self.ref_lon + random.uniform(-0.01, 0.01),
                "iha_irtifa": random.uniform(30.0, 100.0),
                "iha_yonelme": random.uniform(0, 360),
                "iha_hizi": random.uniform(30.0, 45.0),
                "hedef_irtifa": random.uniform(30.0, 100.0) # Tırmanış/Dalış simülasyonu için
            }
            self.npc_list.append(npc)

        self.get_logger().info('Sartnameye %100 Uyumlu Telemetri ve Ucus Fizigi Aktif!')

    def timer_callback(self):
        konum_bilgileri = []
        
        # Sartnamedeki saat formati
        now = datetime.now()
        sunucusaati = {
            "gun": now.day,
            "saat": now.hour,
            "dakika": now.minute,
            "saniye": now.second,
            "milisaniye": int(now.microsecond / 1000)
        }

        for npc in self.npc_list:
            # 1. YONELME VE YATIS (Heading & Roll)
            turn_rate = random.uniform(-15.0, 15.0)
            npc["iha_yonelme"] = (npc["iha_yonelme"] + turn_rate) % 360
            # Ucak ne kadar hizli donuyorsa o kadar yatar (Fiziksel baglanti)
            iha_yatis = turn_rate * 2.5 
            iha_yatis = max(-60.0, min(60.0, iha_yatis))

            # 2. DIKILME VE IRTIFA (Pitch & Altitude)
            if abs(npc["iha_irtifa"] - npc["hedef_irtifa"]) < 5.0:
                npc["hedef_irtifa"] = random.uniform(30.0, 100.0)
            
            alt_diff = npc["hedef_irtifa"] - npc["iha_irtifa"]
            climb_rate = max(-4.0, min(4.0, alt_diff * 0.4)) 
            npc["iha_irtifa"] += climb_rate
            # Tirmanirken burun yukari, dalarken burun asagi
            iha_dikilme = climb_rate * 3.5

            # 3. KINEMATIK HAREKET
            heading_rad = math.radians(npc["iha_yonelme"])
            dx_meters = npc["iha_hizi"] * math.sin(heading_rad)
            dy_meters = npc["iha_hizi"] * math.cos(heading_rad)

            d_lat = dy_meters / 111320.0
            d_lon = dx_meters / (111320.0 * math.cos(math.radians(self.ref_lat)))

            npc["iha_enlem"] += d_lat
            npc["iha_boylam"] += d_lon
            
            # Sartname Bolum 7.3 Formatina Birebir Uygun JSON Ciktisi
            uav_data = {
                "takim_numarasi": npc["takim_numarasi"],
                "iha_enlem": round(npc["iha_enlem"], 7),
                "iha_boylam": round(npc["iha_boylam"], 7),
                "iha_irtifa": round(npc["iha_irtifa"], 1),
                "iha_dikilme": round(iha_dikilme, 1),
                "iha_yonelme": int(npc["iha_yonelme"]),
                "iha_yatis": round(iha_yatis, 1),
                "iha_hizi": round(npc["iha_hizi"], 1),
                "zaman_farki": random.randint(20, 300) 
            }
            konum_bilgileri.append(uav_data)

        # Mesaji yayinla
        msg = String()
        msg.data = json.dumps({"sunucusaati": sunucusaati, "konumBilgileri": konum_bilgileri})
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(NpcUavPublisher())
    rclpy.shutdown()

if __name__ == '__main__':
    main()