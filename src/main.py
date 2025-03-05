"""
Warehouse Robot Simulation - Main Entry Point
"""
import os
import argparse
import pygame
import random
import config
import time
import pymunk

from core.environment import WarehouseEnvironment
from core.robot import WarehouseRobot
from core.physics import setup_physics
from core.visualization import render_simulation
from agents.learning_agent import RobotLearningAgent
from utils.metrics import PerformanceEvaluator

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Warehouse Robot Simulation')
    parser.add_argument('--mode', type=str, default='simulation', choices=['train', 'simulation'],
                        help='Mode to run: train or simulation')
    parser.add_argument('--num_robots', type=int, default=5, help='Number of robots')
    parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    parser.add_argument('--load_model', type=str, default=None, help='Path to load trained model')
    parser.add_argument('--save_model', type=str, default='models/robot_model', help='Path to save trained model')
    return parser.parse_args()

def should_change_layout(robots, step_counter, last_layout_change):
    """Determine if layout should change based on robot states and task completion"""
    # Check if enough time has passed since last layout change
    if step_counter - last_layout_change < config.MIN_STEPS_BETWEEN_LAYOUT_CHANGES:
        return False
    
    # Only change layout when all robots are idle or most robots have completed tasks
    idle_count = sum(1 for robot in robots if robot.state == "idle")
    carrying_count = sum(1 for robot in robots if robot.carrying_item)
    
    # If most robots are idle, it's a good time to change layout
    if idle_count >= len(robots) * 0.6:
        return True
    
    # Or if a significant number of tasks were completed (half the robots changed carrying state)
    if carrying_count >= len(robots) // 2:
        return True
    
    return False

def assign_tasks(robots, environment, evaluator=None):
    """Assign pickup and dropoff tasks to idle robots with better coordination"""
    
    # Track which points are already assigned to prevent conflicts
    assigned_pickup_points = set()
    assigned_dropoff_points = set()
    
    # First, check if any robots have reached their targets
    for robot in robots:
        if robot.state in ["pickup", "dropoff"]:
            # Record task completion
            if robot.task_start_time and evaluator:
                task_end_time = time.time()
                evaluator.record_task_completion(
                    robot.id, 
                    robot.state, 
                    robot.task_start_time, 
                    task_end_time
                )
                print(f"Robot {robot.id} completed {robot.state} task")
            
            # Update robot state based on completed task
            if robot.state == "pickup":
                robot.carrying_item = True
                robot.target = None
                robot.state = "idle"
                robot.task_start_time = None
            elif robot.state == "dropoff" and robot.carrying_item:
                robot.carrying_item = False
                robot.target = None
                robot.state = "idle"
                robot.task_start_time = None
    
    # Check which pickup/dropoff points are already targeted by moving robots
    for robot in robots:
        if robot.state == "moving" and robot.target:
            # Find which pickup/dropoff point this robot is heading to
            for point in environment.pickup_points:
                if (abs(point['position'][0] - robot.target[0]) < 5 and 
                    abs(point['position'][1] - robot.target[1]) < 5):
                    assigned_pickup_points.add(point['id'])
            
            for point in environment.dropoff_points:
                if (abs(point['position'][0] - robot.target[0]) < 5 and 
                    abs(point['position'][1] - robot.target[1]) < 5):
                    assigned_dropoff_points.add(point['id'])
    
    # Then assign new tasks to idle robots
    for robot in robots:
        if robot.state == "idle" and not robot.target:
            # Assign pickup task if robot is not carrying an item
            if not robot.carrying_item:
                # Get available pickup points (not already assigned)
                available_pickup_points = [
                    p for p in environment.pickup_points 
                    if p['id'] not in assigned_pickup_points
                ]
                
                if available_pickup_points:
                    # Choose closest pickup point
                    closest_point = min(
                        available_pickup_points,
                        key=lambda p: (p['position'][0] - robot.body.position.x)**2 + 
                                     (p['position'][1] - robot.body.position.y)**2
                    )
                    
                    robot.target = closest_point['position']
                    robot.target_id = closest_point['id']
                    robot.plan_path(robot.target)
                    robot.task_start_time = time.time()
                    assigned_pickup_points.add(closest_point['id'])
                    print(f"Robot {robot.id} assigned pickup task at {robot.target}")
            
            # Assign dropoff task if robot is carrying an item
            elif robot.carrying_item:
                # Get available dropoff points (not already assigned)
                available_dropoff_points = [
                    p for p in environment.dropoff_points 
                    if p['id'] not in assigned_dropoff_points
                ]
                
                if available_dropoff_points:
                    # Choose closest dropoff point
                    closest_point = min(
                        available_dropoff_points,
                        key=lambda p: (p['position'][0] - robot.body.position.x)**2 + 
                                     (p['position'][1] - robot.body.position.y)**2
                    )
                    
                    robot.target = closest_point['position']
                    robot.target_id = closest_point['id']
                    robot.plan_path(robot.target)
                    robot.task_start_time = time.time()
                    assigned_dropoff_points.add(closest_point['id'])
                    print(f"Robot {robot.id} assigned dropoff task at {robot.target}")

