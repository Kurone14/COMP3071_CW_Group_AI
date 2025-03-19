from simulation.warehouse import WarehouseSimulation
from simulation.pathfinding import PathFinder
from simulation.assignment import ItemAssigner
from gui.main_window import WarehouseGUI

def main():
    width = 15
    height = 15
    robot_count = 4
    item_count = 0 
    obstacle_density = 0.06  
    
    gui = WarehouseGUI(width, height)
    
    temp_grid = [[0 for _ in range(width)] for _ in range(height)]
    temp_drop_point = (width-3, height-3)  
    path_finder = PathFinder(temp_grid, width, height, temp_drop_point)
    
    item_assigner = ItemAssigner(temp_grid, path_finder)
    
    simulation = WarehouseSimulation(
        width=width,
        height=height,
        robot_count=robot_count,
        item_count=item_count,
        obstacle_density=obstacle_density,
        gui=gui,
        path_finder=path_finder,
        item_assigner=item_assigner
    )
    
    gui.run()

if __name__ == "__main__":
    main()