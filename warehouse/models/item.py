class Item:
    def __init__(self, id, x, y, weight):
        self.id = id
        self.x = x
        self.y = y
        self.weight = weight
        self.picked = False
        self.assigned = False