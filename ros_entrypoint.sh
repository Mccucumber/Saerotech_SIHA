#!/bin/bash
set -e

# Setup ROS2 environment based on the ROS_DISTRO
source "/opt/ros/$ROS_DISTRO/setup.bash"

# Source the workspace
source "/ros2_ws/install/setup.bash"

exec "$@"
