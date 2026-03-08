# Base ROS2 image (Jazzy Jalisco)
FROM ros:jazzy-ros-base

# Change shell to bash for easier sourcing
SHELL ["/bin/bash", "-c"]

# Install necessary build tools, Gazebo transport dependencies, and keys
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    python3-colcon-common-extensions \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Add Gazebo stable repository for direct Python bindings (python3-gz-*)
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-gz \
    python3-gz-transport13 \
    python3-gz-msgs10 \
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
