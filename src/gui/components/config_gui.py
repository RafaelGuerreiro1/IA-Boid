import os
import pygame
import pygame_gui
from pygame_gui.elements import UILabel, UIDropDownMenu, UICheckBox
import math

class Config_GUI:
    """
    Manages the user interface elements related to simulation configuration
    and feature toggles, housed within the sliding window.

    This class creates labels, a configuration file dropdown, a fuzzy logic
    checkbox, and a visual legend for the simulation entities. All UI elements
    are anchored to the provided container so they move together during the
    sliding animation.
    """
    def __init__(self, manager, container_wrapper):
        """
        Initializes the GUI components, loads available configuration files,
        and sets up the visual legend.

        :param manager: The UIManager instance responsible for processing UI events.
        :type manager: pygame_gui.UIManager
        :param container_wrapper: An instance of the custom Container class that provides the UIPanel.
        :type container_wrapper: object
        """
        self.manager = manager

        # Get the actual UI Panel from your wrapper to attach elements to
        self.ui_container = container_wrapper.get_ui_container()

        # Config Files Logic
        config_files = self.__get_config_files()

        # This ensures they move when the container moves.

        #  Title Label
        self.title_label = UILabel(
            relative_rect=pygame.Rect(0, 5, 200, 50),
            text="RPygramar & Sphincz",
            manager=self.manager,
            container=self.ui_container,
            anchors={'centerx': 'centerx', 'top': 'top'}
        )

        NEXT_Y = 50

        # Config Label
        self.config_label = UILabel(
            relative_rect=pygame.Rect(10, NEXT_Y, 100, 30),
            text="Config File:",
            manager=self.manager,
            container=self.ui_container
        )

        NEXT_Y = NEXT_Y + 30

        # Dropdown
        self.config_dropdown = UIDropDownMenu(
            options_list=config_files,
            starting_option=config_files[0],
            relative_rect=pygame.Rect(10, NEXT_Y, 150, 30),
            manager=self.manager,
            container=self.ui_container,
        )

        NEXT_Y = NEXT_Y + 50

        # Check Box
        self.config_checkbox = UICheckBox(
            text='Enable Fuzzy Logic',
            relative_rect=pygame.Rect(10, NEXT_Y, 30, 30),
            container=self.ui_container,
            manager=self.manager,
        )

        # --- Legend Definition ---
        LEGEND_START_Y = self.config_dropdown.relative_rect.bottom + 100

        self.legend_data = [
            {'color': pygame.Color('green'), 'text': 'Selected Boid', 'relative_y': LEGEND_START_Y},
            {'color': pygame.Color('red'), 'text': 'Predator', 'relative_y': LEGEND_START_Y + 30},
            {'color': pygame.Color('yellow'), 'text': 'Leader', 'relative_y': LEGEND_START_Y + 60},
            {'color': pygame.Color('lightblue'), 'text': 'Boid', 'relative_y': LEGEND_START_Y + 90},

        ]

        # Create UILabels for the legend text
        for item in self.legend_data:
            UILabel(
                relative_rect=pygame.Rect(30, item['relative_y'], 100, 30),
                text=item['text'],
                manager=self.manager,
                container=self.ui_container
            )

    def draw_symbols(self, surface):
        """
        Draws the colored triangle symbols next to the legend labels.

        The symbols are drawn directly onto the main Pygame surface using
        the absolute screen coordinates of the UI container, ensuring they
        are correctly positioned even while the sliding window is moving.

        :param surface: The main Pygame display surface.
        :type surface: pygame.Surface
        """
        # Get the absolute screen position of the UI container (the UIPanel)
        panel_abs_x, panel_abs_y = self.ui_container.get_abs_rect().topleft

        # Symbols are drawn 10 pixels from the left edge of the panel
        SYMBOL_ABS_X = panel_abs_x + 15

        for item in self.legend_data:
            # Calculate the symbol's absolute Y position
            symbol_abs_y = panel_abs_y + item['relative_y'] + 15 # +15 centers it vertically on the label

            self.__draw_triangle(
                surface,
                item['color'],
                SYMBOL_ABS_X,
                symbol_abs_y,
                size=5
            )

    @staticmethod
    def __get_config_files():
        """
        Scans the './configs' directory and returns a list of available
        JSON configuration files. Creates the directory if it doesn't exist.

        :returns: A list of configuration file names (e.g., ['default.json', 'aggressive.json']).
        :rtype: list[str]
        """
        config_dir = "./src/configs"
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except OSError:
                pass
            return ["None"]

        files = [f for f in os.listdir(config_dir) if f.endswith(".json")]
        return files if files else ["None"]

    @staticmethod
    def __draw_triangle(surface, color, center_x, center_y, size=5):
        """
        Static helper method to draw a simple, filled, forward-pointing triangle.

        :param surface: The surface to draw on.
        :type surface: pygame.Surface
        :param color: The color of the triangle.
        :type color: pygame.Color
        :param center_x: The x-coordinate of the center of the triangle.
        :type center_x: int
        :param center_y: The y-coordinate of the center of the triangle.
        :type center_y: int
        :param size: Controls the size (base and height) of the triangle.
        :type size: int
        """

        h = size * math.sqrt(3) / 2 # Height calculation for equilateral triangle

        points = [
            (center_x + size, center_y), # Tip
            (center_x - size/2, center_y - h), # Top-rear
            (center_x - size/2, center_y + h)  # Bottom-rear
        ]

        pygame.draw.polygon(surface, color, points)