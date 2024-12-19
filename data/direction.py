UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


def xy_shift_parent_map(d):
    if d == UP:
        return [0, 1]
    elif d == RIGHT:
        return [-1, 0]
    elif d == DOWN:
        return [0, -1]
    elif d == LEFT:
        return [1, 0]
    else:
        return [0, 0]
