import json
import random
import sys

import pygame
import pygame_gui
from src.config import *
from src.fuzzy import FuzzySystemBoid, FuzzySystemPredator
from src.gui.components.plots.fuzzy_plots import draw_fuzzy_plot_native
from src.gui.components.sliding_window import SlidingWindow
from src.utils.entities.boid import Boid
from src.utils.entities.predator import Predator


class BoidSimulation:
    """
    Main application driver class for the Boid simulation.

    This class initializes the Pygame environment, manages the simulation loop,
    handles user input (mouse clicks, key presses), updates all simulation
    entities (Boids and Predators), manages the configuration state, and
    renders the simulation elements, including the fuzzy system plots.
    """

    def __init__(self):
        """Initializes Pygame, sets up the display, UI, and loads the initial configuration."""

        self.config = None

        pygame.init()
        pygame.display.set_caption(TITLE)
        pygame_icon = pygame.image.load('./src/assets/boid_icon.png')
        pygame.display.set_icon(pygame_icon)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()

        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT), './src/gui/components/theme.json')

        # Simulation Entities
        self.boids: list[Boid] = []
        self.predators: list[Predator] = []
        self.selected_boid: Boid | None = None

        # Fuzzy Plot Cache
        self.fuzzy_plot_surface: pygame.Surface | None = None
        self.last_selected_boid_id = None  # Used to track if we need to regenerate the plot

        # Plot Update Control
        self.plot_frame_counter = 0
        self.plot_update_interval = 5

        # GUI
        self.sliding_window = SlidingWindow(self.screen, self.manager, self.config)

        # Load the initial config file
        self.load_config()

        # Pause State
        self.paused = False
        self.pause_font = pygame.font.Font(None, 72)

        self.running = True

    def run_simulation(self):
        """
        The main simulation loop.

        It handles event processing, updates the physics of all entities,
        renders the screen, updates the GUI, and manages the frame rate.
        """
        while self.running:
            time_delta = self.clock.tick(self.config.screen.general.FPS) / 1000.0

            self.screen.fill(BACKGROUND_COLOR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_click(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.sliding_window.opened = not self.sliding_window.opened

                    elif event.key == pygame.K_p:
                        self.paused = not self.paused

                if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == self.sliding_window.config_gui.config_dropdown:
                        self.load_config()

                self.manager.process_events(event)

            for boid in self.boids:
                if not self.paused:
                    boid.update(boids=self.boids, predators=self.predators, enable_fuzzy=self.sliding_window.config_gui.config_checkbox.is_checked)
                boid.draw(self.screen)

            for predator in self.predators:
                if not self.paused:
                    predator.update(boids=self.boids, enable_fuzzy=self.sliding_window.config_gui.config_checkbox.is_checked)
                predator.draw(self.screen)

            if self.sliding_window.config_gui.config_checkbox.is_checked:
                # Plot Update
                if not self.paused:
                    self._update_fuzzy_plot()

                if self.fuzzy_plot_surface:
                    # Draw the plot surface at the bottom right of the screen, adjusted for size
                    plot_x = self.config.screen.dimensions.WIDTH - self.fuzzy_plot_surface.get_width() - 10
                    plot_y = self.config.screen.dimensions.HEIGHT - self.fuzzy_plot_surface.get_height() - 10
                    self.screen.blit(self.fuzzy_plot_surface, (plot_x, plot_y))

            # Sliding Window
            self.sliding_window.update()
            self.sliding_window.draw(self.screen)

            if self.paused:
                self._draw_pause_overlay()

            # Manager
            self.manager.draw_ui(self.screen)
            self.manager.update(time_delta)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _update_fuzzy_plot(self):
        """
        Manages the generation and caching of the fuzzy logic plot.

        The plot is regenerated only when the selected entity changes or
        when the update interval (plot_update_interval) is met, ensuring
        live feedback without excessive rendering cost.
        """
        current_boid_id = id(self.selected_boid) if self.selected_boid else None

        # Flag to indicate if we NEED to regenerate the plot this frame
        should_regenerate = False

        # --- Case 1: Selection Changed/Deselected ---
        if current_boid_id != self.last_selected_boid_id:
            self.last_selected_boid_id = current_boid_id
            self.plot_frame_counter = 0  # Force immediate update on selection change
            if not self.selected_boid:
                self.fuzzy_plot_surface = None
                return
            should_regenerate = True

        if self.selected_boid and not should_regenerate:
            self.plot_frame_counter += 1
            if self.plot_frame_counter % self.plot_update_interval == 0:
                should_regenerate = True

        # If we shouldn't regenerate this frame, exit early
        if not should_regenerate:
            return

        # --- Regenerate Plot (Only happens if should_regenerate is True) ---

        self.fuzzy_plot_surface = draw_fuzzy_plot_native(self.selected_boid)

        if should_regenerate:
            self.plot_frame_counter = 1

    def _handle_mouse_click(self, click_pos):
        """
        Handles mouse clicks for entity selection and deselection.

        It checks all Boids and Predators against the click position,
        selecting the first hit entity and deselecting any previously
        selected entity.

        :param click_pos: The (x, y) coordinates of the mouse click.
        :type click_pos: tuple[int, int]
        """

        # Deselect any currently selected boid first
        if self.selected_boid:
            self.selected_boid.is_selected = False
            self.selected_boid = None

        all_entities = self.boids + self.predators

        for entity in all_entities:
            if entity.is_clicked(click_pos):
                entity.is_selected = True
                self.selected_boid = entity
                break

    def _draw_pause_overlay(self):
        """Draws a translucent overlay and 'PAUSED' text when the simulation is paused."""

        # Create a translucent surface
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 10))  # Black with 150/255 opacity
        self.screen.blit(overlay, (0, 0))

        # Render PAUSED text
        pause_text = self.pause_font.render("PAUSED", True, (255, 255, 255))  # White text
        text_rect = pause_text.get_rect(center=(self.config.screen.dimensions.WIDTH // 2,
                                                self.config.screen.dimensions.HEIGHT // 2))

        # Define opacity
        TEXT_ALPHA = 25

        # Set text alpha
        pause_text.set_alpha(TEXT_ALPHA)

        # Draw text to screen
        self.screen.blit(pause_text, text_rect)

    def apply_config(self):
        """
        Applies the settings from the loaded configuration object
        to the Pygame environment (e.g., screen dimensions, title)
        and resets the simulation state.
        """

        # Apply Screen and Display Settings
        WIDTH = self.config.screen.dimensions.WIDTH
        HEIGHT = self.config.screen.dimensions.HEIGHT
        TITLE = self.config.screen.general.TITLE

        pygame.display.set_caption(TITLE)

        # Reset the display surface if dimensions have changed
        current_width, current_height = self.screen.get_size()
        if current_width != WIDTH or current_height != HEIGHT:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.reset_simulation()

    def reset_simulation(self):
        """
        Clears existing Boids and Predators and instantiates new entities
        (including leaders, followers, and predators) based on the current
        configuration's counts and parameters.
        """
        if not self.config: return

        # Get values from the loaded config object
        NUM_BOIDS = self.config.boids.NUM_BOIDS
        NUM_PREDATORS = self.config.boids.NUM_PREDATORS
        WIDTH = self.config.screen.dimensions.WIDTH
        HEIGHT = self.config.screen.dimensions.HEIGHT

        # ==== Boids ====
        self.boids = []

        # Create Leader
        leader = Boid(position=(random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                      is_leader=True, fuzzy_system=FuzzySystemBoid(config=self.config), config=self.config)
        self.boids.append(leader)

        # Create Followers
        for _ in range(NUM_BOIDS - 1):
            self.boids.append(Boid(position=(random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                                   is_leader=False,
                                   scout_group=random.choice([None, 1, 2]),
                                   fuzzy_system=FuzzySystemBoid(config=self.config), config=self.config))

        # ==== Predator ====
        self.predators = []

        for _ in range(NUM_PREDATORS):
            self.predators.append(
                Predator(position=(random.randint(0, self.config.screen.dimensions.WIDTH), random.randint(0, self.config.screen.dimensions.HEIGHT)), fuzzy_system=FuzzySystemPredator(config=self.config), config=self.config))

    def load_config(self):
        """
        Reads the configuration data from the file selected in the GUI dropdown.

        It parses the JSON, creates the configuration object, and calls
        :py:meth:`apply_config` to update the simulation.
        """

        # Get the selected file name from the dropdown
        config_file = self.sliding_window.config_gui.config_dropdown.selected_option
        if isinstance(config_file, tuple):
            config_file = config_file[0]  # Handle case where selection is (filename, index)

        try:
            with open(f'./src/configs/{config_file}', 'r') as file:
                data = json.load(file)

            self.config = Config(data=data)  # Create the new configuration object
            self.apply_config()  # Apply and reset the simulation
            self.sliding_window.set_config(self.config)

        except FileNotFoundError:
            print(f"Error: Config file not found at ./configs/{config_file}")
        except Exception as e:
            print(f"Error loading or applying configuration: {e}")
