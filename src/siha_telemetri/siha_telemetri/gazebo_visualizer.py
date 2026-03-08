import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import math
import subprocess
import time
import os

# gz Python bindings for direct transport (avoids subprocess CLI parsing issues)
try:
    import gz.transport13
    from gz.msgs10 import (
        pose_pb2 as gz_pose_pb2,
        boolean_pb2 as gz_bool_pb2,
        entity_factory_pb2 as gz_entity_factory_pb2,
        entity_pb2 as gz_entity_pb2
    )
    GZ_TRANSPORT_AVAILABLE = True
except ImportError:
    GZ_TRANSPORT_AVAILABLE = False

class GazeboVisualizer(Node):
    def __init__(self):
        super().__init__('visualizer')
        self.subscription = self.create_subscription(String, '/sunucu_telemetri', self.listener_callback, 10)
        
        self.ref_lat = None
        self.ref_lon = None
        self.spawned_uavs = set()
        self.arena_setup = False
        
        # gz transport node for direct pose updates
        if GZ_TRANSPORT_AVAILABLE:
            self.gz_node = gz.transport13.Node()
        else:
            self.gz_node = None
            self.get_logger().warn('gz.transport13 bulunamadi.')

        # Clean up any stale entities from previous runs
        self.cleanup_old_entities()
        
        self.get_logger().info('Radar Modu Baslatildi. Sahada gorus saglaniyor...')
        self.update_reference_point()

    def cleanup_old_entities(self):
        """Delete border segments and UAVs leftover from previous visualizer runs using native transport."""
        if not (self.gz_node and GZ_TRANSPORT_AVAILABLE):
            return

        # List of entities to try removing
        entities_to_remove = ["center_pillar"]
        for i in range(16):
            entities_to_remove.append(f"dynamic_border_segment_{i}")
        for i in range(1, 16):
            entities_to_remove.append(f"uav_{i}")

        for name in entities_to_remove:
            req = gz_entity_pb2.Entity()
            req.name = name
            req.type = gz_entity_pb2.Entity.MODEL
            
            # Non-blocking request to remove entity
            # We don't wait for result because it might not exist (common case)
            self.gz_node.request(
                '/world/empty/remove', req,
                gz_entity_pb2.Entity, gz_bool_pb2.Boolean,
                100 # Short timeout for cleanup
            )
        
        time.sleep(1.0)  # Give Gazebo time to process deletions

    def update_reference_point(self):
        filepath = 'boundary.json'
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if "boundary" in data and len(data["boundary"]) >= 3:
                        boundary = data["boundary"]
                        lats = [p[0] for p in boundary]
                        lons = [p[1] for p in boundary]
                        self.ref_lat = min(lats)
                        self.ref_lon = min(lons)
                        self.get_logger().info(f'Referans: {self.ref_lat}, {self.ref_lon}')
                        if not self.arena_setup:
                            self.setup_arena(boundary)
                            self.arena_setup = True
            except Exception as e:
                self.get_logger().error(f'Referans yukleme hatasi: {e}')

    def setup_arena(self, boundary_coords):
        """Spawns dynamic polygon boundary walls and a center marker."""
        # Center pillar (white)
        self.spawn_entity("center_pillar", self.get_cylinder_sdf("center_pillar", 3, 1000, "1 1 1 1"), 0, 0, 500, 0, 0, 0, 1)

        if not boundary_coords or len(boundary_coords) < 3:
            return

        num_points = len(boundary_coords)
        for i in range(num_points):
            p1_lat = boundary_coords[i][0]
            p1_lon = boundary_coords[i][1]
            p2_lat = boundary_coords[(i + 1) % num_points][0]
            p2_lon = boundary_coords[(i + 1) % num_points][1]

            x1 = (p1_lon - self.ref_lon) * 111320.0 * math.cos(math.radians(self.ref_lat))
            y1 = (p1_lat - self.ref_lat) * 111320.0
            x2 = (p2_lon - self.ref_lon) * 111320.0 * math.cos(math.radians(self.ref_lat))
            y2 = (p2_lat - self.ref_lat) * 111320.0

            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            mid_x = (x1 + x2) / 2.0
            mid_y = (y1 + y2) / 2.0

            # Compute yaw angle and convert to quaternion (rotation around Z axis)
            yaw = math.atan2(y2 - y1, x2 - x1)
            qz = math.sin(yaw / 2.0)
            qw = math.cos(yaw / 2.0)

            wall_name = f"dynamic_border_segment_{i}"
            wall_sdf = self.get_box_sdf(wall_name, length, 5.0, 150.0, "1 0 0 1")
            # z=75 = half of 150m height so wall sits on ground level
            self.spawn_entity(wall_name, wall_sdf, mid_x, mid_y, 75, 0.0, 0.0, qz, qw)

    def get_cylinder_sdf(self, name, r, l, col):
        return (f"<sdf version='1.6'><model name='{name}'><static>true</static>"
                f"<link name='l'><visual name='v'><geometry><cylinder>"
                f"<radius>{r}</radius><length>{l}</length></cylinder></geometry>"
                f"<material><ambient>{col}</ambient><diffuse>{col}</diffuse>"
                f"<emissive>{col}</emissive></material></visual></link></model></sdf>")

    def get_box_sdf(self, name, x, y, z, col):
        """Simple static box SDF with NO rotation — rotation is passed in EntityFactory pose."""
        return (f"<sdf version='1.6'><model name='{name}'><static>true</static>"
                f"<link name='l'><visual name='v'><geometry><box>"
                f"<size>{x} {y} {z}</size></box></geometry>"
                f"<material><ambient>{col}</ambient><diffuse>{col}</diffuse>"
                f"<emissive>{col}</emissive></material></visual></link></model></sdf>")

    def spawn_entity(self, name, sdf, px, py, pz, ox, oy, oz, ow):
        """Spawn entity using native transport EntityFactory service (no subprocess)."""
        if not (self.gz_node and GZ_TRANSPORT_AVAILABLE):
            return

        try:
            req = gz_entity_factory_pb2.EntityFactory()
            req.sdf = sdf
            req.pose.position.x = float(px)
            req.pose.position.y = float(py)
            req.pose.position.z = float(pz)
            req.pose.orientation.x = float(ox)
            req.pose.orientation.y = float(oy)
            req.pose.orientation.z = float(oz)
            req.pose.orientation.w = float(ow)

            # Request entity creation
            self.gz_node.request(
                '/world/empty/create', req,
                gz_entity_factory_pb2.EntityFactory, gz_bool_pb2.Boolean,
                500
            )
        except Exception as e:
            self.get_logger().error(f"Spawning error for {name}: {e}")

    def listener_callback(self, msg):
        if self.ref_lat is None or self.ref_lon is None:
            self.update_reference_point()
            if self.ref_lat is None:
                return
        try:
            data = json.loads(msg.data)
            uav_list = data.get("konumBilgileri", data.get("konum_bilgileri", []))
            for npc in uav_list:
                tid = npc.get("takim_numarasi", npc.get("takimNumarasi"))
                iha_boylam = npc.get("iha_boylam", npc.get("IHA_boylam", 0.0))
                iha_enlem  = npc.get("iha_enlem",  npc.get("IHA_enlem",  0.0))
                iha_irtifa = npc.get("iha_irtifa", npc.get("IHA_irtifa", 0.0))
                x = (iha_boylam - self.ref_lon) * 111320.0 * math.cos(math.radians(self.ref_lat))
                y = (iha_enlem  - self.ref_lat) * 111320.0
                z = iha_irtifa

                if tid not in self.spawned_uavs:
                    self.spawn_uav(tid, x, y, z)
                    self.spawned_uavs.add(tid)
                    # We don't sleep here anymore as native transport is async and robust
                else:
                    self.move_uav(f"uav_{tid}", x, y, z)
        except Exception:
            pass

    def move_uav(self, name, x, y, z):
        """Move a kinematic UAV model via gz.transport13 Python bindings."""
        if self.gz_node and GZ_TRANSPORT_AVAILABLE:
            try:
                req = gz_pose_pb2.Pose()
                req.name = name
                req.position.x = float(x)
                req.position.y = float(y)
                req.position.z = float(z)
                req.orientation.w = 1.0
                self.gz_node.request(
                    '/world/empty/set_pose', req,
                    gz_pose_pb2.Pose, gz_bool_pb2.Boolean, 250
                )
            except Exception:
                pass

    def spawn_uav(self, id, x, y, z):
        name = f"uav_{id}"
        # Kinematic = not static, no gravity → can be moved by set_pose
        sdf = (f"<sdf version='1.6'><model name='{name}'><static>false</static>"
               f"<link name='l'><gravity>false</gravity><kinematic>true</kinematic>"
               f"<visual name='v'><geometry><sphere><radius>25.0</radius></sphere></geometry>"
               f"<material><ambient>1 1 0 1</ambient><diffuse>1 1 0 1</diffuse>"
               f"<emissive>1 1 0 1</emissive></material></visual>"
               f"<collision name='c'><geometry>"
               f"<sphere><radius>25.0</radius></sphere></geometry></collision>"
               f"</link></model></sdf>")
        self.spawn_entity(name, sdf, x, y, z, 0, 0, 0, 1)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(GazeboVisualizer())
    rclpy.shutdown()

if __name__ == '__main__': main()