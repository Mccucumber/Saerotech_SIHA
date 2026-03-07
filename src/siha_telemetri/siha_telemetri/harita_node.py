import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class HaritaNode(Node):
    def __init__(self):
        super().__init__('harita_node')
        self.subscription = self.create_subscription(
            String,
            '/sunucu_telemetri',
            self.listener_callback,
            10)
        self.get_logger().info("Dinamik Harita Düğümü Aktif: Veriler telemetri.json'a aktarılıyor...")

    def listener_callback(self, msg):
        # Gelen telemetri verisini doğrudan dosyaya yazıyoruz
        with open('telemetri.json', 'w') as f:
            f.write(msg.data)

def main(args=None):
    rclpy.init(args=args)
    node = HaritaNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()