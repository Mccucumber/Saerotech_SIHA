import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import random
import math
import time
from datetime import datetime
import os

class NpcUavPublisher(Node):
    def __init__(self):
        super().__init__('npc_uav_publisher')
        self.publisher_ = self.create_publisher(String, '/sunucu_telemetri', 10)
        self.physics_timer = self.create_timer(0.1, self.physics_callback) # 10 Hz Physics Loop
        self.publish_timer = self.create_timer(1.0, self.publish_callback) # 1 Hz Publish Loop

        # Haberlesme dokumanindaki ornek koordinatlara (Samsun civari) yaklastirildi
        self.ref_lat = 41.51
        self.ref_lon = 36.11
        self.center_lat = self.ref_lat
        self.center_lon = self.ref_lon
        self.npc_list = []
        
        self.boundary = None
        self.boundary_mtime = 0
        self.load_boundary()
        
        self.hss_list = []
        self.hss_mtime = 0
        self.load_hss()

        self.get_logger().info('Hazir! Arayuzden sinir cizilmesi bekleniyor...')

    def load_boundary(self):
        filepath = 'boundary.json'
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            if mtime > self.boundary_mtime:
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if "boundary" in data:
                            self.boundary = data["boundary"]
                            self.boundary_mtime = mtime
                            
                            # Sınırın (polygonun) merkezini hesapla ki uçaklar merkeze yönelsin
                            lats = [p[0] for p in self.boundary]
                            lons = [p[1] for p in self.boundary]
                            self.center_lat = sum(lats) / len(lats)
                            self.center_lon = sum(lons) / len(lons)
                            
                            self.get_logger().info('Yeni sinir verisi yuklendi, merkez hesaplandi.')
                            
                            
                            # Eğer İHA'lar henüz oluşturulmadıysa (ilk sınır çizimi) şimdi oluştur
                            if len(self.npc_list) == 0 and len(self.boundary) >= 3:
                                self.spawn_uavs()
                            else:
                                # Mevcut İHA'lar dışarıdaysa içeri taşı
                                for npc in self.npc_list:
                                    if not self.is_in_boundary(npc["iha_enlem"], npc["iha_boylam"]):
                                        lat, lon = self.get_random_pos_in_boundary()
                                        npc["iha_enlem"] = lat
                                        npc["iha_boylam"] = lon
                except Exception as e:
                    self.get_logger().error(f'Sinir yukleme hatasi: {e}')

    def spawn_uavs(self):
        for i in range(1, 16):
            start_lat, start_lon = self.get_random_pos_in_boundary()
            npc = {
                "takim_numarasi": i,
                "iha_enlem": start_lat,
                "iha_boylam": start_lon,
                "iha_irtifa": random.uniform(30.0, 100.0),
                "iha_yonelme": random.uniform(0, 360),
                "iha_hiz": random.uniform(30.0, 45.0),
                "hedef_irtifa": random.uniform(30.0, 100.0),
                "iha_batarya": random.randint(30, 100),
                "iha_otonom": 1,
                "iha_kilitlenme": random.choice([0, 1]),
                "hedef_merkez_X": random.randint(0, 640),
                "hedef_merkez_Y": random.randint(0, 480),
                "hedef_genislik": random.randint(20, 50),
                "hedef_yukseklik": random.randint(20, 50)
            }
            self.npc_list.append(npc)
        self.get_logger().info('15 adet IHA sinir icerisinde basariyla spawn edildi!')

    def load_hss(self):
        filepath = 'hss.json'
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            if mtime > self.hss_mtime:
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        self.hss_list = data
                        self.hss_mtime = mtime
                        self.get_logger().info(f'Yeni HSS (No-Fly Zone) verisi yuklendi. Toplam HSS: {len(self.hss_list)}')
                except Exception as e:
                    self.get_logger().error(f'HSS yukleme hatasi: {e}')

    def is_in_boundary(self, lat, lon):
        if not self.boundary or len(self.boundary) < 3:
            return True # Sınır yoksa uçuş serbest
        
        inside = False
        j = len(self.boundary) - 1
        for i in range(len(self.boundary)):
            lat_i, lon_i = self.boundary[i]
            lat_j, lon_j = self.boundary[j]
            
            intersect = ((lon_i > lon) != (lon_j > lon)) and (lat < (lat_j - lat_i) * (lon - lon_i) / (lon_j - lon_i + 1e-9) + lat_i)
            if intersect:
                inside = not inside
            j = i
            
        return inside

    def get_random_pos_in_boundary(self):
        if not self.boundary or len(self.boundary) < 3:
            return self.ref_lat + random.uniform(-0.01, 0.01), self.ref_lon + random.uniform(-0.01, 0.01)
        
        min_lat = min(p[0] for p in self.boundary)
        max_lat = max(p[0] for p in self.boundary)
        min_lon = min(p[1] for p in self.boundary)
        max_lon = max(p[1] for p in self.boundary)
        
        for _ in range(100):
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            if self.is_in_boundary(lat, lon):
                return lat, lon
        return self.ref_lat, self.ref_lon

    def physics_callback(self):
        dt = 0.1
        # Dinamik olarak sınır güncellemelerini çek
        self.load_boundary()
        self.load_hss()
        
        # Sınır yoksa veya UAV yoksa fizigi calistirma
        if not self.boundary or len(self.npc_list) == 0:
            return

        for npc in self.npc_list:
            # ---------------------------------------------------------
            # SINIR VE HSS (ENGEL) KAÇINMA KONTROLÜ
            
            heading_rad_la = math.radians(npc["iha_yonelme"])
            hss_collision = None
            
            # 1, 2, 3 ve 4 saniye sonraki konumlarını kontrol et (Çoklu nokta testi)
            for lookahead_sec in [1.0, 2.0, 3.0, 4.0]:
                dx_meters_la = npc["iha_hiz"] * math.sin(heading_rad_la) * lookahead_sec
                dy_meters_la = npc["iha_hiz"] * math.cos(heading_rad_la) * lookahead_sec
                
                d_lat_la = dy_meters_la / 111320.0
                d_lon_la = dx_meters_la / (111320.0 * math.cos(math.radians(self.ref_lat)))
                
                f_lat = npc["iha_enlem"] + d_lat_la
                f_lon = npc["iha_boylam"] + d_lon_la
                
                for hss in self.hss_list:
                    dist_meters = math.sqrt(
                        ((f_lat - hss["hssEnlem"]) * 111320.0) ** 2 + 
                        ((f_lon - hss["hssBoylam"]) * (111320.0 * math.cos(math.radians(self.ref_lat)))) ** 2
                    )
                    # 50m güvenlik payı ile çarpışma testi
                    if dist_meters < (hss["hssYaricap"] + 50.0):
                        hss_collision = hss
                        break
                if hss_collision:
                    break
            
            # Sınır kontrolü için sadece 3 saniyelik ileriyi baz alalım
            future_lat = npc["iha_enlem"] + (npc["iha_hiz"] * math.cos(heading_rad_la) * 3.0) / 111320.0
            future_lon = npc["iha_boylam"] + (npc["iha_hiz"] * math.sin(heading_rad_la) * 3.0) / (111320.0 * math.cos(math.radians(self.ref_lat)))
            
            if hss_collision:
                # Uçak bir HSS dairesine giriyor (veya girecek)! Merkezin TERSİNE dön (Daha sert kavis)
                dy = (hss_collision["hssEnlem"] - npc["iha_enlem"]) * 111320.0
                dx = (hss_collision["hssBoylam"] - npc["iha_boylam"]) * (111320.0 * math.cos(math.radians(self.ref_lat)))
                
                angle_to_hss = math.degrees(math.atan2(dx, dy)) % 360
                angle_diff = (angle_to_hss - npc["iha_yonelme"] + 180) % 360 - 180
                
                # Hedef HSS ise tehlikelidir, tam tersine oldukça sert dön (Saniyede 35 derece)
                target_turn_rate = -35.0 if angle_diff > 0 else 35.0

            elif not self.is_in_boundary(future_lat, future_lon):
                # Uçak dış sınıra yaklaşıyor!
                # Oyun alanının merkezine doğru dön
                dy = (self.center_lat - npc["iha_enlem"]) * 111320.0
                dx = (self.center_lon - npc["iha_boylam"]) * (111320.0 * math.cos(math.radians(self.ref_lat)))
                target_angle = math.degrees(math.atan2(dx, dy)) % 360
                
                angle_diff = (target_angle - npc["iha_yonelme"] + 180) % 360 - 180
                target_turn_rate = 18.0 if angle_diff > 0 else -18.0
            else:
                # Serbest doğa uçuşu (Hafif salınımlı rastgele rota)
                if "turn_bias" not in npc:
                    npc["turn_bias"] = random.uniform(-10.0, 10.0)
                npc["turn_bias"] += random.uniform(-1.0, 1.0)
                npc["turn_bias"] = max(-15.0, min(15.0, npc["turn_bias"]))
                target_turn_rate = npc["turn_bias"]

            # Her tickte donus hizini uygula
            turn_step = target_turn_rate * dt

            # 1. YONELME VE YATIS (Heading & Roll)
            npc["iha_yonelme"] = (npc["iha_yonelme"] + turn_step) % 360
            # Ucak ne kadar hizli donuyorsa o kadar yatar (Fiziksel baglanti)
            iha_yatis = target_turn_rate * 2.5 
            npc["iha_yatis"] = max(-60.0, min(60.0, iha_yatis))

            # 2. DIKILME VE IRTIFA (Pitch & Altitude)
            if abs(npc["iha_irtifa"] - npc["hedef_irtifa"]) < 5.0:
                npc["hedef_irtifa"] = random.uniform(30.0, 100.0)
            
            alt_diff = npc["hedef_irtifa"] - npc["iha_irtifa"]
            target_climb_rate = max(-4.0, min(4.0, alt_diff * 0.4)) 
            npc["iha_irtifa"] += target_climb_rate * dt
            # Tirmanirken burun yukari, dalarken burun asagi
            npc["iha_dikilme"] = target_climb_rate * 3.5

            # 3. KINEMATIK HAREKET
            heading_rad = math.radians(npc["iha_yonelme"])
            dx_meters = npc["iha_hiz"] * math.sin(heading_rad) * dt
            dy_meters = npc["iha_hiz"] * math.cos(heading_rad) * dt

            d_lat = dy_meters / 111320.0
            d_lon = dx_meters / (111320.0 * math.cos(math.radians(self.ref_lat)))

            npc["iha_enlem"] += d_lat
            npc["iha_boylam"] += d_lon

    def publish_callback(self):
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

        # Sınır yoksa veya UAV yoksa henüz veri gönderme
        if not self.boundary or len(self.npc_list) == 0:
            msg = String()
            msg.data = json.dumps({"sunucusaati": sunucusaati, "konumBilgileri": [], "hss_koordinat_bilgileri": self.hss_list})
            self.publisher_.publish(msg)
            return

        for npc in self.npc_list:
            # Kilitlenme varsa hedef verilerini rastgele koru, yoksa sıfırla
            if npc["iha_kilitlenme"] == 0:
                hedef_x = 0
                hedef_y = 0
                hedef_g = 0
                hedef_h = 0
            else:
                hedef_x = npc["hedef_merkez_X"]
                hedef_y = npc["hedef_merkez_Y"]
                hedef_g = npc["hedef_genislik"]
                hedef_h = npc["hedef_yukseklik"]

            gps_now = datetime.now()
            
            # Sartname Bolum 7.3 Formatina Birebir Uygun JSON Ciktisi (Cevap simulasyonu oldugu icin zaman_farki ekleniyor)
            uav_data = {
                "takim_numarasi": npc["takim_numarasi"],
                "iha_enlem": round(npc["iha_enlem"], 7),
                "iha_boylam": round(npc["iha_boylam"], 7),
                "iha_irtifa": round(npc["iha_irtifa"], 1),
                "iha_dikilme": round(npc.get("iha_dikilme", 0.0), 1),
                "iha_yonelme": int(npc["iha_yonelme"]),
                "iha_yatis": round(npc.get("iha_yatis", 0.0), 1),
                "iha_hiz": round(npc["iha_hiz"], 1),
                "iha_batarya": npc["iha_batarya"],
                "iha_otonom": npc["iha_otonom"],
                "iha_kilitlenme": npc["iha_kilitlenme"],
                "hedef_merkez_X": hedef_x,
                "hedef_merkez_Y": hedef_y,
                "hedef_genislik": hedef_g,
                "hedef_yukseklik": hedef_h,
                "gps_saati": {
                    "saat": gps_now.hour,
                    "dakika": gps_now.minute,
                    "saniye": gps_now.second,
                    "milisaniye": int(gps_now.microsecond / 1000)
                },
                "zaman_farki": random.randint(20, 300) 
            }
            konum_bilgileri.append(uav_data)

        # Mesaji yayinla. Serverin gonderecegi cevap formatina (Bolum 7.3) tam uygun)
        msg = String()
        msg.data = json.dumps({"sunucusaati": sunucusaati, "konumBilgileri": konum_bilgileri, "hss_koordinat_bilgileri": self.hss_list})
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(NpcUavPublisher())
    rclpy.shutdown()

if __name__ == '__main__':
    main()