# COMP3071_CW_Group_AI
Repository for the Designing Intelligent Agents (COMP3071) Coursework by Group AI.

## Description
This project simulates an autonomous warehouse robot system. It features multiple robots navigating a grid-based warehouse environment to pick up and deliver items while avoiding various types of obstacles. The simulation includes a graphical user interface (GUI) for visualization and control, along with performance tracking and metrics analysis.

## Features
* **Grid-Based Environment:** Simulates a warehouse floor plan with configurable dimensions.
* **Autonomous Robots:** Robots navigate the grid, pick up items based on capacity, and deliver them to a designated drop point.
* **Item Management:** Items with varying weights are randomly placed in the environment.
* **Obstacle Handling:** Supports permanent, temporary, and semi-permanent obstacles with lifecycles managed by an Obstacle Manager. Robots can interact with and potentially wait for temporary obstacles.
* **Advanced Pathfinding:**
    * Multiple pathfinding strategies (A\*, Adaptive Dynamic A\*, Proximal Policy Dijkstra).
    * Dynamic Strategy Selection: Intelligently chooses the best algorithm based on context (obstacle density, distance, load).
    * Collision Resolution: Handles potential collisions between robots.
    * Trajectory Tracking: Visualizes the planned path for robots.
* **GUI:**
    * Visual representation of the grid, robots, items, obstacles, and robot trajectories.
    * Simulation controls (Start, Pause, Reset).
    * Runtime entity manipulation (Add/Edit/Delete Robots & Items).
    * Obstacle placement controls.
    * Status panels displaying performance metrics and entity details.
    * Pathfinding strategy monitor.
    * Clustering toggle for item pickup strategy.
* **Simulation Management:**
    * Handles simulation lifecycle (start, pause, reset).
    * Manages robots, items, and the grid environment.
    * Includes stall detection and recovery mechanisms.
* **Analytics & Metrics:**
    * Tracks overall performance (time, steps, delivery efficiency).
    * Calculates detailed metrics (robot utilization, path lengths, strategy usage, obstacle interactions).
    * Provides visualization and reporting capabilities for metrics (requires `matplotlib`, `numpy`, `pandas`).

## Project Structure
* `main.py`: Main entry point for the simulation application.
* `core/`: Contains core models (Grid, Robot, Item) and utilities (Logger, Event System).
* `simulation/`: Contains the core simulation logic.
    * `warehouse.py`: Main simulation coordinator.
    * `controller/`: Components managing robot movement, item assignment, collisions, and simulation steps.
    * `manager/`: Components managing simulation lifecycle, entities (robots, items), and the grid.
    * `pathfinding/`: Pathfinding algorithms, strategies, and the strategy selector.
    * `obstacles/`: Obstacle management, classification, and layout generation.
    * `analytics/`: Performance tracking, stall detection, and metrics calculation/monitoring.
* `gui/`: Contains the graphical user interface components.
    * `application.py`: Main GUI application class.
    * `components/`: Reusable GUI elements (Menus, Dialogs, Monitors).
    * `handlers/`: Event handlers for user interactions and simulation events.
    * `panels/`: Specific UI panels (Control, Status, Legend).
    * `views/`: Canvas drawing and entity list displays.
* `requirements.txt`: (Assumed) Lists project dependencies.

## Setup and Installation

It is recommended to use a virtual environment to manage dependencies.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    * Ensure you have Python 3 installed.
    * Navigate to the project's root directory (`warehouse_robot_system` parent folder).
    * Run the following command:
        ```bash
        python -m venv venv
        ```
    * This creates a `venv` folder in your project directory.

3.  **Activate the virtual environment:**
    * **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    * Your command prompt should now indicate that you are in the `(venv)` environment.

4.  **Install dependencies:**
    * Make sure you have a `requirements.txt` file in the project root.
    * Run the following command:
        ```bash
        pip install -r requirements.txt
        ```
    * This will install libraries like `numpy`, `pandas`, and `matplotlib` needed for the analytics features.

## How to Run

1.  **Ensure the virtual environment is activated** (see Setup section).
2.  Navigate to the project's root directory (the one containing the `warehouse_robot_system` folder).
3.  Execute the main script:
    ```bash
    python warehouse_robot_system/main.py
    ```
4.  This will launch the graphical user interface for the simulation.

## Authors
* Kurone14   [ Yong Chun Choi (20413712)]
* darryl2003 [ Darryl Djohan  (20414727)]
