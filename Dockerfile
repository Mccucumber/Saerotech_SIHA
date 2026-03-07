# Base ROS2 image
FROM ros:jazzy-ros-base

# Install necessary build tools
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set up the workspace
WORKDIR /ros2_ws

# Copy the source code into the workspace
COPY src/ /ros2_ws/src/

# Build the ROS2 workspace
RUN /bin/bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build"

# Copy and set up the entrypoint script
COPY ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]

# Default command to run your ROS2 node
# Modify this command if you have launch files or want to run a different node
CMD ["ros2", "run", "siha_telemetri", "harita_node"]
