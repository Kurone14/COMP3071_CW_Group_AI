class Robot:
    def __init__(self, id, x, y, capacity):
        self.id = id
        self.x = x
        self.y = y
        self.capacity = capacity
        self.current_weight = 0
        self.carrying_items = []
        self.target_items = []
        self.path = []
        self.steps = 0