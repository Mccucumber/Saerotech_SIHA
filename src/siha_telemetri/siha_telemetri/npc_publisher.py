import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import random
import math
import time

class NpcUavPublisher(Node):
    def __init__(self):
        super().__init__('npc_uav_publisher')
        # Veriyi /sunucu_telemetri kanalından yayınlıyoruz
        self.publisher_ = self.create_publisher(String, '/sunucu_telemetri', 10)
        # Saniyede 1 kez veri üret (1 Hz)
        self.timer = self.create_timer(1.0, self.timer_callback) 
        
        # Referans koordinat (41.0, 29.0) - Haritadaki başlangıç bölgesi
        self.ref_lat = 41.0
        self.ref_lon = 29.0
        self.npc_list = []

        # 15 farklı İHA oluşturuyoruz
        for i in range(1, 16):
            npc = {
                "takim_numarasi": i,
                "IHA_enlem": self.ref_lat + random.uniform(-0.01, 0.01),
                "IHA_boylam": self.ref_lon + random.uniform(-0.01, 0.01),
                "IHA_irtifa": random.uniform(80.0, 250.0),
                "heading": random.uniform(0, 360),     # Başlangıç yönü
                # HAREKETİN GÖRÜNMESİ İÇİN HIZ ARTIRILDI (80-120 m/s ~ 300-400 km/h test için ideal)
                "speed": random.uniform(80.0, 120.0)    
            }
            self.npc_list.append(npc)

        self.get_logger().info('Düzeltilmiş NPC Uçuş Fiziği Aktif. İHAlar hızlandırıldı!')

    def timer_callback(self):
        telemetry_data = []
        for npc in self.npc_list:
            # 1. MANEVRA: Yönü daha belirgin değiştir (Daha keskin dönüşler için +-20 derece)
            npc["heading"] += random.uniform(-20.0, 20.0)
            npc["heading"] %= 360 

            # 2. KİNEMATİK: Hız ve Yönü kullanarak katedilen mesafeyi hesapla
            heading_rad = math.radians(npc["heading"])
            dx_meters = npc["speed"] * math.sin(heading_rad) # Doğu-Batı
            dy_meters = npc["speed"] * math.cos(heading_rad) # Kuzey-Güney

            # 3. KOORDİNAT DÖNÜŞÜMÜ: Metreyi dünya derecesine çevir
            d_lat = dy_meters / 111320.0
            d_lon = dx_meters / (111320.0 * math.cos(math.radians(self.ref_lat)))

            # 4. YENİ KONUMU UYGULA
            npc["IHA_enlem"] += d_lat
            npc["IHA_boylam"] += d_lon
            
            # JSON formatına uygun veri paketi oluştur
            uav_data = {
                "takim_numarasi": npc["takim_numarasi"],
                "IHA_enlem": round(npc["IHA_enlem"], 6),
                "IHA_boylam": round(npc["IHA_boylam"], 6),
                "IHA_irtifa": round(npc["IHA_irtifa"], 2),
                "IHA_dikilme": 0,
                "IHA_yonelme": int(npc["heading"]),
                "IHA_yatis": 0,
                "zaman_farki": int(time.time() * 1000)
            }
            telemetry_data.append(uav_data)

        # Mesajı hazırla ve yayınla
        msg = String()
        msg.data = json.dumps({"sistem_saati": int(time.time()), "konum_bilgileri": telemetry_data})
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(NpcUavPublisher())
    rclpy.shutdown()

if __name__ == '__main__':
    main()