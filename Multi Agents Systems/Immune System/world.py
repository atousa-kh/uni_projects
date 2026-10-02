"""
Tissue World — The Body Environment
دنیای بافت — محیط بدن با بافت‌ها، عروق و عفونت‌ها

Generates an organic-looking tissue layout with:
  - Healthy tissue cells (passable)
  - Organ structures (impassable clusters)
  - Blood vessel corridors (travel routes)
  - Infection sites that spread over time
"""

import random
import math
from config import (
    GRID_COLS, GRID_ROWS, TISSUE, ORGAN, INFECTED, BLOOD_VESSEL,
    NUM_INITIAL_INFECTIONS, NUM_ORGAN_CLUSTERS, ORGAN_CLUSTER_RADIUS,
    VESSEL_COLS, VESSEL_ROWS, MAX_INFECTION_WAVES,
)


class TissueWorld:
    """
    Represents the body tissue environment.
    Grid is stored as grid[row][col] = cell_type.
    """

    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)

        self.grid = [[TISSUE for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.infections = []        # Current infected positions [(x, y), ...]
        self.cleared = []           # Cleared infection positions
        self.wave_count = 0         # Number of infection waves
        self.total_infections = 0
        self._generate_tissue()

    def _generate_tissue(self):
        """Generate organic tissue layout with vessels and organs."""
        # Step 1: Create blood vessel network
        self._create_vessels()

        # Step 2: Place organ structures (clusters of ORGAN cells)
        self._place_organs()

        # Step 3: Ensure agent starting positions are accessible
        start_positions = [
            (2, 2), (GRID_COLS - 3, 2), (GRID_COLS // 2, GRID_ROWS - 3)
        ]
        for sx, sy in start_positions:
            self._clear_area(sx, sy, radius=2)

        # Step 4: Add some organic texture to tissue
        self._add_tissue_texture()

        # Step 5: Place initial infections
        self._place_infections()

    def _create_vessels(self):
        """Create blood vessel corridors (like arteries and veins)."""
        # Main vertical vessels
        for col in VESSEL_COLS:
            for row in range(GRID_ROWS):
                self.grid[row][col] = BLOOD_VESSEL
                # Wider vessels at intersections
                if row in VESSEL_ROWS:
                    for dcol in [-1, 1]:
                        nc = col + dcol
                        if 0 <= nc < GRID_COLS:
                            self.grid[row][nc] = BLOOD_VESSEL

        # Main horizontal vessels
        for row in VESSEL_ROWS:
            for col in range(GRID_COLS):
                self.grid[row][col] = BLOOD_VESSEL
                if col in VESSEL_COLS:
                    for drow in [-1, 1]:
                        nr = row + drow
                        if 0 <= nr < GRID_ROWS:
                            self.grid[nr][col] = BLOOD_VESSEL

    def _place_organs(self):
        """Place organic-looking organ structures."""
        # Find suitable centers (away from vessel intersections)
        candidates = []
        for row in range(2, GRID_ROWS - 2):
            for col in range(2, GRID_COLS - 2):
                # Not on a main vessel
                if col not in VESSEL_COLS and row not in VESSEL_ROWS:
                    candidates.append((col, row))

        random.shuffle(candidates)

        placed = 0
        for cx, cy in candidates:
            if placed >= NUM_ORGAN_CLUSTERS:
                break

            radius = random.randint(*ORGAN_CLUSTER_RADIUS)

            # Draw organic cluster (not perfectly circular)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius + random.uniform(-0.5, 0.5):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS:
                            if self.grid[ny][nx] == TISSUE:
                                self.grid[ny][nx] = ORGAN
            placed += 1

    def _clear_area(self, cx, cy, radius=2):
        """Clear organ cells around a center point."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS:
                    if self.grid[ny][nx] == ORGAN:
                        self.grid[ny][nx] = TISSUE

    def _add_tissue_texture(self):
        """Add subtle texture variation to tissue cells."""
        # This is just visual - store in a separate texture map
        self.texture = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                self.texture[row][col] = random.randint(0, 3)

    def _place_infections(self):
        """Place initial infection sites."""
        # Find passable cells away from starting positions
        passable = [
            (x, y) for y in range(GRID_ROWS) for x in range(GRID_COLS)
            if self.grid[y][x] in {TISSUE, BLOOD_VESSEL}
        ]
        random.shuffle(passable)

        # Remove cells too close to starting positions
        start_positions = [(2, 2), (GRID_COLS - 3, 2), (GRID_COLS // 2, GRID_ROWS - 3)]
        filtered = []
        for pos in passable:
            too_close = False
            for sp in start_positions:
                if abs(pos[0] - sp[0]) + abs(pos[1] - sp[1]) < 5:
                    too_close = True
                    break
            if not too_close:
                filtered.append(pos)

        for i in range(min(NUM_INITIAL_INFECTIONS, len(filtered))):
            ix, iy = filtered[i]
            self._infect_cell(ix, iy)

    def _infect_cell(self, x, y):
        """Infect a single cell."""
        if self.grid[y][x] in {TISSUE, BLOOD_VESSEL}:
            self.grid[y][x] = INFECTED
            if (x, y) not in self.infections:
                self.infections.append((x, y))
                self.total_infections += 1
            return True
        return False

    # ─── Cell Access ───

    def get_cell(self, x, y):
        if 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS:
            return self.grid[y][x]
        return None

    def is_passable(self, x, y, avoid_infected=False):
        if not (0 <= x < GRID_COLS and 0 <= y < GRID_ROWS):
            return False
        cell = self.grid[y][x]
        if cell == ORGAN:
            return False
        if avoid_infected and cell == INFECTED:
            return False
        return True

    def is_valid_pos(self, x, y):
        return 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS

    # ─── Infection Management ───

    def clear_infection(self, x, y):
        """Clear an infection at the given position."""
        if (x, y) in self.infections:
            self.infections.remove((x, y))
            self.grid[y][x] = TISSUE
            self.cleared.append((x, y))
            return True
        return False

    def spread_infection(self):
        """Spread infection to adjacent tissue cells."""
        new_infections = []
        for ix, iy in list(self.infections):
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = ix + dx, iy + dy
                if self.is_valid_pos(nx, ny):
                    if self.grid[ny][nx] == TISSUE and random.random() < 0.2:
                        self._infect_cell(nx, ny)
                        new_infections.append((nx, ny))
        return new_infections

    def spawn_wave(self):
        """Spawn a new infection wave at a random location."""
        if self.wave_count >= MAX_INFECTION_WAVES:
            return []

        self.wave_count += 1
        # Find a passable cell far from current infections
        passable = [
            (x, y) for y in range(GRID_ROWS) for x in range(GRID_COLS)
            if self.grid[y][x] in {TISSUE, BLOOD_VESSEL}
        ]
        random.shuffle(passable)

        new = []
        # Create a small cluster (2-3 cells)
        if passable:
            cx, cy = passable[0]
            self._infect_cell(cx, cy)
            new.append((cx, cy))
            # Spread 1-2 more around it
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                if len(new) >= 3:
                    break
                nx, ny = cx + dx, cy + dy
                if self.is_valid_pos(nx, ny) and self.grid[ny][nx] in {TISSUE, BLOOD_VESSEL}:
                    self._infect_cell(nx, ny)
                    new.append((nx, ny))

        return new

    # ─── Queries ───

    def get_nearest(self, pos, targets):
        if not targets:
            return None
        return min(targets, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))

    def get_infections(self):
        return list(self.infections)

    def get_largest_cluster(self, infections=None):
        """Find the largest connected cluster of infections."""
        if infections is None:
            infections = self.infections
        if not infections:
            return []

        inf_set = set(infections)
        visited = set()
        largest = []

        for pos in infections:
            if pos in visited:
                continue
            # BFS to find cluster
            cluster = []
            queue = [pos]
            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)
                cluster.append(curr)
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nb = (curr[0] + dx, curr[1] + dy)
                    if nb in inf_set and nb not in visited:
                        queue.append(nb)
            if len(cluster) > len(largest):
                largest = cluster

        return largest

    @property
    def all_clear(self):
        return len(self.infections) == 0

    @property
    def health_percent(self):
        """Body health percentage (0-100)."""
        total_passable = sum(
            1 for y in range(GRID_ROWS) for x in range(GRID_COLS)
            if self.grid[y][x] != ORGAN
        )
        if total_passable == 0:
            return 100
        infected = len(self.infections)
        return max(0, int(100 * (1 - infected / total_passable) * 100) / 100)

    @property
    def stats(self):
        return {
            'infections_remaining': len(self.infections),
            'infections_cleared': len(self.cleared),
            'total_infections': self.total_infections,
            'wave_count': self.wave_count,
            'health': self.health_percent,
        }
