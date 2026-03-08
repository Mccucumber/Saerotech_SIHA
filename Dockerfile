# Base ROS2 image (Jazzy Jalisco)
FROM ros:jazzy-ros-base

# Change shell to bash for easier sourcing
SHELL ["/bin/bash", "-c"]

# Install necessary build tools and Gazebo transport dependencies
# ros-jazzy-ros-gz is required for the native Python transport in gazebo_visualizer.py
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

# Set up the workspace
WORKDIR /ros2_ws

# Copy the source code into the workspace
COPY src/ /ros2_ws/src/

# Build the ROS2 workspace
RUN source /opt/ros/$ROS_DISTRO/setup.bash && colcon build

# Copy and set up the entrypoint script
COPY ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]

# The CMD is typically overridden in docker-compose.yml for each service
CMD ["ros2", "run", "siha_telemetri", "harita_node"]
