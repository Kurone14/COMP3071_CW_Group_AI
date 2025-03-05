"""
Visualization Module
Handles rendering the simulation, UI elements, and information display
"""
import pygame
import pymunk.pygame_util
import config

def render_simulation(screen, space, env, step_counter, num_robots):
    """Render the entire simulation including robots, environment, and UI elements"""
    # Clear the screen
    screen.fill((255, 255, 255))
    
    # Create drawing options for pymunk
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    # Draw physics objects
    space.debug_draw(draw_options)
    
    # Draw environment (obstacles, pickup/dropoff points, etc.)
    env.render(screen)
    
    # Draw UI elements
    render_ui(screen, step_counter, num_robots, env.layout_version)
    
    # Update display
    pygame.display.flip()

def render_ui(screen, step_counter, num_robots, layout_version):
    """Render UI elements including status information and instructions"""
    font = pygame.font.SysFont(None, 24)
    
    # Display simulation info
    info_text = font.render(
        f"Step: {step_counter} | Robots: {num_robots} | Layout v{layout_version}", 
        True, (0, 0, 0)
    )
    screen.blit(info_text, (10, 10))
    
    # Display instructions
    instructions = font.render("Press 'C' to change layout", True, (0, 0, 0))
    screen.blit(instructions, (10, config.SCREEN_HEIGHT - 30))

def render_robot_status(screen, robots):
    """Render detailed status for each robot"""
    font = pygame.font.SysFont(None, 18)
    
    y_pos = 40
    for robot in robots:
        status_text = font.render(
            f"Robot {robot.id}: {robot.state} | Target: {robot.target}", 
            True, (0, 0, 0)
        )
        screen.blit(status_text, (10, y_pos))
        y_pos += 20

def render_path(screen, robot):
    """Render the planned path for a robot"""
    if robot.path:
        # Draw lines connecting path points
        points = [(robot.body.position.x, robot.body.position.y)] + robot.path
        for i in range(len(points) - 1):
            pygame.draw.line(
                screen, 
                (0, 255, 255), 
                points[i], 
                points[i+1], 
                2
            )
        
        # Draw target as a circle
        if robot.target:
            pygame.draw.circle(
                screen,
                (255, 0, 255),
                robot.target,
                5,
                1
            )

def highlight_collisions(screen, robot, environment):
    """Highlight collision areas and near-miss situations"""
    # This would be called for each robot to show potential collision areas
    sensor_range = robot.sensor_range
    
    # Draw sensor range circle
    pygame.draw.circle(
        screen,
        (255, 0, 0, 128),  # Semi-transparent red
        (int(robot.body.position.x), int(robot.body.position.y)),
        sensor_range,
        1
    )
    
    # Highlight detected obstacles
    for obstacle in robot.detected_obstacles:
        pygame.draw.rect(
            screen,
            (255, 200, 0, 128),  # Semi-transparent yellow
            (obstacle['position'][0], obstacle['position'][1],
             obstacle['size'][0], obstacle['size'][1]),
            2
        )