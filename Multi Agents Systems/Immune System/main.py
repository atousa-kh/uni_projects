"""
Immune System Simulation — Main Entry Point
نقطه ورود اصلی شبیه‌سازی سیستم ایمنی بدن

The body is under attack! Three immune cells with different architectures cooperate:
  🔴 Neutrophil  (Reactive)     — Chemotaxis reflex, no plan memory
  🔵 T-Cell      (Deliberative) — Strategic A* targeting of infection clusters
  🟢 Macrophage  (Hybrid)       — Reactive evasion + deliberative migration + cytokine signaling

Controls:
  SPACE  - Pause/Resume
  R      - Restart simulation
  +/-    - Adjust simulation speed
  ESC    - Quit
"""

import pygame
import sys

from config import (
    FPS, AGENT_MOVE_INTERVAL, INFECTION_SPREAD_INTERVAL,
    NEW_WAVE_INTERVAL, MAX_INFECTION_WAVES,
)
from world import TissueWorld
from agents import NeutrophilAgent, TCellAgent, MacrophageAgent
from messaging import CytokineBus, SIG_INFECTION_SPREAD
from renderer import Renderer


class Simulation:
    """Main simulation controller."""

    def __init__(self):
        self.renderer = Renderer()
        self.reset()

    def reset(self):
        """Initialize or reset the simulation."""
        self.world = TissueWorld()
        self.cytokine_bus = CytokineBus()

        # Create immune cells
        self.neutrophil = NeutrophilAgent(self.world, self.cytokine_bus)
        self.tcell = TCellAgent(self.world, self.cytokine_bus)
        self.macrophage = MacrophageAgent(self.world, self.cytokine_bus)
        self.agents = [self.neutrophil, self.tcell, self.macrophage]

        # Timing
        self.start_time = pygame.time.get_ticks()
        self.last_agent_update = pygame.time.get_ticks()
        self.last_infection_spread = pygame.time.get_ticks()
        self.last_wave = pygame.time.get_ticks()
        self.move_interval = AGENT_MOVE_INTERVAL
        self.spread_interval = INFECTION_SPREAD_INTERVAL
        self.wave_interval = NEW_WAVE_INTERVAL

        # State
        self.paused = False
        self.completed = False
        self.completion_time = 0

    def run(self):
        """Main simulation loop."""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self._handle_key(event.key)

            dt = self.renderer.tick(FPS)

            if not self.paused and not self.completed:
                self._update(dt)

            elapsed = pygame.time.get_ticks() - self.start_time
            self.renderer.draw(
                self.world, self.agents, self.cytokine_bus,
                elapsed, self.paused
            )

            if self.completed:
                self.renderer.draw_completion(self.world, self.completion_time)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_key(self, key):
        if key == pygame.K_ESCAPE:
            return False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.reset()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.move_interval = max(150, self.move_interval - 80)
            self.spread_interval = max(4000, self.spread_interval - 1000)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.move_interval = min(2000, self.move_interval + 80)
            self.spread_interval = min(30000, self.spread_interval + 1500)
        return True

    def _update(self, dt):
        now = pygame.time.get_ticks()

        # ─── Agent Decision Making ───
        if now - self.last_agent_update >= self.move_interval:
            for agent in self.agents:
                agent.decide()
            self.last_agent_update = now

        # ─── Infection Spreading ───
        if now - self.last_infection_spread >= self.spread_interval:
            new_infections = self.world.spread_infection()
            if new_infections:
                for pos in new_infections:
                    self.macrophage.known_infections.add(pos)
                self.macrophage.emit_signal(
                    SIG_INFECTION_SPREAD,
                    f"Infection spreading! New at {new_infections}"
                )
            self.last_infection_spread = now

        # ─── New Infection Waves ───
        if (now - self.last_wave >= self.wave_interval and
                self.world.wave_count < MAX_INFECTION_WAVES and
                not self.world.all_clear):
            wave = self.world.spawn_wave()
            if wave:
                self.macrophage.emit_signal(
                    SIG_INFECTION_SPREAD,
                    f"New infection wave! Pathogens at {wave}"
                )
                for pos in wave:
                    self.macrophage.known_infections.add(pos)
            self.last_wave = now

        # ─── Smooth Agent Movement ───
        for agent in self.agents:
            agent.update_pixel_pos(dt)

        # ─── Check Completion ───
        if self.world.all_clear and not self.completed:
            self.completed = True
            self.completion_time = now - self.start_time


def main():
    print("=" * 60)
    print("  Immune System Simulation")
    print("  شبیه‌سازی سیستم ایمنی بدن")
    print("=" * 60)
    print()
    print("  Immune Cells:")
    print("    🔴 Neutrophil  (Reactive)     — Chemotaxis reflex")
    print("    🔵 T-Cell      (Deliberative) — Strategic A* targeting")
    print("    🟢 Macrophage  (Hybrid)       — Reactive + Deliberative + Signals")
    print()
    print("  Controls:")
    print("    SPACE  - Pause/Resume")
    print("    R      - Restart")
    print("    +/-    - Adjust speed")
    print("    ESC    - Quit")
    print("=" * 60)

    sim = Simulation()
    sim.run()


if __name__ == "__main__":
    main()
