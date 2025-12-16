import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
import pygame
import math

# =========================================
#         THE FUZZY LOGIC ENGINE
# =========================================

class FuzzySystemBoid:
    def __init__(self, config):
        self.config = config

        # ==== Setup Variables ====
        self.__setup_variables()
        # ==== Setup Membership Functions ====
        self.__setup_membership_functions()
        # ==== Setup Rules ====
        self.__setup_rules()
        # ==== Setup Inference System ====
        self.__setup_inference_system()

    def __setup_variables(self):
        pass

    def __setup_membership_functions(self):
        pass

    def __setup_rules(self):
        pass

    def __setup_inference_system(self):
        # ==== Inference System ====

        rules = []

        self.boidz_controller = ctrl.ControlSystem(rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    def get_system(self):
        return self.boidz_sys

    def calculate_fuzzy(self, current_entity, boids: list, predators: list):
        """
        Senses the environment, calculates the variables that will be inputs for the fuzzy system.

        :param current_entity: The Boid instance currently being updated.
        :type current_entity: Boid
        :param boids: List of all Boid entities.
        :type boids: list
        :param predators: List of all Predator entities.
        :type predators: list
        """
        pass

    def compute(self):
        """
        :returns: A vector to be applied to the Boid's velocity, or None on error.
        :rtype: pygame.math.Vector2 | None
        """
        return pygame.Vector2(0, 0)

    def get_output_variables(self) -> list[str]:
        """
        Returns a list of all defined output variable names (Consequent labels).
        """
        if not hasattr(self, 'boidz_controller'):
            return []

        return [consequent.label for consequent in self.boidz_controller.consequents]

    def get_input_variables(self) -> list[str]:
        """
        Returns a list of all defined input variable names (Antecedent labels).
        """

        if not hasattr(self, 'boidz_controller'):
            return []

        return [antecedent.label for antecedent in self.boidz_controller.antecedents]

class FuzzySystemPredator:
    def __init__(self, config):
        self.config = config

        # ==== Setup Variables ====
        self.__setup_variables()
        # ==== Setup Membership Functions ====
        self.__setup_membership_functions()
        # ==== Setup Rules ====
        self.__setup_rules()
        # ==== Setup Inference System ====
        self.__setup_inference_system()

    def __setup_variables(self):
        pass

    def __setup_membership_functions(self):
        pass

    def __setup_rules(self):
        pass

    def __setup_inference_system(self):
        # ==== Inference System ====
        rules = []
        self.boidz_controller = ctrl.ControlSystem(rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    def get_system(self):
        return self.boidz_sys

    def calculate_fuzzy(self, current_entity, boids: list):
        """
        Senses the environment to find the closest prey within the hunting
        range. Calculates the **variables** to set the fuzzy inputs.

        :param current_entity: The Predator instance currently being updated.
        :type current_entity: Predator
        :param boids: List of all Boid entities (prey).
        :type boids: list
        """
        pass

    def compute(self, current_entity):
        """
        :returns: A vector to be applied to the Predator velocity, or None on error.
        :rtype: pygame.math.Vector2 | None
        """
        return pygame.Vector2(0, 0)

    def get_output_variables(self) -> list[str]:
        """
        Returns a list of all defined output variable names (Consequent labels).
        """
        if not hasattr(self, 'boidz_controller'):
            return []

        return [consequent.label for consequent in self.boidz_controller.consequents]

    def get_input_variables(self) -> list[str]:
        """
        Returns a list of all defined input variable names (Antecedent labels).
        """

        if not hasattr(self, 'boidz_controller'):
            return []

        return [antecedent.label for antecedent in self.boidz_controller.antecedents]