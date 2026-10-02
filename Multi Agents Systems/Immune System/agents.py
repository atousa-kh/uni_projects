"""
Immune Cell Agents — Three different architectures
سلول‌های ایمنی با سه معماری متفاوت

1. NeutrophilAgent  (نوتروفیل) - REACTIVE: immediate phagocytosis reflex
2. TCellAgent       (سلول T)   - DELIBERATIVE: strategic targeting with A*
3. MacrophageAgent  (ماکروفاژ) - HYBRID: reactive eating + deliberative migration + signaling
"""

import random
from config import (
    TISSUE, INFECTED, BLOOD_VESSEL, ORGAN,
    GRID_COLS, GRID_ROWS, CELL_SIZE, TOP_BAR_HEIGHT,
    REACTIVE, DELIBERATIVE, HYBRID, AGENT_INFO, COLORS,
    AGENT_MOVE_INTERVAL,
)
from pathfinding import astar, manhattan_distance
from messaging import (
    CytokineSignal, CytokineBus,
    SIG_PATHOGEN_FOUND, SIG_INFECTION_CLEARED, SIG_INFECTION_SPREAD,
    SIG_RECRUIT, SIG_COORDINATE, SIG_DANGER,
    SIG_STATUS, SIG_TARGET_ASSIGN,
)


# ════════════════════════════════════════════════════════════════
#  Base Immune Cell
# ════════════════════════════════════════════════════════════════

class BaseImmuneCell:
    """Base class for all immune cell agents."""

    def __init__(self, agent_type, world, cytokine_bus):
        info = AGENT_INFO[agent_type]
        self.name = info['name']
        self.agent_type = agent_type
        self.symbol = info['symbol']
        self.color = COLORS[info['color_key']]
        self.color_dark = COLORS.get(info['color_key'] + '_dark', self.color)
        self.color_glow = COLORS.get(info['color_key'] + '_glow', self.color)
        self.trail_color = COLORS.get('trail_' + info['color_key'].lower(), self.color)

        # Position
        self.pos = info['start_pos']
        self.pixel_pos = self._grid_to_pixel(self.pos)
        self.target_pixel_pos = self.pixel_pos
        self.moving = False

        # References
        self.world = world
        self.cytokine_bus = cytokine_bus

        # Trail
        self.trail = [self.pos]
        self.max_trail = 50

        # Status
        self.current_action = "Patrolling..."
        self.status = "idle"
        self.pathogens_engulfed = 0

        # Register with cytokine bus
        self.cytokine_bus.register(self.name)

    def _grid_to_pixel(self, grid_pos):
        x = grid_pos[0] * CELL_SIZE + CELL_SIZE // 2
        y = grid_pos[1] * CELL_SIZE + CELL_SIZE // 2 + TOP_BAR_HEIGHT
        return (float(x), float(y))

    def move_to(self, new_pos):
        if new_pos != self.pos:
            self.pos = new_pos
            self.trail.append(new_pos)
            if len(self.trail) > self.max_trail:
                self.trail = self.trail[-self.max_trail:]
            self.target_pixel_pos = self._grid_to_pixel(new_pos)
            self.moving = True

    def update_pixel_pos(self, dt_ms):
        from config import SMOOTH_MOVE_SPEED
        tx, ty = self.target_pixel_pos
        cx, cy = self.pixel_pos
        dx, dy = tx - cx, ty - cy
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < 1.0:
            self.pixel_pos = self.target_pixel_pos
            self.moving = False
        else:
            move = min(SMOOTH_MOVE_SPEED * dt_ms / 1000.0, dist)
            self.pixel_pos = (cx + dx / dist * move, cy + dy / dist * move)

    def emit_signal(self, signal_type, content, target=None):
        signal = CytokineSignal(self.name, signal_type, content, target)
        self.cytokine_bus.emit(signal)

    def receive_signals(self):
        return self.cytokine_bus.receive(self.name)

    def is_cardinal_adjacent(self, pos):
        dx = abs(pos[0] - self.pos[0])
        dy = abs(pos[1] - self.pos[1])
        return (dx + dy) == 1

    def decide(self):
        raise NotImplementedError


# ════════════════════════════════════════════════════════════════
#  1. REACTIVE — Neutrophil (نوتروفیل)
# ════════════════════════════════════════════════════════════════

