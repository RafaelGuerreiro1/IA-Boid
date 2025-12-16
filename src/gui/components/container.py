import pygame
from pygame_gui.elements import UIPanel

class Container:
    """
    Serves as the wrapper and positional anchor for the components housed
    within the SlidingWindow.

    It manages the calculated layout metrics (padding, dimensions) and
    synchronizes the absolute screen position of its internal Pygame GUI
    elements (UIPanel) and custom Pygame native graphics (title) with
    the current position of the sliding window.
    """
    def __init__(self, manager, window_width, window_height):
        """
        Initializes the container, sets up layout metrics, pre-renders the
        custom title, and creates the main Pygame_GUI UIPanel.

        :param manager: The UIManager instance responsible for the UI.
        :type manager: pygame_gui.UIManager
        :param window_width: The width of the external sliding window.
        :type window_width: int
        :param window_height: The height of the external sliding window.
        :type window_height: int
        """
        # Layout metrics
        self.padding_x = 20
        self.padding_y = 50
        self.width = window_width
        self.height = window_height

        self.manager = manager

        # We keep a logical Rect for position calculation
        self.rect = pygame.Rect(-self.width, 0, self.width, self.height)

        # --- 1. Custom Title Setup (PYGAME NATIVE) ---
        font = pygame.font.SysFont("Tahoma", 58)
        self.text_surface = font.render('pyBoidz', True, (200, 200, 200)) # Store the rendered surface

        # Calculate the text's intended relative position (margin/padding) once
        self.text_relative_x = self.width // 2 - (self.text_surface.get_width() // 2)
        self.text_relative_y = self.padding_y # Fixed vertical offset from the top

        # Pygame_GUI Panel Setup
        UI_TOP_OFFSET = 100

        self.panel_start_offset_x = self.padding_x
        self.panel_start_offset_y = UI_TOP_OFFSET

        self.panel = UIPanel(
            relative_rect=pygame.Rect(self.padding_x, UI_TOP_OFFSET,
                                      self.width - (self.padding_x * 2),
                                      self.height - UI_TOP_OFFSET - self.padding_y),
            starting_height=1,
            visible=True,
            manager=manager,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0},
            object_id='#config_side_panel'
        )

        # Initial position of the panel relative to the window's top-left
        self.rel_x = 0
        self.rel_y = 0

    def update_position(self, window_x, window_y):
        """
        Updates the container's absolute screen position based on the
        SlidingWindow's movement.

        This method is critical for synchronization: it updates the
        internal tracking Rect and explicitly calls set_position() on the
        Pygame_GUI panel to move it with the sliding animation.

        :param window_x: The absolute x-coordinate of the SlidingWindow's top-left corner.
        :type window_x: int
        :param window_y: The absolute y-coordinate of the SlidingWindow's top-left corner.
        :type window_y: int
        """
        # Calculate new absolute position for the overall container's top-left
        self.rect.topleft = (window_x, window_y)

        # The panel must be repositioned relative to the screen (absolute coordinates)
        new_panel_x = window_x + self.panel_start_offset_x
        new_panel_y = window_y + self.panel_start_offset_y

        self.panel.set_position((new_panel_x, new_panel_y))

        self.panel.show()


    def draw_custom_title(self, screen):
        """
        Draws the pre-rendered 'pyBoidz' text title onto the screen.

        The position is calculated based on the container's current global
        position (:py:attr:`rect`) plus the initial relative padding/centering.

        :param screen: The main Pygame display surface.
        :type screen: pygame.Surface
        """
        # Calculate the text's final GLOBAL position
        global_text_x = self.rect.x + self.text_relative_x
        global_text_y = self.rect.y + self.text_relative_y

        # Blit the text to the calculated global position
        screen.blit(self.text_surface, (global_text_x, global_text_y))

    def get_ui_container(self):
        """
        Returns the Pygame_GUI UIPanel instance.

        This is used by child GUI classes (like Config_GUI) to attach their
        elements, ensuring they inherit the panel's movement.

        :returns: The internal UIPanel object.
        :rtype: pygame_gui.elements.UIPanel
        """
        return self.panel