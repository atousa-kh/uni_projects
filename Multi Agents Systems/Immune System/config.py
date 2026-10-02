"""
Configuration for the Immune System Simulation
تنظیمات شبیه‌سازی سیستم ایمنی بدن
"""

# ─── Grid Settings ───
GRID_COLS = 24
GRID_ROWS = 16
CELL_SIZE = 40

# ─── UI Layout ───
PANEL_WIDTH = 420
TOP_BAR_HEIGHT = 52
GRID_PIXEL_W = GRID_COLS * CELL_SIZE
GRID_PIXEL_H = GRID_ROWS * CELL_SIZE
WINDOW_WIDTH = GRID_PIXEL_W + PANEL_WIDTH
WINDOW_HEIGHT = GRID_PIXEL_H + TOP_BAR_HEIGHT

# ─── Simulation Timing ───
FPS = 60
AGENT_MOVE_INTERVAL = 550       # ms between agent decisions
INFECTION_SPREAD_INTERVAL = 12000  # ms between infection spread
NEW_WAVE_INTERVAL = 25000       # ms between new infection waves
SMOOTH_MOVE_SPEED = 260         # pixels/sec for smooth movement

# ─── World Generation ───
NUM_INITIAL_INFECTIONS = 6
NUM_ORGAN_CLUSTERS = 5          # Number of organ structure clusters
ORGAN_CLUSTER_RADIUS = (1, 3)   # Min/max radius of organ clusters
NUM_VESSEL_BRANCHES = 6         # Blood vessel branch paths
MAX_INFECTION_WAVES = 3         # Maximum new infection waves

# ─── Cell Types ───
TISSUE = 0          # Healthy tissue (passable)
ORGAN = 1           # Organ structure (impassable)
INFECTED = 2        # Infected cell (passable, has pathogen)
BLOOD_VESSEL = 3    # Blood vessel (passable, travel route)

# ─── Agent Architecture Types ───
REACTIVE = 'Reactive'
DELIBERATIVE = 'Deliberative'
HYBRID = 'Hybrid'

# ─── Colors ───
COLORS = {
    # Background & Grid
    'bg':               (18, 22, 28),
    'tissue':           (62, 40, 48),
    'tissue_light':     (72, 48, 56),
    'tissue_detail':    (55, 36, 44),
    'grid_line':        (30, 24, 30),

    # Blood vessels
    'vessel':           (110, 30, 40),
    'vessel_light':     (140, 45, 55),
    'vessel_center':    (160, 50, 60),

    # Organs
    'organ':            (95, 50, 60),
    'organ_top':        (115, 65, 75),
    'organ_detail':     (75, 38, 48),

    # Infection colors
    'infected_base':    (30, 80, 20),
    'infected_1':       (50, 180, 40),
    'infected_2':       (80, 220, 60),
    'infected_3':       (130, 255, 90),
    'infected_glow':    (40, 200, 50),
    'infected_dead':    (50, 60, 45),

    # Immune cells
    'neutrophil':       (230, 70, 80),
    'neutrophil_dark':  (160, 40, 50),
    'neutrophil_glow':  (255, 100, 110),
    'tcell':            (80, 100, 230),
    'tcell_dark':       (45, 55, 160),
    'tcell_glow':       (110, 140, 255),
    'macrophage':       (60, 200, 140),
    'macrophage_dark':  (35, 140, 95),
    'macrophage_glow':  (90, 230, 170),

    # Cytokine signals
    'cytokine':         (255, 220, 80),
    'cytokine_glow':    (255, 240, 120),

    # UI Panel
    'panel_bg':         (18, 20, 26),
    'panel_border':     (50, 45, 55),
    'panel_section':    (26, 24, 32),
    'top_bar':          (22, 20, 28),

    # Text
    'text':             (185, 180, 190),
    'text_dim':         (100, 95, 105),
    'text_bright':      (235, 230, 240),
    'text_title':       (215, 210, 225),

    # Message colors per agent
    'msg_neutrophil':   (255, 130, 140),
    'msg_tcell':        (140, 160, 255),
    'msg_macrophage':   (140, 230, 190),
    'msg_system':       (180, 180, 190),

    # Status colors
    'status_active':    (80, 220, 140),
    'status_idle':      (200, 200, 80),
    'status_danger':    (255, 90, 90),

    # Trails
    'trail_neutrophil': (230, 70, 80),
    'trail_tcell':      (80, 100, 230),
    'trail_macrophage': (60, 200, 140),

    # Health bar
    'health_good':      (80, 200, 120),
    'health_warn':      (220, 180, 50),
    'health_critical':  (220, 60, 60),
}

# ─── Agent Info ───
AGENT_INFO = {
    REACTIVE: {
        'name': 'Neutrophil',
        'persian_name': 'نوتروفیل',
        'symbol': 'N',
        'color_key': 'neutrophil',
        'start_pos': (2, 2),
        'description': 'Reactive: immediate phagocytosis reflex',
        'biography': 'First responder — engulfs nearest pathogen instantly',
    },
    DELIBERATIVE: {
        'name': 'T-Cell',
        'persian_name': 'سلول T',
        'symbol': 'T',
        'color_key': 'tcell',
        'start_pos': (GRID_COLS - 3, 2),
        'description': 'Deliberative: strategic targeting with A*',
        'biography': 'Strategic commander — plans optimal attack routes',
    },
    HYBRID: {
        'name': 'Macrophage',
        'persian_name': 'ماکروفاژ',
        'symbol': 'M',
        'color_key': 'macrophage',
        'start_pos': (GRID_COLS // 2, GRID_ROWS - 3),
        'description': 'Hybrid: reactive eating + deliberative migration + signaling',
        'biography': 'Versatile defender — eats, plans, and signals others',
    },
}

# ─── Vessel Network (main arteries as column positions) ───
VESSEL_COLS = {0, 6, 12, 18, GRID_COLS - 1}
VESSEL_ROWS = {0, 5, 10, GRID_ROWS - 1}