def run_training(env, robots, learning_agents, args, evaluator):
    """Run training mode"""
    print("Starting training mode...")
    
    # Train robots
    for episode in range(args.episodes):
        print(f"Episode {episode+1}/{args.episodes}")
        
        # Reset environment for new episode
        env.reset()
        
        # Train each agent
        for i, agent in enumerate(learning_agents):
            agent.train(env, robots[i], episode_num=episode)
            
        # Periodically change layout to train adaptation
        if episode > 0 and episode % 100 == 0:
            print("Changing warehouse layout...")
            env.change_layout()
            evaluator.record_layout_change()
            
        # Save models periodically
        if episode > 0 and episode % 200 == 0:
            for i, agent in enumerate(learning_agents):
                model_path = f"{args.save_model}_{i}.pkl"
                agent.save_model(model_path)
                print(f"Saved model for robot {i} to {model_path}")
    
    # Save final models
    for i, agent in enumerate(learning_agents):
        model_path = f"{args.save_model}_{i}.pkl"
        agent.save_model(model_path)
        print(f"Saved final model for robot {i} to {model_path}")

def should_change_layout(robots, step_counter, last_layout_change):
    """Determine if layout should change based on robot states and task completion"""
    # Check if enough time has passed since last layout change
    if step_counter - last_layout_change < config.MIN_STEPS_BETWEEN_LAYOUT_CHANGES:
        return False
    
    # Only change layout when all robots are idle or most robots have completed tasks
    idle_count = sum(1 for robot in robots if robot.state == "idle")
    carrying_count = sum(1 for robot in robots if robot.carrying_item)
    
    # If most robots are idle, it's a good time to change layout
    if idle_count >= len(robots) * 0.6:
        return True
    
    # Or if a significant number of tasks were completed (half the robots changed carrying state)
    if carrying_count >= len(robots) // 2:
        return True
    
    return False

