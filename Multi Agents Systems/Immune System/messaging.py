"""
Chemical Signaling System — Inter-Agent Communication
سامانه سیگنالینگ شیمیایی — ارتباط بین سلول‌های ایمنی

In biology, immune cells communicate via cytokines (chemical messengers).
This module simulates that communication through a CytokineBus.
"""

import time
from collections import deque


class CytokineSignal:
    """Represents a chemical signal (cytokine) between immune cells."""

    def __init__(self, sender, signal_type, content, target=None):
        self.sender = sender          # Name of sending cell
        self.signal_type = signal_type  # Type: PATHOGEN_FOUND, etc.
        self.content = content          # Human-readable description
        self.target = target            # Target cell name, or None for broadcast
        self.timestamp = time.time()

    @property
    def is_broadcast(self):
        return self.target is None

    def __repr__(self):
        tgt = f" -> {self.target}" if self.target else " [Broadcast]"
        return f"[{self.sender}]{tgt}: {self.content}"


class CytokineBus:
    """
    Central cytokine signaling bus for inter-cell communication.
    Like the biological cytokine network, signals can be:
      - Paracrine: targeted to specific cells
      - Endocrine: broadcast to all cells
    """

    def __init__(self, max_log=150):
        self.log = []
        self.queues = {}
        self.max_log = max_log

    def register(self, cell_name):
        """Register an immune cell with the signaling bus."""
        if cell_name not in self.queues:
            self.queues[cell_name] = deque()

    def emit(self, signal):
        """
        Emit a cytokine signal through the bus.
        If target is set → paracrine (targeted delivery).
        If target is None → endocrine (broadcast to all).
        """
        self.log.append(signal)
        if len(self.log) > self.max_log:
            self.log = self.log[-self.max_log:]

        if signal.target:
            if signal.target in self.queues:
                self.queues[signal.target].append(signal)
        else:
            for name, queue in self.queues.items():
                if name != signal.sender:
                    queue.append(signal)

    def receive(self, cell_name):
        """Get and clear all pending signals for a cell."""
        if cell_name not in self.queues:
            return []
        signals = list(self.queues[cell_name])
        self.queues[cell_name].clear()
        return signals

    def get_recent(self, n=30):
        """Get the n most recent signals for display."""
        return self.log[-n:]

    def clear(self):
        """Clear all signals and queues."""
        self.log.clear()
        for q in self.queues.values():
            q.clear()


# ─── Signal Type Constants (Cytokine Types) ───
SIG_PATHOGEN_FOUND = "PATHOGEN_FOUND"          # New pathogen detected
SIG_INFECTION_CLEARED = "INFECTION_CLEARED"      # Infection eliminated
SIG_INFECTION_SPREAD = "INFECTION_SPREAD"        # Infection spreading
SIG_RECRUIT = "RECRUIT"                          # Recruit cells to area
SIG_COORDINATE = "COORDINATE"                    # Coordinate attack
SIG_DANGER = "DANGER"                            # Too close to infection
SIG_STATUS = "STATUS"                            # Status update
SIG_TARGET_ASSIGN = "TARGET_ASSIGN"              # Assign target to another cell
