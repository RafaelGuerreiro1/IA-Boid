import pygame
import pygame.gfxdraw
import random
import math

class GeneralBoid:
    """
    Abstract base class for all moving entities (Boids and Predators) in the
    simulation.

    This class encapsulates fundamental physics, boundary constraints, and
    common parameters like visual ranges and speed limits required for
    autonomous agents in a boid system. It provides essential methods for
    movement control and basic user interaction.

    :ivar config: A configuration object containing global simulation settings.
    :vartype config: object
    """
    def __init__(self, position, config, boid_type):
        self.config = config

        self.LEFT_MARGIN = self.config.screen.margins.MARGIN_FROM_EDGE
        self.RIGHT_MARGIN = self.config.screen.dimensions.WIDTH - self.config.screen.margins.MARGIN_FROM_EDGE
        self.TOP_MARGIN = self.config.screen.margins.MARGIN_FROM_EDGE
        self.BOTTOM_MARGIN = self.config.screen.dimensions.HEIGHT - self.config.screen.margins.MARGIN_FROM_EDGE

        self.MAX_SPEED = self.config.boids.MAX_SPEED if boid_type == 'boid' else self.config.boids.PREDATOR_SPEED
        self.MIN_SPEED = self.config.boids.MIN_SPEED
        self.MAX_FORCE = self.config.boids.MAX_FORCE
        self.VISUAL_RANGE = self.config.boids.VISUAL_RANGE
        self.PROTECTED_RANGE = self.config.boids.PROTECTED_RANGE
        self.PROTECTED_RANGE_SQUARED = self.config.boids.PROTECTED_RANGE**2
        self.BOID_SIZE = self.config.boids.BOID_SIZE
        self.VISUAL_RANGE_SQUARED = self.VISUAL_RANGE * self.VISUAL_RANGE
        self.STEERING_FORCE = 0.005
        self.LEADER_TRACKING_RANGE_SQUARED = self.VISUAL_RANGE_SQUARED
        self.PREDATOR_EVASION_RANGE_SQUARED = self.VISUAL_RANGE_SQUARED
        self.MAX_BIAS = 0.01
        self.BIAS_INCREMENT = 0.00004
        self.BIAS_VAL = 0.001

        self.HUNT_RANGE = self.config.boids.HUNT_RANGE
        self.HUNT_RANGE_SQUARED = self.config.boids.HUNT_RANGE**2

        # Selection State Variables
        self.is_selected = False
        self.original_color = None
        self.selection_color = self.config.colors.SELECTION_COLOR

        # Dynamical Parameters
        self.position = pygame.math.Vector2(position)
        self.angle = random.uniform(0, math.pi * 2)
        self.velocity = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle)) * random.uniform(2, self.MAX_SPEED)

    def avoid_screen_edges(self, turn_factor : float):
        """
        Applies a steering force to prevent the entity from leaving the
        defined screen margins.

        :param turn_factor: The magnitude of the force applied to turn the entity
                            back into the center area.
        :type turn_factor: float
        """
        # Turn if boid reached designated margin
        if self.position.x < self.LEFT_MARGIN:
            self.velocity.x += turn_factor
        if self.position.x > self.RIGHT_MARGIN:
            self.velocity.x -= turn_factor
        if self.position.y > self.BOTTOM_MARGIN:
            self.velocity.y -= turn_factor
        if self.position.y < self.TOP_MARGIN:
            self.velocity.y += turn_factor

    def enforce_speed_limit(self):
        """
        Ensures the entity's speed remains within the configured
        [MIN_SPEED, MAX_SPEED] range.

        If the speed exceeds MAX_SPEED, it is clamped. If it drops below
        MIN_SPEED, it is boosted.
        """

        speed = math.sqrt(self.velocity.x**2 + self.velocity.y**2)

        if speed < self.MIN_SPEED:
            self.velocity.x = (self.velocity.x/speed)*self.MIN_SPEED
            self.velocity.y = (self.velocity.y/speed)*self.MIN_SPEED
        if speed > self.MAX_SPEED:
            self.velocity.x = (self.velocity.x/speed)*self.MAX_SPEED
            self.velocity.y = (self.velocity.y/speed)*self.MAX_SPEED

    def is_clicked(self, click_pos: tuple[int, int]) -> bool:
        """
        Checks if a given screen coordinate (mouse click) is within the
        entity's hit radius.

        A generous hit radius (2x BOID_SIZE) is used to simplify selection.

        :param click_pos: The (x, y) coordinate of the mouse click.
        :type click_pos: tuple[int, int]
        :returns: True if the click is within the entity's bounding area, False otherwise.
        :rtype: bool
        """

        # Use a simple circular distance check for performance
        HIT_RADIUS_SQUARED = (self.config.boids.BOID_SIZE * 2) ** 2 # Define a generous hit radius

        mouse_vec = pygame.math.Vector2(click_pos)
        distance_squared = self.position.distance_squared_to(mouse_vec)

        return distance_squared < HIT_RADIUS_SQUARED