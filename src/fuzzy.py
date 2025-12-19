import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pygame
import math
import warnings
import matplotlib
# Força o matplotlib a não bloquear o Pygame
matplotlib.use('Agg') # 'Agg' é para renderizar sem abrir janela, ou 'TkAgg' para janelas separadas
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

class FuzzySystemBoid:
    def __init__(self, config):
        self.config = config
        self.perception_radius = getattr(config, 'perception_radius', 50)
        self.max_speed = getattr(config, 'max_speed', 5)
        
        self.last_entity = None
        self.last_boids = []
        self.enable_graphics = False

        self.__setup_variables()
        self.__setup_membership_functions()
        self.__setup_rules()
        self.__setup_inference_system()

    def __setup_variables(self):
        # Universos aumentados ligeiramente para evitar erros de limites [0, 51] etc.
        self.Distancia = ctrl.Antecedent(np.arange(0, 61, 1), 'Distancia')
        self.Densidade = ctrl.Antecedent(np.arange(0, 101, 1), 'Densidade')
        self.Velocidade = ctrl.Antecedent(np.arange(0, 61, 1), 'Velocidade')

        self.Forca_Separacao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Separacao')
        self.Forca_Coesao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Coesao')
        self.Forca_Alinhamento = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Alinhamento')

    def __setup_membership_functions(self):
        self.Distancia['muito_perto'] = fuzz.trimf(self.Distancia.universe, [0, 0, 15])
        self.Distancia['media'] = fuzz.trimf(self.Distancia.universe, [10, 25, 40])
        self.Distancia['longe'] = fuzz.trimf(self.Distancia.universe, [30, 60, 60])

        self.Densidade['baixa'] = fuzz.trapmf(self.Densidade.universe, [0, 0, 5, 15])
        self.Densidade['media'] = fuzz.trapmf(self.Densidade.universe, [10, 20, 30, 40])
        self.Densidade['alta'] = fuzz.trapmf(self.Densidade.universe, [35, 50, 100, 100])

        self.Velocidade['baixa'] = fuzz.trimf(self.Velocidade.universe, [0, 0, 15])
        self.Velocidade['media'] = fuzz.trimf(self.Velocidade.universe, [10, 25, 40])
        self.Velocidade['alta'] = fuzz.trimf(self.Velocidade.universe, [35, 60, 60])

        for c in [self.Forca_Separacao, self.Forca_Coesao, self.Forca_Alinhamento]:
            c['fraca'] = fuzz.trimf(c.universe, [0, 0, 4])
            c['media'] = fuzz.trimf(c.universe, [3, 5, 7])
            c['forte'] = fuzz.trimf(c.universe, [6, 10, 10])
            c['muito_forte'] = fuzz.trimf(c.universe, [8, 10, 10])

    def __setup_rules(self):
        self.rules = [
            ctrl.Rule(self.Distancia['muito_perto'], self.Forca_Separacao['muito_forte']),
            ctrl.Rule(self.Distancia['media'], self.Forca_Separacao['media']),
            ctrl.Rule(self.Distancia['longe'], self.Forca_Separacao['fraca']),
            ctrl.Rule(self.Densidade['baixa'], self.Forca_Coesao['forte']),
            ctrl.Rule(self.Densidade['media'], self.Forca_Coesao['media']),
            ctrl.Rule(self.Densidade['alta'], self.Forca_Coesao['fraca']),
            ctrl.Rule(self.Velocidade['baixa'], self.Forca_Alinhamento['fraca']),
            ctrl.Rule(self.Velocidade['media'], self.Forca_Alinhamento['media']),
            ctrl.Rule(self.Velocidade['alta'], self.Forca_Alinhamento['forte']),
        ]

    def __setup_inference_system(self):
        self.boidz_controller = ctrl.ControlSystem(self.rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    # -------------------------------------------------------------------------
    # CORREÇÃO 1: Adicionámos predators=None para não crashar com o motor
    # CORREÇÃO 2: Movemos o teletransporte (screen wrap) para aqui dentro
    # -------------------------------------------------------------------------
    def calculate_fuzzy(self, current_entity, boids: list, predators=None):
        self.last_entity = current_entity
        self.last_boids = boids if boids else []
        
        # --- HACK DE TELETRANSPORTE (Permitido pois altera o estado do boid atual) ---
        # Como não podemos mexer no engine, garantimos que eles não fogem aqui.
        try:
            w, h = pygame.display.get_surface().get_size()
            if current_entity.position.x > w: current_entity.position.x = 0
            elif current_entity.position.x < 0: current_entity.position.x = w
            if current_entity.position.y > h: current_entity.position.y = 0
            elif current_entity.position.y < 0: current_entity.position.y = h
        except:
            pass # Previne erro se o display ainda não estiver iniciado
        # -----------------------------------------------------------------------------

        neighbors = [b for b in self.last_boids if b is not current_entity and current_entity.position.distance_to(b.position) < self.perception_radius]

        avg_dist = 60 
        density = 0
        avg_speed_diff = 0.0

        if neighbors:
            distances = [current_entity.position.distance_to(b.position) for b in neighbors]
            avg_dist = float(np.mean(distances))
            density = len(neighbors)
            speed_diffs = [abs(current_entity.velocity.length() - b.velocity.length()) for b in neighbors]
            avg_speed_diff = float(np.mean(speed_diffs))

        self.boidz_sys.input['Distancia'] = np.clip(avg_dist, 0, 60)
        self.boidz_sys.input['Densidade'] = np.clip(density, 0, 100)
        self.boidz_sys.input['Velocidade'] = np.clip(avg_speed_diff, 0, 60)

        try:
            self.boidz_sys.compute()
        except Exception as e:
            print(f"Erro no calculo Fuzzy Boid: {e}")

    def compute(self):
        if self.last_entity is None:
            return pygame.Vector2(0, 0)

        try:
            sep = self.boidz_sys.output.get('Forca_Separacao', 0)
            coh = self.boidz_sys.output.get('Forca_Coesao', 0)
            ali = self.boidz_sys.output.get('Forca_Alinhamento', 0)

            v_sep = self._separation_vector(self.last_entity, self.last_boids) * sep
            v_coh = self._cohesion_vector(self.last_entity, self.last_boids) * coh
            v_ali = self._alignment_vector(self.last_entity, self.last_boids) * ali

            return v_sep + v_coh + v_ali
        except:
            return pygame.Vector2(0,0)

    # -------------------------------------------------------------------------
    # CORREÇÃO 3: Vetor de Separação corrigido (sem divisão por distância)
    # -------------------------------------------------------------------------
    def _separation_vector(self, entity, boids):
        steer = pygame.Vector2(0, 0)
        count = 0
        for b in boids:
            if b is entity: continue
            d = entity.position.distance_to(b.position)
            if 0 < d < self.perception_radius:
                diff = (entity.position - b.position)
                diff.normalize_ip() # Apenas direção! A magnitude vem do Fuzzy (sep).
                steer += diff
                count += 1
        return steer / count if count > 0 else steer

    def _cohesion_vector(self, entity, boids):
        center = pygame.Vector2(0, 0)
        count = 0
        for b in boids:
            if b is entity: continue
            if entity.position.distance_to(b.position) < self.perception_radius:
                center += b.position
                count += 1
        if count > 0:
            center /= count
            desired = center - entity.position
            if desired.length() > 0:
                return desired.normalize()
        return pygame.Vector2(0, 0)

    def _alignment_vector(self, entity, boids):
        avg_vel = pygame.Vector2(0, 0)
        count = 0
        for b in boids:
            if b is entity: continue
            if entity.position.distance_to(b.position) < self.perception_radius:
                avg_vel += b.velocity
                count += 1
        if count > 0:
            avg_vel /= count
            if avg_vel.length() > 0:
                return avg_vel.normalize()
        return pygame.Vector2(0, 0)

    def show_fuzzy_graphs(self):
        if not self.enable_graphics:
            return
        self.Distancia.view(sim=self.boidz_sys)
        plt.show()

    # -------------------------------------------------------------------------
    # CORREÇÃO 4: Métodos obrigatórios para a GUI (tinham sido removidos)
    # -------------------------------------------------------------------------
    def get_system(self): 
        return self.boidz_sys

    def get_output_variables(self): 
        return [c.label for c in self.boidz_controller.consequents]

    def get_input_variables(self): 
        return [a.label for a in self.boidz_controller.antecedents]




class FuzzySystemPredator:
    def __init__(self, config):
        self.config = config
        self.max_speed = getattr(config, 'max_speed', 6)
        self.last_entity = None
        self.last_boids = []

        self.__setup_variables()
        self.__setup_membership_functions()
        self.__setup_rules()
        self.__setup_inference_system()

    def __setup_variables(self):
        # Entradas
        self.distancia = ctrl.Antecedent(np.arange(0, 502, 1), 'distancia')
        self.alinhamento = ctrl.Antecedent(np.arange(-180, 182, 1), 'alinhamento')

        # Saídas
        self.magnitude = ctrl.Consequent(np.arange(0, 11, 0.1), 'magnitude')
        self.correcao_direcao = ctrl.Consequent(np.arange(-90, 92, 1), 'correcao_direcao')

    def __setup_membership_functions(self):
        # Distância
        self.distancia['muito_perto'] = fuzz.trimf(self.distancia.universe, [0, 0, 100])
        self.distancia['longe'] = fuzz.trimf(self.distancia.universe, [80, 500, 501])

        # Alinhamento
        self.alinhamento['esquerda'] = fuzz.trimf(self.alinhamento.universe, [-180, -90, 0])
        self.alinhamento['centro'] = fuzz.trimf(self.alinhamento.universe, [-20, 0, 20])
        self.alinhamento['direita'] = fuzz.trimf(self.alinhamento.universe, [0, 90, 180])

        # Saídas
        self.magnitude['lenta'] = fuzz.trimf(self.magnitude.universe, [0, 2, 5])
        self.magnitude['rapida'] = fuzz.trimf(self.magnitude.universe, [4, 10, 10])

        self.correcao_direcao['forte_esq'] = fuzz.trimf(self.correcao_direcao.universe, [-90, -90, -30])
        self.correcao_direcao['nenhuma'] = fuzz.trimf(self.correcao_direcao.universe, [-15, 0, 15])
        self.correcao_direcao['forte_dir'] = fuzz.trimf(self.correcao_direcao.universe, [30, 90, 90])

    def __setup_rules(self):
        self.rules = [
            ctrl.Rule(self.distancia['muito_perto'], self.magnitude['rapida']),
            ctrl.Rule(self.distancia['longe'], self.magnitude['lenta']),
            ctrl.Rule(self.alinhamento['esquerda'], self.correcao_direcao['forte_esq']),
            ctrl.Rule(self.alinhamento['centro'], self.correcao_direcao['nenhuma']),
            ctrl.Rule(self.alinhamento['direita'], self.correcao_direcao['forte_dir']),
        ]

    def __setup_inference_system(self):
        self.boidz_controller = ctrl.ControlSystem(self.rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    def calculate_fuzzy(self, current_entity, boids: list):
        self.last_entity = current_entity
        self.last_boids = boids if boids else []

        # --- HACK DE TELETRANSPORTE DO PREDADOR ---
        # Mantém o predador dentro do ecrã para ele não perder os boids
        try:
            w, h = pygame.display.get_surface().get_size()
            if current_entity.position.x > w: current_entity.position.x = 0
            elif current_entity.position.x < 0: current_entity.position.x = w
            if current_entity.position.y > h: current_entity.position.y = 0
            elif current_entity.position.y < 0: current_entity.position.y = h
        except:
            pass
        # ------------------------------------------

        if not self.last_boids:
            return

        closest = min(self.last_boids, key=lambda b: current_entity.position.distance_to(b.position))
        dist = current_entity.position.distance_to(closest.position)

        dir_to_prey = closest.position - current_entity.position
        if dir_to_prey.length() == 0:
            angle_diff = 0
        else:
            target_angle = math.degrees(math.atan2(dir_to_prey.y, dir_to_prey.x))
            current_angle = math.degrees(current_entity.angle)
            angle_diff = (target_angle - current_angle + 180) % 360 - 180

        self.boidz_sys.input['distancia'] = np.clip(dist, 0, 501)
        self.boidz_sys.input['alinhamento'] = np.clip(angle_diff, -180, 181)

        try:
            self.boidz_sys.compute()
        except:
            pass

    # AQUI ESTAVA O ERRO: Esta função tem de aceitar 'current_entity' explicitamente
    def compute(self, current_entity=None):
        # Atualiza a entidade se ela for passada pelo predator.py
        if current_entity:
            self.last_entity = current_entity
            
        if self.last_entity is None:
            return pygame.Vector2(0, 0)

        try:
            outputs = getattr(self.boidz_sys, 'output', {})
            mag = outputs.get('magnitude', 3)
            corr = outputs.get('correcao_direcao', 0)

            new_angle = self.last_entity.angle + math.radians(corr)
            desired_vel = pygame.Vector2(math.cos(new_angle), math.sin(new_angle)) * mag
            
            return desired_vel - self.last_entity.velocity
        except:
             return pygame.Vector2(0,0)

    # Funções auxiliares para a GUI não crashar ao clicar no predador
    def get_system(self): 
        return self.boidz_sys
    
    def get_output_variables(self): 
        return [c.label for c in self.boidz_controller.consequents]
    
    def get_input_variables(self): 
        return [a.label for a in self.boidz_controller.antecedents]