"""
A* Pathfinding Algorithm
الگوریتم جستجوی A* برای مسیریابی سلول‌های ایمنی
"""

import heapq
from config import TISSUE, INFECTED, BLOOD_VESSEL, ORGAN


def astar(grid, start, goal, passable=None):
    """
    A* pathfinding on a 2D grid.

    Args:
        grid: 2D list [row][col] of cell types
        start: (x, y) start position
        goal: (x, y) goal position
        passable: set of cell types considered passable

    Returns:
        List of (x,y) positions forming the path (excluding start), or None.
    """
    if passable is None:
        passable = {TISSUE, INFECTED, BLOOD_VESSEL}

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    gx, gy = goal
    if not (0 <= gx < cols and 0 <= gy < rows):
        return None

    goal_passable = passable | {TISSUE, INFECTED, BLOOD_VESSEL}
    if grid[gy][gx] not in goal_passable:
        return None

    if start == goal:
        return []

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    counter = 0
    heapq.heappush(open_set, (0, counter, start))
    came_from = {}
    g_score = {start: 0}
    closed = set()

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)

            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if neighbor in closed:
                continue
            if grid[ny][nx] not in passable:
                continue

            # Slight preference for blood vessels (faster travel)
            extra_cost = 0
            if grid[ny][nx] == INFECTED:
                extra_cost = 3  # Slightly avoid infected areas unless necessary

            tentative_g = g_score[current] + 1 + extra_cost

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                counter += 1
                heapq.heappush(open_set, (f, counter, neighbor))

    return None


def manhattan_distance(a, b):
    """Calculate Manhattan distance between two points."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
