WIDTH = 1000
HEIGHT = 700
FPS = 144
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

import json

class Config:
    """
    Classe para carregar e aceder às definições do sistema de forma hierárquica.

    Exemplo de acesso:
        self.config.screen.dimensions.WIDTH
        self.config.boids.MAX_SPEED
        self.config.colors.BOID_COLOR
    """

    def __init__(self, data=None):
        """
        Inicializa o objeto Config. Pode receber um dicionário (data)
        com as configurações, ou ficar vazio até ser carregado depois.
        """
        if data:
            self.load_from_dict(data)

    def load_from_dict(self, data):
        """
        Carrega recursivamente as chaves de um dicionário como atributos
        desta classe. Se o valor for outro dicionário, cria um subobjeto Config.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self, key, value)

    def __repr__(self):
        """
        Representação legível (útil para debugging).
        """
        return f"<Config {self.__dict__}>"

