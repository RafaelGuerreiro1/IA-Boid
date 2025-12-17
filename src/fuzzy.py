import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pygame
import math
import warnings

# Ignora avisos de runtime do skfuzzy (comum quando as regras não se sobrepõem)
warnings.filterwarnings("ignore")

class FuzzySystemBoid:
    def __init__(self, config):
        self.config = config
        self.perception_radius = getattr(config, 'perception_radius', 50)
        self.max_speed = getattr(config, 'max_speed', 5)
        
        # Memória para os inputs (evita erros de argumentos no compute)
        self.last_entity = None
        self.last_boids = []
        self.last_predators = []
        
        self.__setup_variables()
        self.__setup_membership_functions()
        self.__setup_rules()
        self.__setup_inference_system()

    def __setup_variables(self):
        # Antecedentes (Entradas)
        self.Distancia = ctrl.Antecedent(np.arange(0, 52, 1), 'Distancia')
        self.Densidade = ctrl.Antecedent(np.arange(0, 102, 1), 'Densidade')
        self.Velocidade = ctrl.Antecedent(np.arange(0, 56, 0.1), 'Velocidade')
        self.Distancia_Predador = ctrl.Antecedent(np.arange(0, 102, 1), 'Distancia_Predador')

        # Consequentes (Saídas)
        self.Forca_Separacao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Separacao')
        self.Forca_Coesao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Coesao')
        self.Forca_Alinhamento = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Alinhamento')
        self.Forca_Evasao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Evasao')

    def __setup_membership_functions(self):
        # Membros da Distância
        self.Distancia['muito_perto'] = fuzz.trimf(self.Distancia.universe, [0, 0, 15])
        self.Distancia['media'] = fuzz.trimf(self.Distancia.universe, [10, 25, 40])
        self.Distancia['longe'] = fuzz.trimf(self.Distancia.universe, [30, 50, 51])

        # Membros da Densidade
        self.Densidade['baixa'] = fuzz.trapmf(self.Densidade.universe, [0, 0, 5, 15])
        self.Densidade['media'] = fuzz.trapmf(self.Densidade.universe, [10, 20, 30, 40])
        self.Densidade['alta'] = fuzz.trapmf(self.Densidade.universe, [35, 50, 101, 101])

        # Membros da Velocidade
        self.Velocidade['baixa'] = fuzz.trimf(self.Velocidade.universe, [0, 0, 15])
        self.Velocidade['media'] = fuzz.trimf(self.Velocidade.universe, [10, 25, 40])
        self.Velocidade['alta'] = fuzz.trimf(self.Velocidade.universe, [35, 55, 55])

        # Membros do Predador
        self.Distancia_Predador['perto'] = fuzz.trimf(self.Distancia_Predador.universe, [0, 0, 40])
        self.Distancia_Predador['medio'] = fuzz.trimf(self.Distancia_Predador.universe, [30, 60, 90])
        self.Distancia_Predador['longe'] = fuzz.trimf(self.Distancia_Predador.universe, [80, 101, 101])

        for c in [self.Forca_Separacao, self.Forca_Coesao, self.Forca_Alinhamento, self.Forca_Evasao]:
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
            ctrl.Rule(self.Distancia_Predador['perto'], self.Forca_Evasao['muito_forte']),
            ctrl.Rule(self.Distancia_Predador['medio'], self.Forca_Evasao['forte']),
            ctrl.Rule(self.Distancia_Predador['longe'], self.Forca_Evasao['fraca']),
        ]

    def __setup_inference_system(self):
        self.boidz_controller = ctrl.ControlSystem(self.rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    def calculate_fuzzy(self, current_entity, boids: list, predators: list):
        self.last_entity = current_entity
        self.last_boids = boids
        self.last_predators = predators
        
        neighbors = [b for b in boids if b is not current_entity and current_entity.position.distance_to(b.position) < self.perception_radius]
        avg_dist, density, avg_speed_diff = 50, 0, 0.0
        
        if neighbors:
            distances = [current_entity.position.distance_to(b.position) for b in neighbors]
            avg_dist = np.mean(distances)
            density = len(neighbors)
            speed_diffs = [abs(current_entity.velocity.length() - b.velocity.length()) for b in neighbors]
            avg_speed_diff = np.mean(speed_diffs)

        pred_dist = 100
        if predators:
            closest_pred = min(predators, key=lambda p: current_entity.position.distance_to(p.position))
            pred_dist = current_entity.position.distance_to(closest_pred.position)

        self.boidz_sys.input['Distancia'] = np.clip(avg_dist, 0, 51)
        self.boidz_sys.input['Densidade'] = np.clip(density, 0, 101)
        self.boidz_sys.input['Velocidade'] = np.clip(avg_speed_diff, 0, 55)
        self.boidz_sys.input['Distancia_Predador'] = np.clip(pred_dist, 0, 101)

        try:
            self.boidz_sys.compute()
        except:
            pass

    def compute(self, *args, **kwargs):
        # Esta função aceita agora qualquer argumento para evitar crashes de assinatura
        if self.last_entity is None:
            return pygame.Vector2(0, 0)
            
        outputs = getattr(self.boidz_sys, 'output', {})
        sep = outputs.get('Forca_Separacao', 0)
        coh = outputs.get('Forca_Coesao', 0)
        ali = outputs.get('Forca_Alinhamento', 0)
        eva = outputs.get('Forca_Evasao', 0)

        # Cálculo dos vetores
        v_sep = self._separation_vector(self.last_entity, self.last_boids) * sep
        v_coh = self._cohesion_vector(self.last_entity, self.last_boids) * coh
        v_ali = self._alignment_vector(self.last_entity, self.last_boids) * ali
        v_eva = self._evasion_vector(self.last_entity, self.last_predators) * eva

        return v_sep + v_coh + v_ali + v_eva

    # Funções de suporte exigidas pela GUI
    def get_system(self): return self.boidz_sys
    def get_output_variables(self): return [c.label for c in self.boidz_controller.consequents]
    def get_input_variables(self): return [a.label for a in self.boidz_controller.antecedents]

    # Lógica de vetores Pygame
    def _separation_vector(self, entity, boids):
        steer = pygame.Vector2(0, 0)
        count = 0
        for b in boids:
            if b is entity: continue
            d = entity.position.distance_to(b.position)
            if 0 < d < self.perception_radius:
                diff = (entity.position - b.position)
                if d > 0: diff /= d
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
            if desired.length() > 0: return desired.normalize()
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
            if avg_vel.length() > 0: return avg_vel.normalize()
        return pygame.Vector2(0, 0)

    def _evasion_vector(self, entity, predators):
        if not predators: return pygame.Vector2(0, 0)
        closest = min(predators, key=lambda p: entity.position.distance_to(p.position))
        if entity.position.distance_to(closest.position) < self.perception_radius * 2:
            flee = entity.position - closest.position
            if flee.length() > 0: return flee.normalize()
        return pygame.Vector2(0, 0)

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
        self.distancia = ctrl.Antecedent(np.arange(0, 502, 1), 'distancia')
        self.alinhamento = ctrl.Antecedent(np.arange(-180, 182, 1), 'alinhamento')
        self.magnitude = ctrl.Consequent(np.arange(0, 11, 0.1), 'magnitude')
        self.correcao_direcao = ctrl.Consequent(np.arange(-90, 92, 1), 'correcao_direcao')

    def __setup_membership_functions(self):
        self.distancia['muito_perto'] = fuzz.trimf(self.distancia.universe, [0, 0, 100])
        self.distancia['longe'] = fuzz.trimf(self.distancia.universe, [80, 500, 501])
        self.alinhamento['esquerda'] = fuzz.trimf(self.alinhamento.universe, [-180, -90, 0])
        self.alinhamento['centro'] = fuzz.trimf(self.alinhamento.universe, [-20, 0, 20])
        self.alinhamento['direita'] = fuzz.trimf(self.alinhamento.universe, [0, 90, 180])
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
        self.last_boids = boids
        if not boids: return
        closest = min(boids, key=lambda b: current_entity.position.distance_to(b.position))
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

    def compute(self, *args, **kwargs):
        if self.last_entity is None: return pygame.Vector2(0, 0)
        outputs = getattr(self.boidz_sys, 'output', {})
        mag = outputs.get('magnitude', 3)
        corr = outputs.get('correcao_direcao', 0)
        new_angle = self.last_entity.angle + math.radians(corr)
        desired_vel = pygame.Vector2(math.cos(new_angle), math.sin(new_angle)) * mag
        return desired_vel - self.last_entity.velocity

    def get_system(self): return self.boidz_sys
    def get_output_variables(self): return [c.label for c in self.boidz_controller.consequents]
    def get_input_variables(self): return [a.label for a in self.boidz_controller.antecedents]