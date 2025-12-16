from __future__ import annotations

import pygame
import pygame.gfxdraw
import math
from src.utils.generalboid import GeneralBoid

# =========================================
#               PREDATOR CLASS
# =========================================

class Predator(GeneralBoid):
    """
    Represents the predator entity in the simulation, designed to hunt Boids.

    The predator's behavior is focused on finding the closest Boid within
    its hunting range and applying a steering force to intercept it. Like
    the Boid, it can switch between traditional hunting logic and a
    Fuzzy Logic system for decision-making.

    Inherits from: :py:class:`GeneralBoid`

    :param position: The initial (x, y) coordinate of the predator.
    :type position: tuple[int, int]
    :param fuzzy_system: An instance of the Predator's fuzzy logic controller, if enabled.
    :type fuzzy_system: FuzzySystemPredator
    :param config: The simulation configuration object.
    :type config: object
    """
    def __init__(self, position, fuzzy_system, config):
        super().__init__(position, config, boid_type='predator')

        self.config = config
        self.fuzzy_system = fuzzy_system
        self.closest_prey_vector = pygame.math.Vector2(0, 0)

        self.is_selected = False

        # Tunable parameters
        self.predator_speed = self.config.boids.PREDATOR_SPEED
        self.hunting_range_squared = self.VISUAL_RANGE * self.VISUAL_RANGE
        self.max_force = 0.5
        self.turn_factor = 0.2

    def hunt(self, boids: list):
        """
        The standard hunting algorithm (arithmetic steering).

        It iterates through all Boids (prey) to find the closest one within
        the hunting range, then calculates and applies a steering force to
        move towards that closest prey. The force is clamped by `self.max_force`.

        :param boids: List of all Boid entities (prey).
        :type boids: list
        """

        closest_prey = None
        min_distance_squared = float('inf')
        self.closest_prey_vector = pygame.math.Vector2(0, 0)

        for boid in boids:
            dx = self.position.x - boid.position.x
            dy = self.position.y - boid.position.y
            distance_squared = dx * dx + dy * dy

            # Find the closest boid (prey)
            if distance_squared < min_distance_squared and distance_squared < self.hunting_range_squared:
                min_distance_squared = distance_squared
                closest_prey = boid

            # Steer towards the closest boid
            if closest_prey:
                # Vector pointing from predator to prey
                desired_velocity = closest_prey.position - self.position

                if desired_velocity.length_squared() > 0:
                    desired_velocity = desired_velocity.normalize() * self.predator_speed
                else:
                    desired_velocity = pygame.math.Vector2(0, 0)

                # Normalize and scale to max speed, then steer
                steering_force = desired_velocity - self.velocity

                # If the force is too strong, clamp it to max_force
                if steering_force.length_squared() > self.max_force * self.max_force:
                    steering_force.scale_to_length(self.max_force)

                # Limit and apply the steering force
                self.velocity += steering_force

    def hunt_fuzzy(self, boids: list):
        """
        The hunting algorithm using the PredatorFuzzySystem.

        It delegates the sensing, logic calculation, and force generation
        entirely to the external fuzzy system.

        :param boids: List of all Boid entities (prey).
        :type boids: list
        """
        # 1. Sense the environment and set fuzzy inputs
        self.fuzzy_system.calculate_fuzzy(current_entity=self, boids=boids)

        # 2. Compute outputs and get the steering vector
        # The compute method applies the speed_factor and turning_factor
        # to generate the final vector.
        steering_force = self.fuzzy_system.compute(current_entity=self)

        # 3. Apply the force to the predator's velocity
        self.velocity += steering_force


    def update(self, boids: list, enable_fuzzy: bool):
        """
        Performs one simulation step for the Predator.

        1. Calls either :py:meth:`hunt_fuzzy` or :py:meth:`hunt` based on `enable_fuzzy`.
        2. Enforces screen edge avoidance.
        3. Enforces speed limits.
        4. Updates the predator's position.

        :param boids: List of all Boid entities.
        :type boids: list
        :param enable_fuzzy: Flag to enable the fuzzy logic system for this update.
        :type enable_fuzzy: bool
        """
        if enable_fuzzy:
            self.hunt_fuzzy(boids)
        else:
            self.hunt(boids)

        # Enforce avoidance in screen edges
        self.avoid_screen_edges(turn_factor=self.turn_factor)
        # Enforce min and max speeds
        self.enforce_speed_limit()
        # Update boid's position
        self.position.x += self.velocity.x
        self.position.y += self.velocity.y

    def draw(self, screen):
        """
        Renders the predator as a large triangle on the screen.

        The color is the default predator color, which is overridden by
        the selection color if :py:attr:`is_selected` is True.

        :param screen: The Pygame display surface to draw onto.
        :type screen: pygame.Surface
        """
        angle = math.atan2(self.velocity.y, self.velocity.x)

        # Calculate triangle vertices based on heading angle
        p1 = self.position + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.config.boids.BOID_SIZE
        p2 = self.position + pygame.math.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * (self.config.boids.BOID_SIZE/1.5)
        p3 = self.position + pygame.math.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * (self.config.boids.BOID_SIZE/1.5)

        c = self.config.colors.PREDATOR_COLOR

        if self.is_selected:
            c = self.selection_color

        pygame.gfxdraw.filled_polygon(screen, [p1, p2, p3], c)
        pygame.gfxdraw.aapolygon(screen, [p1, p2, p3], c) # Anti-aliased outline