class NeutrophilAgent(BaseImmuneCell):
    """
    REACTIVE ARCHITECTURE (واکنشی)

    The neutrophil is the body's first responder.
    Pure reflex behavior: Sense nearest pathogen → Move toward it → Engulf.

    Key characteristics:
    - NO plan memory: recalculates path every single step
    - NO deliberation: never compares alternatives
    - Immediate reflex toward the nearest infection (stimulus)
    - Uses A* as a "reflex" — recalculated each step, never stored
    - Can move through infected tissue (brave first responder!)
    - This is biologically accurate: neutrophils chemotax toward signals
    """

    def __init__(self, world, cytokine_bus):
        super().__init__(REACTIVE, world, cytokine_bus)
        self.last_infection_count = 0
        self.stuck_counter = 0

    def decide(self):
        """Reactive decision: sense → reflex, NO plan memory."""

        # ─── CHECK INCOMING SIGNALS ───
        signals = self.receive_signals()
        for sig in signals:
            if sig.signal_type == SIG_TARGET_ASSIGN:
                # Neutrophil ignores assignments — follows chemotaxis instinct
                self.emit_signal(
                    SIG_STATUS,
                    f"Chemotaxis override! Following my nose, not orders.",
                    target=sig.sender
                )
            elif sig.signal_type == SIG_RECRUIT:
                # Recruitment signal acknowledged (but still follows instinct)
                pass

        # ─── REFLEX 1: Engulf adjacent pathogen ───
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.pos[0] + dx, self.pos[1] + dy
            if self.world.get_cell(nx, ny) == INFECTED:
                # REFLEX: Phagocytize immediately!
                self.world.clear_infection(nx, ny)
                self.pathogens_engulfed += 1
                self.current_action = f"PHAGOCYTOSIS at ({nx},{ny})!"
                self.status = "active"
                self.emit_signal(
                    SIG_INFECTION_CLEARED,
                    f"Pathogen at ({nx},{ny}) engulfed!"
                )
                self.stuck_counter = 0
                return

        # ─── REFLEX 2: Chemotax toward nearest pathogen ───
        infections = self.world.get_infections()

        if not infections:
            self.current_action = "Patrolling — no pathogens detected"
            self.status = "idle"
            return

        # Find nearest infection (stimulus)
        nearest = self.world.get_nearest(self.pos, infections)

        # REFLEX: Compute one step using A* (as reflex, not a stored plan!)
        # Key: path is NOT saved — recomputed every single step
        passable = {TISSUE, INFECTED, BLOOD_VESSEL}
        path = astar(self.world.grid, self.pos, nearest, passable=passable)

        if path:
            self.move_to(path[0])
            self.current_action = f"CHEMOTAXIS toward {nearest}"
            self.status = "active"
            self.stuck_counter = 0
        else:
            # No path found — random exploration (still reactive!)
            self.stuck_counter += 1
            random_move = self._random_passable_move()
            if random_move:
                self.move_to(random_move)
                self.current_action = f"EXPLORING (no path to {nearest})"
                self.status = "active"
            else:
                self.current_action = "BLOCKED! Cannot reach pathogen"
                self.status = "danger"

        # ─── Report infection sightings ───
        current_count = len(infections)
        if current_count != self.last_infection_count:
            if current_count > self.last_infection_count:
                self.emit_signal(
                    SIG_PATHOGEN_FOUND,
                    f"Chemotaxis sensed {current_count} infections! Nearest: {nearest}"
                )
            self.last_infection_count = current_count

    def _random_passable_move(self):
        options = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.pos[0] + dx, self.pos[1] + dy
            if self.world.is_passable(nx, ny, avoid_infected=False):
                options.append((nx, ny))
        if options:
            return random.choice(options)
        return None


# ════════════════════════════════════════════════════════════════
#  2. DELIBERATIVE — T-Cell (سلول T)
# ════════════════════════════════════════════════════════════════

