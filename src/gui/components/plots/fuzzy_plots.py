import pygame
import math
import numpy as np

# --- CONSTANTS (UNCHANGED) ---
NATIVE_PLOT_WIDTH = 300
NATIVE_PLOT_HEIGHT = 300
PLOT_PADDING = 10
AXIS_TICK_LENGTH = 2

COLOR_PALETTE = [
    (255, 99, 71),   # Tomato Red
    (60, 179, 113),  # Medium Sea Green
    (30, 144, 255),  # Dodger Blue
    (255, 165, 0),   # Orange
    (147, 112, 219), # Medium Purple
    (255, 215, 0),   # Gold
    (0, 191, 255),   # Deep Sky Blue
    (107, 142, 35),  # Olive Drab
]

BACKGROUND_COLOR = (0, 0, 0, 25)
AXES_COLOR = (255, 255, 255)
RESULT_COLOR = (255, 255, 255)

# Helper function (UNCHANGED)
def _fuzzy_to_pygame_coords(x, y, x_min, x_max, plot_rect):
    """Translates fuzzy (0-1) space to screen pixel coordinates."""

    draw_width = plot_rect.width - 2 * PLOT_PADDING
    draw_height = plot_rect.height - 2 * PLOT_PADDING

    scale_x = draw_width / (x_max - x_min)
    px = plot_rect.left + PLOT_PADDING + (x - x_min) * scale_x

    scale_y = draw_height / 1.0
    py = plot_rect.top + PLOT_PADDING + draw_height - (y * scale_y)

    return int(px), int(py)

