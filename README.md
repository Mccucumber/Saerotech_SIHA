# Saerotech SİHA Telemetry and Web UI

This repository contains a ROS 2 implementation for a UAV (SİHA) Swarm Simulation, including a telemetry node (`harita_node`) and a live web-based Map UI driven by Leaflet.js. 

It is designed to be easily run completely via **Docker**, meaning you do not need to install ROS 2 locally to launch the simulation or view the UI.

## Features
- **ROS 2 Jazzy Base**: Runs nodes for publishing/simulating UAV positions and capturing them in `telemetri.json`.
- **Live Map UI**: Views all 15 UAVs live on a Leaflet map (Samsun-centered) using a lightweight Python Web Server.
- **Dual Views**: Provides both an `index.html` and `index4.html` view that can be accessed simultaneously.

## Prerequisites
Before you begin, ensure you have installed:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone <YOUR-GITHUB-REPO-URL>
   cd Saerotech_SIHA
   ```

2. **Build and Run with Docker Compose:**
   The `docker-compose.yml` file defines two containers: the ROS 2 workspace (`siha_telemetri`) and the Python web server (`web_ui`).
   
   To launch both, simply run:
   ```bash
   docker compose up --build
   ```
   > NOTE: The first build may take a few minutes as it pulls the `ros:jazzy-ros-base` image and compiles the workspace using `colcon build`.

3. **View the Live Map UI:**
   Once the containers are running, you can access the map interfaces from your regular web browser:
   - **Main UI:** `http://localhost:8080/index.html`
   - **Alternate UI:** `http://localhost:8080/index4.html`

4. **Stopping the Simulation:**
   To stop both containers gracefully, press `Ctrl + C` in the terminal where Docker Compose is running, or run:
   ```bash
   docker compose down
   ```

## Local Development (Without Docker)
If you prefer to run this natively on an Ubuntu/WSL system with ROS 2 Jazzy installed:

1. **Build the ROS 2 Workspace:**
   ```bash
   colcon build
   source install/setup.bash
   ```
2. **Run the ROS 2 Node:**
   ```bash
   ros2 run siha_telemetri harita_node
   ```
3. **Run the UI Server (in a separate terminal):**
   ```bash
   python3 serve_ui.py
   ```
   Then open `http://localhost:8080` in your web browser.
