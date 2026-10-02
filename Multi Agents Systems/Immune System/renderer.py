"""
Biological Renderer — Organic visual display for the immune system simulation
رندرر زیستی — نمایش بصری ارگانیک شبیه‌سازی سیستم ایمنی

Draws tissue, blood vessels, infections, immune cells,
and the cytokine signaling panel.
"""

import pygame
import math
from config import (
    GRID_COLS, GRID_ROWS, CELL_SIZE, PANEL_WIDTH, TOP_BAR_HEIGHT,
    GRID_PIXEL_W, GRID_PIXEL_H, WINDOW_WIDTH, WINDOW_HEIGHT,
    TISSUE, ORGAN, INFECTED, BLOOD_VESSEL,
    REACTIVE, DELIBERATIVE, HYBRID, AGENT_INFO, COLORS,
)


class Renderer:
    """Handles all visual rendering with biological/organic style."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(
            "Immune System Simulation | شبیه‌سازی سیستم ایمنی بدن"
        )
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 13)
        self.font_tiny = pygame.font.SysFont("Arial", 11)
        self.font_symbol = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)

        # Animation
        self.anim_tick = 0

        # Pre-render tissue background for performance
        self._tissue_surface = None

    def draw(self, world, agents, cytokine_bus, elapsed_time, paused=False):
        """Main draw method."""
        self.anim_tick += 1

        self.screen.fill(COLORS['bg'])

        # Top bar
        self._draw_top_bar(world, elapsed_time, paused)

        # Grid and world
        self._draw_grid(world)

        # Agent trails
        for agent in agents:
            self._draw_trail(agent)

        # Cytokine signal particles (visual effect)
        self._draw_cytokine_particles(agents, cytokine_bus)

        # Agents
        for agent in agents:
            self._draw_agent(agent)

        # Panel
        self._draw_panel(world, agents, cytokine_bus, elapsed_time)

        pygame.display.flip()

    # ─── Top Bar ───

    def _draw_top_bar(self, world, elapsed_time, paused):
        pygame.draw.rect(self.screen, COLORS['top_bar'],
                         (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(self.screen, COLORS['panel_border'],
                         (0, TOP_BAR_HEIGHT - 1), (WINDOW_WIDTH, TOP_BAR_HEIGHT - 1))

        # Title
        title = self.font_large.render(
            "Immune System Simulation", True, COLORS['text_bright']
        )
        self.screen.blit(title, (15, 14))

        # Stats
        stats = world.stats
        secs = int(elapsed_time / 1000)
        mins = secs // 60
        secs = secs % 60

        # Health bar
        health = stats['health']
        bar_x, bar_y = 370, 16
        bar_w, bar_h = 100, 18
        pygame.draw.rect(self.screen, (40, 35, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        health_color = (
            COLORS['health_good'] if health > 70 else
            COLORS['health_warn'] if health > 40 else
            COLORS['health_critical']
        )
        fill_w = int(bar_w * health / 100)
        if fill_w > 0:
            pygame.draw.rect(self.screen, health_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=3)
        pygame.draw.rect(self.screen, COLORS['panel_border'],
                         (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=3)
        health_text = self.font_tiny.render(f"{health:.0f}%", True, (255, 255, 255))
        hr = health_text.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
        self.screen.blit(health_text, hr)

        label = self.font_tiny.render("Health:", True, COLORS['text_dim'])
        self.screen.blit(label, (bar_x - 45, bar_y + 2))

        info_items = [
            (f"Time: {mins:02d}:{secs:02d}", COLORS['text']),
            (f"Infections: {stats['infections_remaining']}", COLORS['infected_2']),
            (f"Cleared: {stats['infections_cleared']}", COLORS['status_active']),
            (f"Wave: {stats['wave_count']}", COLORS['text_dim']),
        ]

        x = 490
        for text, color in info_items:
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (x, 18))
            x += surf.get_width() + 18

        if paused:
            pause_text = self.font_medium.render("PAUSED", True, COLORS['infected_2'])
            self.screen.blit(pause_text, (WINDOW_WIDTH - 90, 18))

        if world.all_clear:
            done = self.font_medium.render("BODY CLEAR!", True, COLORS['status_active'])
            self.screen.blit(done, (WINDOW_WIDTH - 180, 18))

    # ─── Grid ───

    def _draw_grid(self, world):
        tick = self.anim_tick
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = col * CELL_SIZE
                y = row * CELL_SIZE + TOP_BAR_HEIGHT
                cell = world.grid[row][col]
                tex = world.texture[row][col] if hasattr(world, 'texture') else 0

                if cell == ORGAN:
                    self._draw_organ(x, y, tex)
                elif cell == BLOOD_VESSEL:
                    self._draw_vessel(x, y, tex)
                elif cell == INFECTED:
                    self._draw_tissue(x, y, tex)
                    self._draw_infection(x, y, tick)
                else:
                    self._draw_tissue(x, y, tex)

    def _draw_tissue(self, x, y, tex=0):
        """Draw healthy tissue cell with organic texture."""
        offsets = [0, 3, 6, 9]
        base = COLORS['tissue']
        r = min(255, base[0] + offsets[tex % 4])
        g = min(255, base[1] + offsets[tex % 4])
        b = min(255, base[2] + offsets[tex % 4])
        pygame.draw.rect(self.screen, (r, g, b),
                         (x, y, CELL_SIZE, CELL_SIZE))
        # Subtle cell membrane lines
        if CELL_SIZE >= 30:
            pygame.draw.rect(self.screen, COLORS['tissue_detail'],
                             (x, y, CELL_SIZE, CELL_SIZE), width=1)

    def _draw_vessel(self, x, y, tex=0):
        """Draw blood vessel cell."""
        s = CELL_SIZE
        # Vessel background
        pygame.draw.rect(self.screen, COLORS['vessel'], (x, y, s, s))
        # Lighter center (blood flow)
        margin = s // 4
        pygame.draw.rect(self.screen, COLORS['vessel_light'],
                         (x + margin, y + margin, s - margin * 2, s - margin * 2))
        # Center highlight
        margin2 = s // 3
        pygame.draw.rect(self.screen, COLORS['vessel_center'],
                         (x + margin2, y + margin2, s - margin2 * 2, s - margin2 * 2))

    def _draw_organ(self, x, y, tex=0):
        """Draw organ structure cell with 3D effect."""
        s = CELL_SIZE
        margin = 2

        # Shadow
        pygame.draw.rect(self.screen, COLORS['organ_detail'],
                         (x + margin + 2, y + margin + 2, s - margin * 2, s - margin * 2))
        # Body
        pygame.draw.rect(self.screen, COLORS['organ'],
                         (x + margin, y + margin, s - margin * 2, s - margin * 2))
        # Top highlight
        pygame.draw.rect(self.screen, COLORS['organ_top'],
                         (x + margin, y + margin, s - margin * 2, s // 3))
        # Cell detail
        if s >= 28:
            detail = self.font_tiny.render("o", True, COLORS['organ_detail'])
            self.screen.blit(detail, (x + s // 2 - 3, y + s // 2 - 3))

    def _draw_infection(self, x, y, tick):
        """Draw animated infection (pathogen colony)."""
        cx = x + CELL_SIZE // 2
        cy = y + CELL_SIZE // 2
        s = CELL_SIZE

        # Base glow
        glow_surf = pygame.Surface((s, s), pygame.SRCALPHA)
        glow_alpha = 50 + int(20 * math.sin(tick * 0.12))
        pygame.draw.circle(glow_surf, (*COLORS['infected_glow'], glow_alpha),
                           (s // 2, s // 2), s // 2)
        self.screen.blit(glow_surf, (x, y))

        # Pulsing bacteria colony
        phase = tick * 0.13
        r1 = int(s * 0.32 + 3 * math.sin(phase))
        r2 = int(s * 0.22 + 2 * math.sin(phase + 1.2))
        r3 = int(s * 0.12 + 2 * math.sin(phase + 2.4))

        # Outer layer
        oy1 = int(2 * math.sin(phase * 0.8))
        pygame.draw.circle(self.screen, COLORS['infected_1'],
                           (cx, cy + oy1), r1)
        # Middle layer
        oy2 = int(-2 * math.sin(phase))
        pygame.draw.circle(self.screen, COLORS['infected_2'],
                           (cx, cy + oy2 - 2), r2)
        # Core
        pygame.draw.circle(self.screen, COLORS['infected_3'],
                           (cx, cy - 3), r3)

        # Small bacteria dots
        for i in range(3):
            angle = phase * 0.5 + i * 2.1
            bx = cx + int((r1 - 3) * math.cos(angle))
            by = cy + int((r1 - 3) * math.sin(angle))
            pygame.draw.circle(self.screen, COLORS['infected_2'], (bx, by), 2)

    # ─── Trails ───

    def _draw_trail(self, agent):
        trail = agent.trail
        if len(trail) < 2:
            return

        for i, pos in enumerate(trail[:-1]):
            alpha = int(15 + 35 * (i / len(trail)))
            px = pos[0] * CELL_SIZE + CELL_SIZE // 2
            py = pos[1] * CELL_SIZE + CELL_SIZE // 2 + TOP_BAR_HEIGHT
            radius = 3
            trail_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (*agent.trail_color, alpha)
            pygame.draw.circle(trail_surf, color, (radius, radius), radius)
            self.screen.blit(trail_surf, (px - radius, py - radius))

    # ─── Cytokine Particles ───

    def _draw_cytokine_particles(self, agents, cytokine_bus):
        """Draw visual cytokine signal particles between agents."""
        tick = self.anim_tick
        signals = cytokine_bus.get_recent(n=5)

        for sig in signals[-3:]:
            # Find sender and target pixel positions
            sender_pos = None
            target_pos = None
            for agent in agents:
                if agent.name == sig.sender:
                    sender_pos = (int(agent.pixel_pos[0]), int(agent.pixel_pos[1]))
                if sig.target and agent.name == sig.target:
                    target_pos = (int(agent.pixel_pos[0]), int(agent.pixel_pos[1]))

            if sender_pos and target_pos:
                # Draw moving particle along the line
                age = tick % 60 / 60.0  # Animation phase
                px = sender_pos[0] + (target_pos[0] - sender_pos[0]) * age
                py = sender_pos[1] + (target_pos[1] - sender_pos[1]) * age

                # Glowing particle
                particle_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                alpha = int(180 * (1 - abs(age - 0.5) * 2))
                pygame.draw.circle(particle_surf, (*COLORS['cytokine'], alpha), (8, 8), 6)
                pygame.draw.circle(particle_surf, (*COLORS['cytokine_glow'], alpha), (8, 8), 3)
                self.screen.blit(particle_surf, (int(px) - 8, int(py) - 8))

    # ─── Agents ───

    def _draw_agent(self, agent):
        """Draw an immune cell with glow, body, and label."""
        px, py = int(agent.pixel_pos[0]), int(agent.pixel_pos[1])
        radius = 15

        # Glow effect
        glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        glow_alpha = 35 + int(15 * math.sin(self.anim_tick * 0.08))
        pygame.draw.circle(glow_surf, (*agent.color_glow, glow_alpha),
                           (radius * 2, radius * 2), radius * 2)
        self.screen.blit(glow_surf, (px - radius * 2, py - radius * 2))

        # Danger aura for macrophage
        if agent.agent_type == HYBRID and hasattr(agent, 'threat_active') and agent.threat_active:
            danger_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            danger_alpha = 40 + int(25 * math.sin(self.anim_tick * 0.25))
            pygame.draw.circle(danger_surf, (255, 50, 50, danger_alpha),
                               (radius * 2, radius * 2), radius * 2)
            self.screen.blit(danger_surf, (px - radius * 2, py - radius * 2))

        # Cell body — slightly irregular (organic look)
        pygame.draw.circle(self.screen, agent.color_dark, (px, py), radius + 2)
        pygame.draw.circle(self.screen, agent.color, (px, py), radius)

        # Inner organelle detail
        inner_r = radius // 2
        inner_color = tuple(min(255, c + 40) for c in agent.color)
        pygame.draw.circle(self.screen, inner_color, (px - 2, py - 2), inner_r)

        # Agent symbol
        symbol_surf = self.font_symbol.render(agent.symbol, True, (255, 255, 255))
        symbol_rect = symbol_surf.get_rect(center=(px, py + 1))
        self.screen.blit(symbol_surf, symbol_rect)

        # Label above
        info = AGENT_INFO[agent.agent_type]
        label = f"{info['name']} ({info['persian_name']})"
        label_surf = self.font_tiny.render(label, True, agent.color)
        label_rect = label_surf.get_rect(center=(px, py - radius - 10))
        self.screen.blit(label_surf, label_rect)

    # ─── Message Panel ───

    def _draw_panel(self, world, agents, cytokine_bus, elapsed_time):
        panel_x = GRID_PIXEL_W
        panel_w = PANEL_WIDTH
        panel_h = WINDOW_HEIGHT

        # Background
        pygame.draw.rect(self.screen, COLORS['panel_bg'],
                         (panel_x, 0, panel_w, panel_h))
        pygame.draw.line(self.screen, COLORS['panel_border'],
                         (panel_x, 0), (panel_x, panel_h), 2)

        y = 10

        # ─── Section 1: Cell Status Cards ───
        header = self.font_medium.render("IMMUNE CELL STATUS", True, COLORS['text_bright'])
        self.screen.blit(header, (panel_x + 15, y))
        y += 26

        for agent in agents:
            card_rect = pygame.Rect(panel_x + 8, y, panel_w - 16, 74)
            pygame.draw.rect(self.screen, COLORS['panel_section'], card_rect, border_radius=4)
            pygame.draw.rect(self.screen, agent.color, card_rect, width=2, border_radius=4)

            info = AGENT_INFO[agent.agent_type]
            name_surf = self.font_medium.render(
                f"{info['name']} ({info['persian_name']})", True, agent.color
            )
            self.screen.blit(name_surf, (panel_x + 16, y + 5))

            # Architecture type
            type_surf = self.font_tiny.render(
                f"Architecture: {agent.agent_type}", True, COLORS['text_dim']
            )
            self.screen.blit(type_surf, (panel_x + 16, y + 22))

            # Current action
            action = agent.current_action
            if len(action) > 45:
                action = action[:45] + "..."
            action_color = COLORS['status_active'] if agent.status == 'active' else (
                COLORS['status_idle'] if agent.status == 'idle' else COLORS['status_danger']
            )
            action_surf = self.font_tiny.render(action, True, action_color)
            self.screen.blit(action_surf, (panel_x + 16, y + 37))

            # Stats
            stat_text = f"Engulfed: {agent.pathogens_engulfed} | Pos: {agent.pos}"
            stat_surf = self.font_tiny.render(stat_text, True, COLORS['text_dim'])
            self.screen.blit(stat_surf, (panel_x + 16, y + 52))

            # Reactive overrides indicator for macrophage
            if agent.agent_type == HYBRID:
                override_text = f"Reactive overrides: {agent.reactive_overrides}"
                ov_surf = self.font_tiny.render(override_text, True, COLORS['text_dim'])
                self.screen.blit(ov_surf, (panel_x + 16, y + 63))

            y += 82

        # ─── Section 2: Architecture Legend ───
        y += 4
        pygame.draw.line(self.screen, COLORS['panel_border'],
                         (panel_x + 10, y), (panel_x + panel_w - 10, y))
        y += 8

        legend_title = self.font_medium.render("ARCHITECTURES", True, COLORS['text_bright'])
        self.screen.blit(legend_title, (panel_x + 15, y))
        y += 22

        legends = [
            (COLORS['neutrophil'], "Reactive: Chemotaxis reflex (no plan memory)"),
            (COLORS['tcell'], "Deliberative: A* strategy + plan following"),
            (COLORS['macrophage'], "Hybrid: Reactive evasion + deliberative + signals"),
        ]
        for color, text in legends:
            pygame.draw.circle(self.screen, color, (panel_x + 22, y + 6), 5)
            leg_surf = self.font_tiny.render(text, True, COLORS['text'])
            self.screen.blit(leg_surf, (panel_x + 34, y))
            y += 17

        # ─── Section 3: Cytokine Signal Log ───
        y += 8
        pygame.draw.line(self.screen, COLORS['panel_border'],
                         (panel_x + 10, y), (panel_x + panel_w - 10, y))
        y += 8

        msg_header = self.font_medium.render(
            "CYTOKINE SIGNALS", True, COLORS['text_bright']
        )
        self.screen.blit(msg_header, (panel_x + 15, y))
        y += 22

        signals = cytokine_bus.get_recent(n=30)
        max_y = WINDOW_HEIGHT - 38
        msg_y = max_y

        for sig in reversed(signals):
            if msg_y < y:
                break

            # Color based on sender
            if 'Neutrophil' in sig.sender:
                color = COLORS['msg_neutrophil']
            elif 'T-Cell' in sig.sender:
                color = COLORS['msg_tcell']
            elif 'Macrophage' in sig.sender:
                color = COLORS['msg_macrophage']
            else:
                color = COLORS['msg_system']

            target_str = f"->{sig.target[:5]}" if sig.target else "[ALL]"
            text = f"[{sig.sender[:4]}]{target_str}: {sig.content}"
            if len(text) > 52:
                text = text[:52] + ".."

            sig_surf = self.font_tiny.render(text, True, color)
            self.screen.blit(sig_surf, (panel_x + 12, msg_y))
            msg_y -= 16

        # ─── Bottom: Controls ───
        bottom_y = WINDOW_HEIGHT - 28
        pygame.draw.line(self.screen, COLORS['panel_border'],
                         (panel_x + 10, bottom_y - 5),
                         (panel_x + panel_w - 10, bottom_y - 5))
        controls = self.font_tiny.render(
            "[SPACE] Pause  [R] Restart  [+/-] Speed  [ESC] Quit",
            True, COLORS['text_dim']
        )
        self.screen.blit(controls, (panel_x + 12, bottom_y))

    # ─── Completion Screen ───

    def draw_completion(self, world, elapsed_time):
        overlay = pygame.Surface((GRID_PIXEL_W, GRID_PIXEL_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, TOP_BAR_HEIGHT))

        cx = GRID_PIXEL_W // 2
        cy = GRID_PIXEL_H // 2 + TOP_BAR_HEIGHT

        banner = pygame.Rect(cx - 220, cy - 60, 440, 120)
        pygame.draw.rect(self.screen, (15, 50, 30), banner, border_radius=12)
        pygame.draw.rect(self.screen, COLORS['status_active'], banner, width=3, border_radius=12)

        title = self.font_title.render("INFECTION CLEARED!", True, COLORS['status_active'])
        self.screen.blit(title, title.get_rect(center=(cx, cy - 25)))

        secs = int(elapsed_time / 1000)
        stats = world.stats
        summary = self.font_medium.render(
            f"Pathogens cleared: {stats['infections_cleared']} | "
            f"Waves survived: {stats['wave_count']} | "
            f"Time: {secs}s",
            True, COLORS['text']
        )
        self.screen.blit(summary, summary.get_rect(center=(cx, cy + 10)))

        restart = self.font_small.render("Press R to restart", True, COLORS['text_dim'])
        self.screen.blit(restart, restart.get_rect(center=(cx, cy + 40)))

    def tick(self, fps):
        return self.clock.tick(fps)