class TCellAgent(BaseImmuneCell):
    """
    DELIBERATIVE ARCHITECTURE (تفکری)

    T-Cells are strategic: they identify infection clusters,
    plan optimal attack routes, and follow plans deliberately.
    When they reach a cluster, they release cytotoxic chemicals
    that clear the entire local cluster (apoptosis induction).

    Key characteristics:
    - Maintains internal state: current plan, target cluster
    - Targets LARGEST infection cluster (strategic choice)
    - Plans optimal path with A* and follows it step by step
    - Replans when environment changes or plan becomes blocked
    - CYTOTOXIC BURST: clears all adjacent infections when attacking
      (simulates apoptosis induction in infected cells)
    """

    def __init__(self, world, cytokine_bus):
        super().__init__(DELIBERATIVE, world, cytokine_bus)
        self.plan = []              # Planned route
        self.target = None          # Current target infection
        self.assigned_target = None # Target assigned by macrophage

    def decide(self):
        """Deliberative decision: sense → plan → act."""

        # ─── CHECK INCOMING SIGNALS ───
        signals = self.receive_signals()
        for sig in signals:
            if sig.signal_type == SIG_TARGET_ASSIGN:
                self.assigned_target = sig.content
                self.plan = []
                self.target = None
            elif sig.signal_type == SIG_INFECTION_CLEARED:
                if self.target and str(self.target) in sig.content:
                    self.target = None
                    self.plan = []
            elif sig.signal_type == SIG_RECRUIT:
                # Consider replanning when recruited to an area
                pass

        # ─── ACTION 1: Clear adjacent or on-target infection ───
        if self.target:
            # Check if we're ON the target
            if self.pos == self.target:
                cell = self.world.get_cell(*self.target)
                if cell == INFECTED:
                    # CYTOTOXIC BURST: Clear target + all adjacent infections!
                    cleared = self._cytotoxic_burst(self.target)
                    self.pathogens_engulfed += cleared
                    self.current_action = f"CYTOTOXIC BURST at {self.target}! ({cleared} cleared)"
                    self.status = "active"
                    self.target = None
                    self.plan = []
                    return
                else:
                    self.target = None
                    self.plan = []
            # Check if we're ADJACENT to the target
            elif self.is_cardinal_adjacent(self.target):
                cell = self.world.get_cell(*self.target)
                if cell == INFECTED:
                    # CYTOTOXIC BURST
                    cleared = self._cytotoxic_burst(self.target)
                    self.pathogens_engulfed += cleared
                    self.current_action = f"CYTOTOXIC BURST at {self.target}! ({cleared} cleared)"
                    self.status = "active"
                    self.target = None
                    self.plan = []
                    return
                else:
                    self.target = None
                    self.plan = []

        # ─── ACTION 2: Follow existing plan ───
        if self.plan:
            next_step = self.plan[0]
            cell = self.world.get_cell(next_step[0], next_step[1])
            # Allow stepping on infected cells only if it's the target (final step)
            is_final_step = (len(self.plan) == 1 and next_step == self.target)
            can_move = (
                cell != ORGAN and cell is not None and
                (not (cell == INFECTED) or is_final_step)
            )
            if can_move:
                self.move_to(next_step)
                self.plan.pop(0)
                self.current_action = (
                    f"EN ROUTE to {self.target} "
                    f"({len(self.plan)} steps left)"
                )
                self.status = "active"
                return
            else:
                # Path blocked — must replan
                self.current_action = "REPLANNING — path blocked"
                self.plan = []

        # ─── ACTION 3: Choose target and plan ───
        infections = self.world.get_infections()

        if not infections:
            self.current_action = "Patrolling — tissue clear"
            self.status = "idle"
            self.target = None
            return

        # STRATEGIC CHOICE: Target the largest cluster
        cluster = self.world.get_largest_cluster(infections)
        target = None

        if cluster:
            # Target the infection nearest to us within the largest cluster
            target = self.world.get_nearest(self.pos, cluster)
        else:
            target = self.world.get_nearest(self.pos, infections)

        # Check assigned target
        if self.assigned_target:
            for inf in infections:
                if str(inf) in str(self.assigned_target):
                    target = inf
                    break
            self.assigned_target = None

        self.target = target

        # Plan path using A* (avoid infected tissue — T-Cells take safe routes)
        passable = {TISSUE, BLOOD_VESSEL, INFECTED}
        path = astar(self.world.grid, self.pos, target, passable=passable)

        if path:
            self.plan = path
            self.current_action = (
                f"STRATEGY: Route to {target} "
                f"(cluster size: {len(cluster)}, {len(path)} steps)"
            )
            self.status = "active"
            self.emit_signal(
                SIG_COORDINATE,
                f"Targeting infection cluster at {target} ({len(cluster)} cells)"
            )
        else:
            # Try alternative — just go to nearest infection
            alt = self.world.get_nearest(self.pos, infections)
            if alt != target:
                alt_path = astar(self.world.grid, self.pos, alt, passable=passable)
                if alt_path:
                    self.target = alt
                    self.plan = alt_path
                    self.current_action = (
                        f"STRATEGY: Alternative target at {alt} ({len(alt_path)} steps)"
                    )
                    self.status = "active"
                    return

            self.current_action = "PLANNING — No safe path! Waiting..."
            self.status = "danger"
            self.target = None

    def _cytotoxic_burst(self, center):
        """
        CYTOTOXIC BURST: T-Cell releases cytotoxic chemicals
        that clear the target infection AND all adjacent infected cells.
        This simulates apoptosis induction in a cluster of infected cells.
        """
        cleared = 0
        # Clear the target
        if self.world.get_cell(*center) == INFECTED:
            self.world.clear_infection(*center)
            cleared += 1

        # Clear all adjacent infections (the "burst" effect)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = center[0] + dx, center[1] + dy
            if self.world.get_cell(nx, ny) == INFECTED:
                self.world.clear_infection(nx, ny)
                cleared += 1

        # Also clear diagonal neighbors (weaker effect)
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = center[0] + dx, center[1] + dy
            if self.world.get_cell(nx, ny) == INFECTED:
                self.world.clear_infection(nx, ny)
                cleared += 1

        self.emit_signal(
            SIG_INFECTION_CLEARED,
            f"Cytotoxic burst at {center}! {cleared} infections eliminated!"
        )
        self.emit_signal(
            SIG_COORDINATE,
            f"Area {center} sterilized by T-Cell cytotoxic burst!"
        )
        return cleared


