import pygame_gui
import pygame
from src.config import *
from src.gui.components.container import Container
from src.gui.components.config_gui import Config_GUI


class SlidingWindow:
    """
    Manages the animated user interface panel that slides in and out from the
    side of the screen (typically the left).

    It handles the animation logic, rendering of a semi-transparent background,
    hosting of the configuration GUI components, and displaying a hint when closed.
    """
    def __init__(self, screen, manager, config):
        """
        Initializes the sliding window, starting it in a hidden state off-screen.

        :param screen: The main Pygame display surface.
        :type screen: pygame.Surface
        :param manager: The UIManager instance for handling UI components.
        :type manager: pygame_gui.UIManager
        :param config: The current simulation configuration object.
        :type config: object
        """
        self.screen = screen
        self.manager = manager
        self.config = config

        # Window Dimensions
        self.width = WIDTH // 2.5
        self.height = HEIGHT

        # Initialize a small, readable font
        self.font = pygame.font.Font(None, 24)

        # The visual background rect (starts off-screen)
        self.sliding_window = pygame.Rect(-self.width, 0, self.width, self.height)

        # Alpha surface for transparency
        self.alpha_surface = pygame.Surface(self.sliding_window.size, pygame.SRCALPHA)

        # State variables
        self.opened = False  # Target state: True to open, False to close
        self.is_moving = False # Actual state: True while the animation is running
        self.SLIDE_SPEED = 15

        # Components
        self.container = Container(self.manager, self.width, self.height)
        # Config GUI
        self.config_gui = Config_GUI(self.manager, self.container)

    def slide_in(self):
        """
        Calculates the movement necessary to animate the window sliding into the screen (opening).
        """
        # Target X position is 0 (fully visible)
        if self.sliding_window.x < 0:

            self.sliding_window.x += self.SLIDE_SPEED

            if self.sliding_window.x >= 0:
                self.sliding_window.x = 0
                self.is_moving = False
        else:
            self.is_moving = False # Stop moving once x is 0

    def slide_out(self):
        """
        Calculates the movement necessary to animate the window sliding off the screen (closing).
        """
        # Target X position is the negative width of the window itself
        target_x = -self.sliding_window.width
        if self.sliding_window.x > target_x:
            self.sliding_window.x -= self.SLIDE_SPEED
            # Clamp position if it overshoots
            if self.sliding_window.x <= target_x:
                self.sliding_window.x = target_x
                self.is_moving = False
        else:
            self.is_moving = False # Stop moving once fully hidden

    def update_component_position(self):
        """
        (Note: This method is not used in the provided update logic, as container.update_position
        handles the positioning.)
        """
        container = self.container
        window_rect = self.sliding_window

        new_x = window_rect.x + container.padding_x

        new_y = window_rect.y + container.padding_y

        container.rect.topleft = (new_x, new_y)

    def set_config(self, config):
        """
        Updates the internal configuration object.

        :param config: The new configuration object.
        :type config: object
        """
        self.config = config

    def update(self):
        """
        Runs the animation logic for sliding the window based on the `opened` state.
        Updates the position of the internal UI container to match the window's movement.
        """
        # Animation Logic
        window_width = self.sliding_window.width

        if self.opened and self.sliding_window.x < 0:
            self.is_moving = True
            self.slide_in()
        elif not self.opened and self.sliding_window.x > -window_width:
            self.is_moving = True
            self.slide_out()
        else:
            self.is_moving = False

        self.container.update_position(self.sliding_window.x, self.sliding_window.y)

    def draw(self, surface):
        """
        Renders the sliding window and its contents onto the main surface.

        If the window is open or moving:
        1. Draws the semi-transparent background using the alpha surface.
        2. Draws the custom title and the UI component symbols (legend).

        If the window is closed and stationary:
        1. Renders and displays the "Press H to open settings" hint text.

        :param surface: The Pygame display surface to draw onto.
        :type surface: pygame.Surface
        """
        # Draw if the window is visible OR moving
        if self.is_moving or self.sliding_window.x > -self.width:

            # Draw semi-transparent background
            # self.alpha_surface.fill((0,0,0,0)) # Clear previous frame

            # Create a local rect at (0,0) for drawing onto the alpha surface
            draw_rect = pygame.Rect(0, 0, self.width, self.height)
            pygame.draw.rect(self.alpha_surface, self.config.colors.SLIDING_WINDOW_COLOR, draw_rect)

            # Blit onto main screen
            surface.blit(self.alpha_surface, self.sliding_window.topleft)

            self.container.draw_custom_title(surface)

            self.config_gui.draw_symbols(surface)
        if not self.opened and not self.is_moving:
            hint_text = 'Press "H" to open settings'

            # Render the text
            text_surface = self.font.render(hint_text, True, self.config.colors.HINT_COLOR)

            # Calculate position for left bottom corner (with a small margin)
            margin = 15
            x = margin
            y = surface.get_height() - text_surface.get_height() - margin

            surface.blit(text_surface, (x, y))