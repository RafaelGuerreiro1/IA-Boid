from __future__ import annotations

import pygame
import pygame.gfxdraw
import random
import math
from src.utils.entities.predator import Predator
from src.utils.generalboid import GeneralBoid


# =========================================
#               BOID CLASS
# =========================================

class Boid(GeneralBoid):
    """
    Represents a single autonomous agent (Boid) in the simulation.

    This class handles the calculation and application of forces based on
    flocking rules (Separation, Alignment, Cohesion), specialized group
    behaviors (Leader Tracking, Scout Bias), and defensive behaviors
    (Predator Evasion). The Boid can operate using traditional arithmetic
    steering forces or via a custom Fuzzy Logic system.

    Inherits from: :py:class:`GeneralBoid`

    :param position: The initial (x, y) coordinate of the boid.
    :type position: tuple[int, int]
    :param config: The simulation configuration object.
    :type config: object
    :param is_leader: Flag to designate this boid as the flock leader.
    :type is_leader: bool
    :param scout_group: Designates a bias group: 1 (right), 2 (left), or None.
    :type scout_group: int | None
    :param fuzzy_system: An instance of the Boid's fuzzy logic controller, if enabled.
    :type fuzzy_system: FuzzySystemBoid | None
    """
    def __init__(self, position, config, is_leader=False, scout_group=None, fuzzy_system=None):
        super().__init__(position, config, boid_type='boid')
        assert scout_group == 1 or scout_group == 2 or scout_group is None

        self.config = config

        # Fuzzy System
        self.fuzzy_system = fuzzy_system

        # Static Parameters
        self.is_leader = is_leader
        self.leader_boid = None

        self.scout_group = scout_group # Scout group must be 1 biased towards right or 2 biased towards left

        # Dynamic Parameters
        self.new_steering = None

        # Tunable parameter
        self.avoid_factor = 0.2
        self.matching_factor = 0.05
        self.centering_factor = 0.0005
        self.turn_factor = 0.2
        self.evasion_factor = 0.5

        # Required variables
        self.xpos_avg = 0
        self.ypos_avg = 0
        self.xvel_avg = 0
        self.yvel_avg = 0
        self.neighboring_boids = 0
        self.close_dx = 0
        self.close_dy = 0

    def flock_with_leader(self, boids : list[Boid], predators : list[Predator] = None, enable_fuzzy : bool = False):
        """
        Calculates and applies the primary steering forces based on neighboring entities.

        This method handles:
        1. **Leader Logic**: If the boid is the leader, it only evades predators and returns.
        2. **Leader Tracking**: If a leader is visible, followers steer toward its position and match its velocity.
        3. **Flocking (Cohesion/Alignment)**: Calculates the average position and velocity of neighbors within visual range.
        4. **Steering Application**: Applies forces from the calculated rules, either using the simple **arithmetic rules** (Separation, Cohesion, Alignment) or the output from the **Fuzzy System**.
        5. **Scout Bias**: Applies a slight velocity bias based on its `scout_group` assignment.

        :param boids: List of all boid entities in the simulation.
        :type boids: list[Boid]
        :param predators: List of all predator entities in the simulation.
        :type predators: list[Predator] | None
        :param enable_fuzzy: If True, uses the fuzzy logic system for steering; otherwise, uses arithmetic rules.
        :type enable_fuzzy: bool
        """
        # ==== Leader Logic ====
        if self.is_leader:
            # The leader does not follow other boids or the flock's center

            # Fuzzy Logic if enabled
            if enable_fuzzy:
                self.fuzzy_system.calculate_fuzzy(self, [], predators) # Empty list for boids due to no avoidance
                self.new_steering = self.fuzzy_system.compute()
                self.velocity += self.new_steering
            else:
                self.evade_predators(predators)

            return # leader doesn't apply flocking rules

        # ==== Follower Logic ====

        # Check for the leader and apply a new rule if visible
        leader_in_range = False

        # Check for Leader and apply Leader Tracking Rule
        if not self.leader_boid:
            for boid in boids:
                if boid.is_leader:
                    self.leader_boid = boid
                    break

        if self.leader_boid:
            dx_leader = self.position.x - self.leader_boid.position.x
            dy_leader = self.position.y - self.leader_boid.position.y
            squared_distance_leader = dx_leader * dx_leader + dy_leader * dy_leader

            # If leader is in visual range
            if squared_distance_leader < self.LEADER_TRACKING_RANGE_SQUARED:
                # Steer towards the leader's position
                self.velocity.x += (self.leader_boid.position.x - self.position.x) * self.centering_factor
                self.velocity.y += (self.leader_boid.position.y - self.position.y) * self.centering_factor

                self.velocity.x += (self.leader_boid.velocity.x - self.velocity.x) * self.matching_factor
                self.velocity.y += (self.leader_boid.velocity.y - self.velocity.y) * self.matching_factor

                leader_in_range = True

        # Cohesion and Alignment Logic
        for boid in boids:
            # Skip if boid is itself
            if boid is self or boid.is_leader:
                continue

            # Compute differences in x and y coordinates
            dx = self.position.x - boid.position.x
            dy = self.position.y - boid.position.y

            squared_distance = dx * dx + dy * dy

            # If boid is in visual range
            if not enable_fuzzy and squared_distance < self.PROTECTED_RANGE:
                # Calculate difference in x/y-coordinates to nearfield boid
                self.close_dx += self.position.x - boid.position.x
                self.close_dy += self.position.y - boid.position.y

            # Gather data for Cohesion/Alignment, but if fuzzy is disabled, also gather Separation data
            if squared_distance < self.VISUAL_RANGE_SQUARED:
                self.xpos_avg += boid.position.x
                self.ypos_avg += boid.position.y
                self.xvel_avg += boid.velocity.x
                self.yvel_avg += boid.velocity.y

                self.neighboring_boids += 1

        # If there were any boids in the visual range
        if self.neighboring_boids > 0 and not leader_in_range:
            # Divide accumulator variables by number of boids in visual range
            self.xpos_avg /= self.neighboring_boids
            self.ypos_avg /= self.neighboring_boids
            self.xvel_avg /= self.neighboring_boids
            self.yvel_avg /= self.neighboring_boids

            # Add the centering/matching contributions to velocity
            self.velocity.x = (self.velocity.x +
                               (self.xpos_avg - self.position.x) * self.centering_factor +
                               (self.xvel_avg - self.velocity.x) * self.matching_factor)

            self.velocity.y = (self.velocity.y +
                               (self.ypos_avg - self.position.y) * self.centering_factor +
                               (self.yvel_avg - self.velocity.y) * self.matching_factor)

        # ==== AVOIDANCE/EVASION with Fuzzy vs Standard ====

        if enable_fuzzy and self.fuzzy_system:
            # ==== Fuzzy Logic ====

            self.fuzzy_system.calculate_fuzzy(self, boids, predators) # Empty list for boids due to no avoidance
            self.new_steering = self.fuzzy_system.compute()

            # Apply the cached force
            self.velocity += self.new_steering
        else:

            # Add avoidance contribution to velocity
            self.velocity.x += (self.close_dx * self.avoid_factor)
            self.velocity.y += (self.close_dy * self.avoid_factor)

            # === Evade Predators ===
            self.evade_predators(predators)

        # ==== Bias ====

        # Bias towards right of screen
        if self.scout_group == 1:
            if self.velocity.x > 0:
                self.BIAS_VAL = min(self.MAX_BIAS, self.BIAS_VAL + self.BIAS_INCREMENT)
            else:
                self.BIAS_VAL = max(self.BIAS_INCREMENT, self.BIAS_VAL - self.BIAS_INCREMENT)
            self.velocity.x = (1 - self.BIAS_VAL) * self.velocity.x + (self.BIAS_VAL * 1)

        # Bias towards left of screen
        elif self.scout_group == 2:
            if self.velocity.x < 0:
                self.BIAS_VAL = min(self.MAX_BIAS, self.BIAS_VAL + self.BIAS_INCREMENT)
            else:
                self.BIAS_VAL = max(self.BIAS_INCREMENT, self.BIAS_VAL - self.BIAS_INCREMENT)
            self.velocity.x = self.velocity.x = (1 - self.BIAS_VAL) * self.velocity.x + (self.BIAS_VAL * -1)

    def evade_predators(self, predators: list[Predator] = None):
        """
        Calculates and applies a strong steering force away from any visible predators.

        The evasion force is inversely proportional to the distance from the predator,
        making the force stronger the closer the predator is.

        :param predators: List of predator entities to evade.
        :type predators: list[Predator] | None
        """
        if predators is None:
            return

        total_evasion_vector = pygame.math.Vector2(0, 0)

        # A tiny number to prevent division by zero or weird physics at exact overlap
        EPSILON = 0.1

        for predator in predators:
            dx = self.position.x - predator.position.x
            dy = self.position.y - predator.position.y
            squared_distance = dx * dx + dy * dy

            if self.PREDATOR_EVASION_RANGE_SQUARED > squared_distance > 0:

                # If predator is basically "inside" the prey (distance is near zero)
                if squared_distance < EPSILON:
                    # Doesn't calculate direction from the predator.
                    # Instead, flee in the direction it is already moving.
                    if self.velocity.length_squared() > 0:
                        direction = self.velocity.normalize()
                    else:
                        # If we are standing still and overlapping, pick a random escape route
                        direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()

                    # Apply maximum force constant
                    total_evasion_vector += direction * 5000
                else:
                    # Calculate the vector pointing AWAY from the predator
                    evasion_vector = pygame.math.Vector2(dx, dy)

                    # Normalize the vector to get the direction.
                    direction = evasion_vector.normalize()

                    # Calculate strength of evasion force based on inverse distance.
                    distance = math.sqrt(squared_distance)

                    # The inverse of the distance is 1/distance. Scale it up with a factor
                    # Ensure the vector points away and has a length based on proximity
                    total_evasion_vector += direction * (1 / distance)

        if total_evasion_vector.length_squared() > 0:
            # Normalize the total vector and multiply by the strong evasion_factor

            self.velocity += total_evasion_vector.normalize() * self.evasion_factor


    def reset_required_variables(self):
        """
        Resets the accumulator variables (e.g., position/velocity averages,
        neighbor count) before the start of each simulation step.
        """
        self.xpos_avg = 0
        self.ypos_avg = 0
        self.xvel_avg = 0
        self.yvel_avg = 0
        self.neighboring_boids = 0
        self.close_dx = 0
        self.close_dy = 0

    def update(self, boids : list[Boid], predators : list[Predator] = None, enable_fuzzy : bool = False):
        """
        Performs one simulation step:
        1. Resets state.
        2. Calculates and applies flocking/evasion forces.
        3. Enforces screen edges and speed limits.
        4. Updates the entity's position.

        :param boids: List of all boid entities.
        :type boids: list[Boid]
        :param predators: List of predator entities.
        :type predators: list[Predator] | None
        :param enable_fuzzy: Flag to enable the fuzzy logic system for this update.
        :type enable_fuzzy: bool
        """
        self.reset_required_variables()

        self.flock_with_leader(boids=boids, predators=predators, enable_fuzzy=enable_fuzzy)

        # Enforce avoidance in screen edges
        self.avoid_screen_edges(turn_factor=self.turn_factor)
        # Enforce min and max speeds
        self.enforce_speed_limit()

        # Update boid's position
        self.position.x += self.velocity.x
        self.position.y += self.velocity.y

    def draw(self, screen):
        """
        Renders the boid as a triangle on the screen.

        The color of the boid is determined by its role (Leader, Scout Group,
        or Normal) and is overridden by the selection color if
        :py:attr:`is_selected` is True.

        :param screen: The Pygame display surface to draw onto.
        :type screen: pygame.Surface
        """
        angle = math.atan2(self.velocity.y, self.velocity.x)

        # Calculate triangle vertices based on heading angle
        p1 = self.position + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * self.config.boids.BOID_SIZE
        p2 = self.position + pygame.math.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * (self.config.boids.BOID_SIZE/1.5)
        p3 = self.position + pygame.math.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * (self.config.boids.BOID_SIZE/1.5)

        if self.is_leader:
            c = self.config.colors.LEADER_COLOR
            base_color = self.config.colors.LEADER_COLOR
        elif self.scout_group == 1:
            c = self.config.colors.BIASED_RIGHT_COLOR
            base_color = self.config.colors.BIASED_RIGHT_COLOR
        elif self.scout_group == 2:
            c = self.config.colors.BIASED_LEFT_COLOR
            base_color = self.config.colors.BIASED_LEFT_COLOR
        else:
            c = self.config.colors.BOID_COLOR
            base_color = self.config.colors.BOID_COLOR

        if self.original_color is None:
            self.original_color = base_color

        # --- Apply Selection Color ---
        if self.is_selected:
            c = self.selection_color
        else:
            c = base_color

        pygame.gfxdraw.filled_polygon(screen, [p1, p2, p3], c)
        pygame.gfxdraw.aapolygon(screen, [p1, p2, p3], c) # Anti-aliased outline