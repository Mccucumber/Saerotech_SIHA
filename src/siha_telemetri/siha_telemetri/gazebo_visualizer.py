import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import math
import subprocess
import time

class GazeboVisualizer(Node):
    def __init__(self):
        super().__init__('visualizer')
        self.subscription = self.create_subscription(String, '/sunucu_telemetri', self.listener_callback, 10)
        
        # Referans koordinatlar (Merkez: 41.0, 29.0)
        self.ref_lat = 41.0
        self.ref_lon = 29.0
        self.spawned_uavs = set()
        
        self.get_logger().info('Radar Modu Baslatildi. Sahada gorus saglaniyor...')
        self.setup_arena()

    def setup_arena(self):
        """Yarisma alanini (5km x 5km) belirleyen devasa bir kare ve merkez kulesi ekler."""
        # 1. MERKEZ KULESI (Beyaz)
        self.spawn_raw("center_pillar", self.get_cylinder_sdf("center_pillar", 3, 1000, "1 1 1 1"), 0, 0, 500)
        
        # 2. ARENA SINIRLARI (5000m x 5000m Kare Çerçeve)
        # Kuzey, Guney, Dogu, Bati hatlari (Devasa kutular olarak)
        self.spawn_raw("border_n", self.get_box_sdf("border_n", 5000, 10, 2, "0.5 0.5 0.5 1"), 0, 2500, 1)
        self.spawn_raw("border_s", self.get_box_sdf("border_s", 5000, 10, 2, "0.5 0.5 0.5 1"), 0, -2500, 1)
        self.spawn_raw("border_e", self.get_box_sdf("border_e", 10, 5000, 2, "0.5 0.5 0.5 1"), 2500, 0, 1)
        self.spawn_raw("border_w", self.get_box_sdf("border_w", 10, 5000, 2, "0.5 0.5 0.5 1"), -2500, 0, 1)

    def get_cylinder_sdf(self, name, r, l, col):
        return f"<sdf version='1.6'><model name='{name}'><static>true</static><link name='l'><visual name='v'><geometry><cylinder><radius>{r}</radius><length>{l}</length></cylinder></geometry><material><ambient>{col}</ambient><diffuse>{col}</diffuse><emissive>{col}</emissive></material></visual></link></model></sdf>"

    def get_box_sdf(self, name, x, y, z, col):
        return f"<sdf version='1.6'><model name='{name}'><static>true</static><link name='l'><visual name='v'><geometry><box><size>{x} {y} {z}</size></box></geometry><material><ambient>{col}</ambient><diffuse>{col}</diffuse></material></visual></link></model></sdf>"

    def listener_callback(self, msg):
        try:
            data = json.loads(msg.data)
            for npc in data.get("konum_bilgileri", []):
                tid = npc["takim_numarasi"]
                # Koordinat Donusumu (Metre)
                x = (npc["IHA_boylam"] - self.ref_lon) * 111320.0 * math.cos(math.radians(self.ref_lat))
                y = (npc["IHA_enlem"] - self.ref_lat) * 111320.0
                z = npc["IHA_irtifa"]

                if tid not in self.spawned_uavs:
                    self.spawn_uav(tid, x, y, z)
                    self.spawned_uavs.add(tid)
                    time.sleep(0.1)
                else:
                    # Pozisyon guncelleme
                    cmd = ['gz', 'topic', '-t', f'/model/uav_{tid}/pose', '-m', 'gz.msgs.Pose', '-p', f'position: {{x: {x}, y: {y}, z: {z}}}']
                    subprocess.Popen(cmd)
        except Exception: pass

    def spawn_raw(self, name, sdf, x, y, z):
        req = f'sdf: "{sdf}", pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}'
        # DİKKAT: '--reptype', 'gz.msgs.Boolean' eklendi!
        subprocess.Popen(['gz', 'service', '-s', '/world/radar_world/create', '--reqtype', 'gz.msgs.EntityFactory', '--reptype', 'gz.msgs.Boolean', '--req', req])

    def spawn_uav(self, id, x, y, z):
        name = f"uav_{id}"
        # TÜM BOŞLUKLAR VE ALT SATIRLAR SİLİNDİ, TEK SATIR YAPILDI
        sdf = f"<sdf version='1.6'><model name='{name}'><static>true</static><link name='l'><visual name='v'><geometry><sphere><radius>25.0</radius></sphere></geometry><material><ambient>0 1 0 1</ambient><diffuse>0 1 0 1</diffuse><emissive>0 1 0 1</emissive></material></visual></link></model></sdf>"
        
        req = f'sdf: "{sdf}", pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}'
        subprocess.Popen(['gz', 'service', '-s', '/world/radar_world/create', '--reqtype', 'gz.msgs.EntityFactory', '--reptype', 'gz.msgs.Boolean', '--req', req])

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(GazeboVisualizer())
    rclpy.shutdown()

if __name__ == '__main__': main()