def run_simulation(env, robots, learning_agents, space, evaluator, args=None):
    """Run simulation mode with improved task management and layout changes"""
    print("Starting improved simulation mode...")
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption(config.CAPTION)
    clock = pygame.time.Clock()
    
    # For drawing pymunk objects
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    # Start evaluation
    evaluator.start_evaluation()
    
    # Set up font for better text display
    font = pygame.font.SysFont(None, 24)
    status_font = pygame.font.SysFont(None, 18)
    
    # Simulation loop with improvements
    running = True
    step_counter = 0
    last_layout_change = 0
    auto_layout_change = args.auto_layout_change if hasattr(args, 'auto_layout_change') else True
    
    # Initial task assignment
    assign_tasks(robots, env, evaluator)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    # Change layout on 'c' key press
                    env.change_layout()
                    evaluator.record_layout_change()
                    last_layout_change = step_counter
                    print("Layout changed by user!")
                elif event.key == pygame.K_r:
                    # Reset any stuck robots on 'r' key press
                    for robot in robots:
                        if robot.state == "moving" and (len(robot.path) == 0 or robot.check_if_stuck(force_check=True)):
                            robot.state = "idle"
                            robot.target = None
                            robot.body.velocity = (0, 0)
                    print("Reset stuck robots")
                elif event.key == pygame.K_s:
                    # Display status report on 's' key
                    for robot in robots:
                        print(f"Robot {robot.id}: state={robot.state}, position=({robot.body.position.x:.1f}, {robot.body.position.y:.1f}), target={robot.target}, carrying={robot.carrying_item}")
                elif event.key == pygame.K_a:
                    # Toggle auto layout change
                    auto_layout_change = not auto_layout_change
                    print(f"Auto layout change: {'ON' if auto_layout_change else 'OFF'}")
        
        # Assign tasks to idle robots
        if step_counter % config.TASK_ASSIGNMENT_INTERVAL == 0 or step_counter == 0:
            assign_tasks(robots, env, evaluator)
        
        # Update physics
        space.step(1/config.FPS)
        
        # Update environment
        env.step(None, evaluator)  # Pass None for learning_agents since we're not using them in simulation
        
        # Check if any robots need to be reset (out of bounds or stuck)
        for robot in robots:
            # Reset if out of bounds
            x, y = robot.body.position
            if x < -50 or x > env.width + 50 or y < -50 or y > env.height + 50:
                print(f"Robot {robot.id} reset - out of bounds at ({x:.1f}, {y:.1f})")
                robot.body.position = (env.width/2, env.height/2)
                robot.body.velocity = (0, 0)
                robot.state = "idle"
                robot.target = None
                robot.path = []
            
            # Check for stuck robots periodically
            if step_counter % config.STUCK_CHECK_INTERVAL == robot.id * 20:  # Stagger checks across robots
                if robot.state == "moving" and robot.check_if_stuck():
                    # Robot's check_if_stuck method already handles replanning
                    pass
        
        # Debug: Print robot states periodically
        if step_counter % 200 == 0:
            active_robots = sum(1 for robot in robots if robot.state != "idle")
            carrying_robots = sum(1 for robot in robots if robot.carrying_item)
            print(f"Step {step_counter}: {active_robots} active robots, {carrying_robots} carrying items")
            for robot in robots:
                print(f"Robot {robot.id}: state={robot.state}, position=({robot.body.position.x:.1f}, {robot.body.position.y:.1f}), target={robot.target}, carrying={robot.carrying_item}")
        
        # Render with improved visuals
        screen.fill((255, 255, 255))
        
        # Draw environment elements
        env.render(screen)
        
        # Draw robot paths and states (custom rendering)
        for robot in robots:
            # Draw path
            if robot.path and len(robot.path) > 0:
                path_points = [(robot.body.position.x, robot.body.position.y)] + robot.path
                pygame.draw.lines(screen, (0, 100, 0), False, path_points, 2)
            
            # Draw robot with state-based color
            color = config.ROBOT_COLORS.get(robot.state, (128, 128, 128))
            
            # If carrying, use carrying color
            if robot.carrying_item:
                color = config.ROBOT_COLORS["carrying"]
                
            pygame.draw.circle(
                screen, 
                color, 
                (int(robot.body.position.x), int(robot.body.position.y)), 
                12
            )
            
            # Draw robot ID
            id_text = status_font.render(str(robot.id), True, (255, 255, 255))
            screen.blit(
                id_text, 
                (int(robot.body.position.x) - 4, int(robot.body.position.y) - 6)
            )
        
        # Display info
        info_text = font.render(
            f"Step: {step_counter} | Robots: {len(robots)} | Layout v{env.layout_version}", 
            True, (0, 0, 0)
        )
        screen.blit(info_text, (10, 10))
        
        # Display task statistics
        tasks_completed = sum(
            data.get('tasks_completed', 0) 
            for _, data in evaluator.robot_utilization.items()
        )
        
        stats_text = font.render(
            f"Tasks Completed: {tasks_completed} | "
            f"Collisions: {evaluator.collision_counts} | "
            f"Auto Layout: {'ON' if auto_layout_change else 'OFF'}", 
            True, (0, 0, 0)
        )
        screen.blit(stats_text, (10, 35))
        
        # Instructions
        instructions = font.render(
            "Press 'C': change layout | 'R': reset stuck robots | 'S': status | 'A': toggle auto layout", 
            True, (0, 0, 0)
        )
        screen.blit(instructions, (10, 570))
        
        pygame.display.flip()
        
        # Check if we should change layout
        if auto_layout_change and should_change_layout(robots, step_counter, last_layout_change):
            env.change_layout()
            evaluator.record_layout_change()
            last_layout_change = step_counter
            print(f"Layout automatically changed at step {step_counter} based on task completion")
        
        # Cap at 60 FPS
        clock.tick(config.FPS)
        step_counter += 1
    
    # Generate performance report
    report = evaluator.generate_report()
    print("\nPerformance Report:")
    for metric, value in report.items():
        if metric != "robot_performance":  # Skip the detailed robot data for cleaner output
            print(f"{metric}: {value}")
    
    pygame.quit()
    return report

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Warehouse Robot Simulation')
    parser.add_argument('--mode', type=str, default='simulation', choices=['train', 'simulation'],
                        help='Mode to run: train or simulation')
    parser.add_argument('--num_robots', type=int, default=5, help='Number of robots')
    parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    parser.add_argument('--load_model', type=str, default=None, help='Path to load trained model')
    parser.add_argument('--save_model', type=str, default='models/robot_model', help='Path to save trained model')
    parser.add_argument('--auto_layout_change', action='store_true', default=True, 
                        help='Automatically change layout based on task completion')
    return parser.parse_args()

