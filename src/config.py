WIDTH = 1000
HEIGHT = 700
FPS = 60
TITLE = "pyBoidz"
BACKGROUND_COLOR = (78, 14, 73)

class Config:
    """
    Access example:
        self.config.screen.dimensions.WIDTH
        self.config.boids.MAX_SPEED
        self.config.colors.BOID_COLOR
    """
    def __init__(self, data):
        # Call the recursive loader
        self.load_from_dict(data)

    def load_from_dict(self, data):
        """Recursively loads attributes from a dictionary."""
        for key, value in data.items():
            if isinstance(value, dict):
                # If the value is another dictionary, create a nested object
                setattr(self, key, Config(value))
            else:
                # If it's a final value, set it as an attribute
                setattr(self, key, value)