# ════════════════════════════════════════════════════════════════
#  3. HYBRID — Macrophage (ماکروفاژ)
# ════════════════════════════════════════════════════════════════

class MacrophageAgent(BaseImmuneCell):
    """
    HYBRID ARCHITECTURE (ترکیبی)

    Macrophages combine reactive and deliberative layers:
    - REACTIVE LAYER: Detect nearby infection → Engulf immediately
    - REACTIVE LAYER: Too close to large infection → Retreat
    - DELIBERATIVE LAYER: Plan migration to infection areas
    - COMMUNICATION: Emit cytokine signals to coordinate other cells

    Key characteristics:
    - Two-layer architecture (reactive + deliberative)
    - Reactive responses override deliberative plans
    - Eats pathogens when adjacent (reactive phagocytosis)
    - Retreats from overwhelming infection (reactive evasion)
    - Plans migration routes (deliberative)
    - Signals other cells about infection locations (cytokine signaling)
    """

    def __init__(self, world, cytokine_bus):
        super().__init__(HYBRID, world, cytokine_bus)
        self.plan = []
        self.target = None
        self.known_infections = set()
        self.threat_active = False
        self.coordination_interval = 4
        self.decision_count = 0
        self.reactive_overrides = 0
        self.last_status_msg = ""
        self.initial_broadcast_done = False

    def decide(self):
        """Hybrid decision: reactive layer first, then deliberative."""
        self.decision_count += 1

        # ─── CHECK INCOMING SIGNALS ───
        signals = self.receive_signals()
        for sig in signals:
            if sig.signal_type == SIG_INFECTION_CLEARED:
                self.known_infections = {
                    i for i in self.known_infections
                    if str(i) not in sig.content
                }
                if self.target and str(self.target) in sig.content:
                    self.target = None
                    self.plan = []

        # ═══════════════════════════════════════════════════════
        #  REACTIVE LAYER 1: Engulf adjacent pathogen
        #  واکنشی ۱: بلع فوری پاتوژن مجاور
        # ═══════════════════════════════════════════════════════
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.pos[0] + dx, self.pos[1] + dy
            if self.world.get_cell(nx, ny) == INFECTED:
                self.world.clear_infection(nx, ny)
                self.pathogens_engulfed += 1
                self.current_action = f"REACTIVE: Phagocytosis at ({nx},{ny})!"
                self.status = "active"
                self.emit_signal(
                    SIG_INFECTION_CLEARED,
                    f"Pathogen at ({nx},{ny}) cleared by Macrophage!"
                )
                self.threat_active = False
                return

        # ═══════════════════════════════════════════════════════
        #  REACTIVE LAYER 2: Retreat from overwhelming infection
        #  واکنشی ۲: عقب‌نشینی از عفونت خطرناک
        # ═══════════════════════════════════════════════════════
        nearby_infections = self._count_nearby_infections(radius=2)

        if nearby_infections >= 3:
            safe_pos = self._find_safe_position()
            if safe_pos and safe_pos != self.pos:
                self.move_to(safe_pos)
                self.reactive_overrides += 1
                self.threat_active = True
                self.current_action = (
                    f"REACTIVE: Retreating! "
                    f"Too many pathogens nearby ({nearby_infections})"
                )
                self.status = "danger"
                self.plan = []  # Reactive overrides deliberative
                self.emit_signal(
                    SIG_DANGER,
                    f"Overwhelmed near {self.pos}! {nearby_infections} pathogens! Retreating!"
                )
                return
            self.threat_active = True
            self.current_action = "REACTIVE: Surrounded! Cannot retreat!"
            self.status = "danger"
            return
        else:
            self.threat_active = False

        # ═══════════════════════════════════════════════════════
        #  DELIBERATIVE LAYER: Plan migration to infection
        #  تفکری: برنامه‌ریزی مهاجرت به سمت عفونت
        # ═══════════════════════════════════════════════════════

        # Clear infection if on or adjacent to target
        if self.target:
            on_or_adjacent = (self.pos == self.target or self.is_cardinal_adjacent(self.target))
            if on_or_adjacent:
                cell = self.world.get_cell(*self.target)
                if cell == INFECTED:
                    self.world.clear_infection(*self.target)
                    self.pathogens_engulfed += 1
                    self.current_action = f"DELIBERATIVE: Cleared target at {self.target}!"
                    self.status = "active"
                    self.emit_signal(
                        SIG_INFECTION_CLEARED,
                        f"Target at {self.target} eliminated!"
                    )
                    self.target = None
                    self.plan = []
                    return
                else:
                    self.target = None
                    self.plan = []

        # Follow existing plan
        if self.plan:
            next_step = self.plan[0]
            if self.world.is_passable(next_step[0], next_step[1], avoid_infected=True):
                self.move_to(next_step)
                self.plan.pop(0)
                self.current_action = (
                    f"DELIBERATIVE: Migrating to {self.target} "
                    f"({len(self.plan)} steps left)"
                )
                self.status = "active"
                return
            else:
                self.plan = []

        # Plan new route
        infections = self.world.get_infections()
        if infections:
            target = self.world.get_nearest(self.pos, infections)
            self.target = target
            passable = {TISSUE, BLOOD_VESSEL, INFECTED}
            path = astar(self.world.grid, self.pos, target, passable=passable)

            if path:
                self.plan = path
                self.current_action = (
                    f"DELIBERATIVE: Migrating toward {target}"
                )
                self.status = "active"
            else:
                self.current_action = "DELIBERATIVE: No safe path — waiting"
                self.status = "danger"
                self.target = None
        else:
            self.current_action = "Patrolling — tissue healthy"
            self.status = "idle"

        # ═══════════════════════════════════════════════════════
        #  CYTOKINE SIGNALING: Coordinate other cells
        #  سیگنالینگ سایتوکاینی: هماهنگی سلول‌های دیگر
        # ═══════════════════════════════════════════════════════
        should_signal = (
            not self.initial_broadcast_done or
            self.decision_count % self.coordination_interval == 0
        )
        if should_signal:
            self._coordinate_cells()
            self.initial_broadcast_done = True

    # ─── Reactive Helper Methods ───

    def _count_nearby_infections(self, radius=2):
        """REACTIVE: Count infected cells within radius."""
        count = 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = self.pos[0] + dx, self.pos[1] + dy
                if self.world.get_cell(nx, ny) == INFECTED:
                    count += 1
        return count

    def _find_safe_position(self):
        """REACTIVE: Find safest adjacent cell (fewest nearby infections)."""
        best_pos = None
        min_danger = float('inf')

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.pos[0] + dx, self.pos[1] + dy
            if self.world.is_passable(nx, ny, avoid_infected=True):
                danger = 0
                for fdx in range(-2, 3):
                    for fdy in range(-2, 3):
                        if self.world.get_cell(nx + fdx, ny + fdy) == INFECTED:
                            weight = max(1, 3 - abs(fdx) - abs(fdy))
                            danger += weight
                if danger < min_danger:
                    min_danger = danger
                    best_pos = (nx, ny)

        return best_pos

    # ─── Coordination (Cytokine Signaling) ───

    def _coordinate_cells(self):
        """Emit cytokine signals to coordinate the immune response."""
        infections = self.world.get_infections()

        # Signal Neutrophil about new infections
        for inf in infections:
            if inf not in self.known_infections:
                self.known_infections.add(inf)
                self.emit_signal(
                    SIG_RECRUIT,
                    f"Infection at {inf} — recruit to area!",
                    target="Neutrophil"
                )
                self.emit_signal(
                    SIG_COORDINATE,
                    f"New pathogen detected at {inf}"
                )

        # Signal T-Cell about clusters
        cluster = self.world.get_largest_cluster(infections)
        if cluster and len(cluster) >= 2:
            cluster_center = self.world.get_nearest(self.pos, cluster)
            self.emit_signal(
                SIG_TARGET_ASSIGN,
                f"Attack cluster at {cluster_center} ({len(cluster)} cells)",
                target="T-Cell"
            )

        # Update known infections
        current_set = set(infections)
        self.known_infections = self.known_infections & current_set

        # Periodic status
        status = f"Infections: {len(infections)} | Pos: {self.pos}"
        if status != self.last_status_msg:
            self.emit_signal(SIG_STATUS, status)
            self.last_status_msg = status
