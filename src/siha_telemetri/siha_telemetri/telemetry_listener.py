import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import math

class TelemetryListener(Node):
    def __init__(self):
        super().__init__('telemetry_listener')
        self.subscription = self.create_subscription(String, '/sunucu_telemetri', self.listener_callback, 10)
        self.ref_lat = 41.0
        self.ref_lon = 29.0

    def listener_callback(self, msg):
        data = json.loads(msg.data)
        ucaklar = data.get("konum_bilgileri", [])
        self.get_logger().info('--- Yeni Veri Paketi Geldi ---')
        for npc in ucaklar[:3]:
            lat = npc["IHA_enlem"]
            lon = npc["IHA_boylam"]
            alt = npc["IHA_irtifa"]
            x = (lon - self.ref_lon) * 111320.0 * math.cos(math.radians(self.ref_lat))
            y = (lat - self.ref_lat) * 111320.0
            z = alt
            self.get_logger().info(f'Takim {npc["takim_numarasi"]} -> X: {x:.2f}m, Y: {y:.2f}m, Z: {z:.2f}m')

def main(args=None):
    rclpy.init(args=args)
    node = TelemetryListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()