def draw_fuzzy_plot_native(selected_boid):
    """
    Renders the fuzzy plots dynamically onto a Pygame Surface with 100x100 dimensions,
    centering the crisp result value label.
    """
    if not selected_boid or not selected_boid.fuzzy_system:
        return None

    sim = selected_boid.fuzzy_system.get_system()
    if not sim.output:
        return None

    output_labels = selected_boid.fuzzy_system.get_output_variables()
    num_outputs = len(output_labels)

    # --- DYNAMIC GRID CALCULATION ---
    NUM_ROWS = math.ceil(math.sqrt(num_outputs))
    NUM_COLS = math.ceil(num_outputs / NUM_ROWS)

    if NUM_COLS == 0:
        return None

    PLOT_W = NATIVE_PLOT_WIDTH / NUM_COLS
    PLOT_H = NATIVE_PLOT_HEIGHT / NUM_ROWS

    plot_surface = pygame.Surface((NATIVE_PLOT_WIDTH, NATIVE_PLOT_HEIGHT), pygame.SRCALPHA)
    plot_surface.fill(BACKGROUND_COLOR)

    # --- FONT SIZES ---
    try:
        font = pygame.font.Font(None, 12)
    except:
        font = pygame.font.SysFont(None, 12)

        # --- DYNAMIC RECT CALCULATION ---
    plot_rects = []
    for i in range(num_outputs):
        col = i % NUM_COLS
        row = i // NUM_COLS

        left = col * PLOT_W
        top = row * PLOT_H

        plot_rects.append(pygame.Rect(left, top, PLOT_W, PLOT_H))
    # -----------------------------

    # --- DYNAMIC COLOR MAPPING ---
    term_color_map = {}
    color_index = 0

    for label in output_labels:
        consequent = next((c for c in sim.ctrl.consequents if c.label == label), None)
        if consequent:
            for term_name in consequent.terms.keys():
                if term_name not in term_color_map:
                    term_color_map[term_name] = COLOR_PALETTE[color_index % len(COLOR_PALETTE)]
                    color_index += 1
    # -----------------------------

    # --- LOOP OVER ALL OUTPUTS ---
    for i, label in enumerate(output_labels):

        if i >= len(plot_rects):
            break

        consequent = next((c for c in sim.ctrl.consequents if c.label == label), None)

        if consequent:
            ax_rect = plot_rects[i]
            x_min = consequent.universe.min()
            x_max = consequent.universe.max()

            title_font = pygame.font.SysFont(None, 20)
            label_font = pygame.font.SysFont(None, 20)

            # --- 0. Draw Subplot Title ---
            title_text = title_font.render(label.replace('_', ' ').title(), True, AXES_COLOR)
            plot_surface.blit(title_text, (ax_rect.left + PLOT_PADDING - 5, ax_rect.top))

            # --- 1. Draw Axes ---
            x_axis_start = (ax_rect.left + PLOT_PADDING, ax_rect.top + ax_rect.height - PLOT_PADDING)
            x_axis_end = (ax_rect.left + ax_rect.width - PLOT_PADDING, ax_rect.top + ax_rect.height - PLOT_PADDING)
            y_axis_start = (ax_rect.left + PLOT_PADDING, ax_rect.top + ax_rect.height - PLOT_PADDING)
            y_axis_end = (ax_rect.left + PLOT_PADDING, ax_rect.top + PLOT_PADDING)

            pygame.draw.line(plot_surface, AXES_COLOR, x_axis_start, x_axis_end, 1)
            pygame.draw.line(plot_surface, AXES_COLOR, y_axis_start, y_axis_end, 1)

            # --- 1.5. Draw Axis Ticks (Labels still skipped for space) ---

            # Y-AXIS TICKS (Fixed interval: 0.25, 0.5, 0.75)
            y_ticks = np.arange(0.25, 0.76, 0.25)
            for y_val in y_ticks:
                px, py = _fuzzy_to_pygame_coords(x_min, y_val, x_min, x_max, ax_rect)

                # Draw small tick mark
                pygame.draw.line(plot_surface, AXES_COLOR, (px - AXIS_TICK_LENGTH, py), (px + AXIS_TICK_LENGTH, py), 1)

            # X-AXIS TICKS (Intervals based on the universe range)
            x_range = x_max - x_min
            x_step = x_range / 3
            x_ticks = np.arange(x_min + x_step, x_max - 0.001, x_step)

            for x_val in x_ticks:
                px, py = _fuzzy_to_pygame_coords(x_val, 0, x_min, x_max, ax_rect)

                # Draw small tick mark
                pygame.draw.line(plot_surface, AXES_COLOR, (px, py - AXIS_TICK_LENGTH), (px, py + AXIS_TICK_LENGTH), 1)

            # --- 2. Draw Membership Functions (Lines) ---
            for term_name, term in consequent.terms.items():

                color = term_color_map.get(term_name, (150, 150, 150))
                universe = consequent.universe
                mf_values = term.mf

                points = []
                for x, y in zip(universe, mf_values):
                    points.append(_fuzzy_to_pygame_coords(x, y, x_min, x_max, ax_rect))

                if len(points) > 1:
                    pygame.draw.lines(plot_surface, color, False, points, 1)

                    # --- 3. Draw Defuzzified Value (Crisp Result Line) ---
            if label in sim.output:
                crisp_value = sim.output[label]

                p_bottom = _fuzzy_to_pygame_coords(crisp_value, 0, x_min, x_max, ax_rect)
                p_top = _fuzzy_to_pygame_coords(crisp_value, 1.05, x_min, x_max, ax_rect)

                # Draw the vertical line
                pygame.draw.line(plot_surface, RESULT_COLOR, p_bottom, p_top, 1)

                # --- KEY CHANGE: Centering the label on the line ---

                # Calculate the y-coordinate for the middle of the line segment
                mid_y = (p_bottom[1] + p_top[1]) / 2

                # Draw the crisp value label
                value_text = label_font.render(f"{crisp_value:.1f}", True, RESULT_COLOR)
                text_w, text_h = value_text.get_size()

                # Position the text horizontally centered on the line (p_top[0])
                # and vertically centered at mid_y
                plot_surface.blit(value_text, (p_top[0] - text_w + 20, mid_y - text_h / 2))

    return plot_surface