def run_training(env, robots, learning_agents, args, evaluator):
    """Run training mode with improved training process"""
    print("Starting training mode...")
    
    # Train robots
    for episode in range(args.episodes):
        print(f"Episode {episode+1}/{args.episodes}")
        
        # Reset environment for new episode
        env.reset()
        
        # Setup episode statistics
        episode_rewards = []
        episode_steps = 0
        
        # Run episode steps
        max_episode_steps = 500  # Limit steps per episode
        
        while episode_steps < max_episode_steps:
            episode_steps += 1
            
            # Train each agent
            for i, agent in enumerate(learning_agents):
                reward = agent.train(env, robots[i], episode_num=episode)
                if reward is not None:
                    episode_rewards.append(reward)
            
            # Update environment
            env.step(learning_agents)
        
        # Print episode statistics
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0
        print(f"Episode {episode+1}: Avg Reward = {avg_reward:.2f}, Steps = {episode_steps}")
            
        # Periodically change layout to train adaptation
        if episode > 0 and episode % 50 == 0:  # More frequent changes
            print("Changing warehouse layout...")
            env.change_layout()
            evaluator.record_layout_change()
            
        # Save models periodically
        if episode > 0 and episode % 100 == 0:
            for i, agent in enumerate(learning_agents):
                model_path = f"{args.save_model}_{i}.pkl"
                agent.save_model(model_path)
                print(f"Saved model for robot {i} to {model_path}")
        
        # Decrease exploration rate
        for agent in learning_agents:
            agent.exploration_rate = max(
                agent.min_exploration_rate, 
                agent.exploration_rate * agent.exploration_decay
            )
    
    # Save final models
    for i, agent in enumerate(learning_agents):
        model_path = f"{args.save_model}_{i}.pkl"
        agent.save_model(model_path)
        print(f"Saved final model for robot {i} to {model_path}")#!/usr/bin/env python3

def main():
    """Main function"""
    args = parse_args()
    
    # Create models directory if it doesn't exist
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    
    # Initialize environment
    env = WarehouseEnvironment(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    
    # Add obstacles with better placement
    env.add_obstacle((100, 100), (50, 50))
    env.add_obstacle((300, 200), (100, 30))
    env.add_obstacle((500, 400), (70, 70))
    env.add_obstacle((200, 400), (60, 60))
    env.add_obstacle((600, 150), (80, 40))
    
    # Initialize physics space
    space = setup_physics()
    
    # Create robots with better starting positions
    robots = []
    learning_agents = []
    
    # Calculate initial positions to avoid bunching
    start_x = 100
    start_y = 50
    x_spacing = min(100, (env.width - 200) / max(1, args.num_robots - 1))
    
    for i in range(args.num_robots):
        # Position robots in a more distributed pattern
        robot_x = start_x + i * x_spacing
        robot_y = start_y + (30 * (i % 2))  # Alternate rows slightly
        
        robot = WarehouseRobot(space, (robot_x, robot_y), i)
        robots.append(robot)
        env.add_robot(robot)
        
        # Set environment reference for each robot
        robot.environment = env
        
        # Create learning agent for each robot
        agent = RobotLearningAgent(robot_id=i)
        learning_agents.append(agent)
        
        # Load model if specified
        if args.load_model:
            model_path = f"{args.load_model}_{i}.pkl"
            if os.path.exists(model_path):
                agent.load_model(model_path)
                print(f"Loaded model for robot {i} from {model_path}")
    
    # Initialize performance evaluator
    evaluator = PerformanceEvaluator()
    
    # Run in specified mode
    if args.mode == 'train':
        run_training(env, robots, learning_agents, args, evaluator)
    elif args.mode == 'simulation':
        run_simulation(env, robots, learning_agents, space, evaluator, args)

if __name__ == "__main__":
    main()