import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
import pygame
import math

# =========================================
#        Zebras
# =========================================

class FuzzySystemBoid:
    def __init__(self, config):
        self.config = config
        # Carregar configurações ou usar valores base
        self.perception_radius = getattr(config, 'perception_radius', 50)

        self.max_speed_config = getattr(getattr(config, 'boids', None), 'MAX_SPEED', 5)
        print(f"DEBUG: MAX_SPEED lido do JSON = {self.max_speed_config}")

        # Variáveis de estado para guardar o que o boid vê
        self.last_entity = None # n existe nenhum last quando criamos o objeto
        self.last_boids = [] #estado das zebras
        self.last_predators = [] # estado das hienas

        # ==== Setup Variables ====
        self.__setup_variables()
        # ==== Setup Membership Functions ====
        self.__setup_membership_functions()
        # ==== Setup Rules ====
        self.__setup_rules() #sistema de inferencia
        # ==== Setup Inference System ====
        self.__setup_inference_system()

    def __setup_variables(self):
        # Percepção (input)
        self.Distancia = ctrl.Antecedent(np.arange(0, 101, 1), 'Distancia')
        self.Densidade = ctrl.Antecedent(np.arange(0, 101, 1), 'Densidade')
        self.Velocidade = ctrl.Antecedent(np.arange(0, 61, 1), 'Velocidade')
        # Variável para detetar o predador
        self.Distancia_Hiena = ctrl.Antecedent(np.arange(0, 201, 1), 'Distancia_Hiena')

        # Desfuzificação (output) - As forças que vamos aplicar no boid
        self.Forca_Separacao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Separacao')
        self.Forca_Coesao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Coesao')
        self.Forca_Alinhamento = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Alinhamento')
        self.Forca_Evasao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Evasao')

    def __setup_membership_functions(self):
        # --- DISTÂNCIA ---
        self.Distancia['muito_perto'] = fuzz.trimf(self.Distancia.universe, [0, 0, 15])
        
        # Testámos com Triangular mas era instável, no que toca o output
        # Com Trapezoidal na zona 'média', as zebras ficam mais estáveis na manada.
        self.Distancia['media'] = fuzz.trapmf(self.Distancia.universe, [10, 20, 40, 50]) 
        
        self.Distancia['longe'] = fuzz.trimf(self.Distancia.universe, [40, 100, 100])

        # --- DENSIDADE ---
        # A densidade é um intervalo, não um valor exato, isto é não tem uma soluão binária, 
        # por isso usámos trapezios.
        self.Densidade['baixa'] = fuzz.trapmf(self.Densidade.universe, [0, 0, 5, 10])
        self.Densidade['media'] = fuzz.trapmf(self.Densidade.universe, [5, 15, 25, 35])
        self.Densidade['alta'] = fuzz.trapmf(self.Densidade.universe, [30, 50, 100, 100])

        # --- VELOCIDADE ---
        # Aqui mantivemos triangular
        self.Velocidade['baixa'] = fuzz.trimf(self.Velocidade.universe, [0, 0, 15])
        self.Velocidade['media'] = fuzz.trimf(self.Velocidade.universe, [10, 25, 40])
        self.Velocidade['alta'] = fuzz.trimf(self.Velocidade.universe, [35, 60, 60])

        # --- Distancia à Hiena ---
        self.Distancia_Hiena['perigo'] = fuzz.trimf(self.Distancia_Hiena.universe, [0, 0, 80])
        self.Distancia_Hiena['atento'] = fuzz.trimf(self.Distancia_Hiena.universe, [50, 120, 150])
        self.Distancia_Hiena['seguro'] = fuzz.trimf(self.Distancia_Hiena.universe, [130, 200, 200])

        # --- OUTPUTS ---
        # Outputs usamos sempre triangular para a decisão ser mais precisa.
        # Uma vez que, com afunção triangular, o máximo pertença acontece em um ponto único 
        # (vertice do triangulo, o ponto medio do intervalo)
        for c in [self.Forca_Separacao, self.Forca_Coesao, self.Forca_Alinhamento, self.Forca_Evasao]:
            c['fraca'] = fuzz.trimf(c.universe, [0, 0, 4])
            c['media'] = fuzz.trimf(c.universe, [3, 5, 7])
            c['forte'] = fuzz.trimf(c.universe, [6, 10, 10])

    def __setup_rules(self):
        # Regras de comportamento de cardume
        r1 = ctrl.Rule(self.Distancia['media'], (self.Forca_Separacao['media'], self.Forca_Coesao['media'], self.Forca_Alinhamento['forte']))
        r2 = ctrl.Rule(self.Distancia['muito_perto'], (self.Forca_Separacao['forte'], self.Forca_Coesao['fraca'], self.Forca_Alinhamento['media']))
        r3 = ctrl.Rule(self.Distancia['longe'], (self.Forca_Separacao['fraca'], self.Forca_Coesao['forte']))

        # Regra para a densidade (se tiver muitas zebras, afasta um bocado)
        r4 = ctrl.Rule(self.Densidade['alta'], self.Forca_Separacao['media'])

        # Se for rapido, alinha com o grupo
        r5 = ctrl.Rule(self.Velocidade['alta'], self.Forca_Alinhamento['forte'])

        # Regras face à distancia das hienas (Prioridade máxima: FUGIR)
        r6 = ctrl.Rule(self.Distancia_Hiena['perigo'], (self.Forca_Evasao['forte'], self.Forca_Separacao['forte'], self.Forca_Alinhamento['fraca']))
        r7 = ctrl.Rule(self.Distancia_Hiena['atento'], self.Forca_Evasao['media'])

        self.rules = [r1, r2, r3, r4, r5, r6, r7]

    def __setup_inference_system(self):
        # ==== Inference System ====
        self.boidz_controller = ctrl.ControlSystem(self.rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)
        #cria o sistema fuzzy completo e permite simular com valores concretos.como?

    def get_system(self):
        return self.boidz_sys

    def calculate_fuzzy(self, current_entity, boids: list, predators: list):
        self.last_entity = current_entity # guarda a zebra atual
        self.last_boids = boids if boids else [] # faz com que a lista nunca seja none para n dar erro
        self.last_predators = predators if predators else [] #idem, esta linha so é necessária faace à distancia do predadpr?

        # --- Screen Wrap (Teletransporte) ---
        # Tivemos de implementar isto aqui porque senao os boids fugiam do ecra
        # isto funciona como tentativa, mas como é acessório, caso haja algum erro vai para o except
        w, h = pygame.display.get_surface().get_size() # retorna uma tupla quer da altura quer da largura
        if current_entity.position.x > w: current_entity.position.x = 0 # passou do valor que tinhamos no eixo do x? volta ao incio do eixo
        elif current_entity.position.x < 0: current_entity.position.x = w # movimento horizontal
        if current_entity.position.y > h: current_entity.position.y = 0
        elif current_entity.position.y < 0: current_entity.position.y = h
        
        # ------------------------------------
        # dentro desta lista vão ficar todos as zebras vizinhas
        #  incluindo apenas aquelas que estão dentro do seu raio de percepção, face à zebra atual.
        # z= zebra
        neighbors = [z for z in self.last_boids if z is not current_entity and current_entity.position.distance_to(z.position) < self.perception_radius]

        avg_dist = 100 # Default longe
        density = 0
        avg_speed_diff = 0.0

        if neighbors:
            distances = [current_entity.position.distance_to(z.position) for z in neighbors]# distancia da zebra atual a cada um dos seus vizinhos
            avg_dist = float(np.mean(distances)) # media dessa tal distância
            density = len(neighbors)# numero de vizinhos logo é a densidade
            speed_diffs = [abs(current_entity.velocity.length() - z.velocity.length()) for z in neighbors] #Uma lista de diferenças de velocidade entre a zebra atual e cada vizinho.
            avg_speed_diff = float(np.mean(speed_diffs)) #diferença média de velocidade entre a zebra atual e seus vizinhos

        # Calcular distancia ao predador
        pred_dist = 200 # Default seguro
        if self.last_predators:
            closest_pred = min(self.last_predators, key=lambda p: current_entity.position.distance_to(p.position))
            pred_dist = current_entity.position.distance_to(closest_pred.position)

        # Atualizar inputs (com clip para garantir que nao sai do universo)
        self.boidz_sys.input['Distancia'] = np.clip(avg_dist, 0, 100)
        self.boidz_sys.input['Densidade'] = np.clip(density, 0, 100)
        self.boidz_sys.input['Velocidade'] = np.clip(avg_speed_diff, 0, 60)
        self.boidz_sys.input['Distancia_Hiena'] = np.clip(pred_dist, 0, 200)

        # print(f"Dist: {avg_dist}, Dens: {density}") # Debug

        self.boidz_sys.compute()
        

    def compute(self):
        if self.last_entity is None:
            return pygame.Vector2(0, 0)
        
        try:
            # Ler outputs do sistema Fuzzy
            sep = self.boidz_sys.output.get('Forca_Separacao', 0)
            coh = self.boidz_sys.output.get('Forca_Coesao', 0)
            ali = self.boidz_sys.output.get('Forca_Alinhamento', 0)
            eva = self.boidz_sys.output.get('Forca_Evasao', 0)

            # Aplicar multiplicadores para afinar o comportamento
            v_sep = self._separation_vector(self.last_entity, self.last_boids) * sep * 1.2
            v_coh = self._cohesion_vector(self.last_entity, self.last_boids) * coh
            v_ali = self._alignment_vector(self.last_entity, self.last_boids) * ali * 2.0
            v_eva = self._evasion_vector(self.last_entity, self.last_predators) * eva * 2.5
            #Estes vetores são multiplicados pelo valor fuzzy correspondente 
            # ajustando intensidade da força.

            return v_sep + v_coh + v_ali + v_eva
        except:
            return pygame.Vector2(0, 0)

    # Métodos auxiliares de vetores
    def _separation_vector(self, entity, boids):#calcula o vetor de separação de uma zebra em relação aos vizinhos
        steer = pygame.Vector2(0, 0) #vetor acumulador que vai somar todas as forças de afastamento
        count = 0# Conta quantos vizinhos estão próximos, para depois calcular a média
        for z in boids:
            if z is entity: continue
            d = entity.position.distance_to(z.position) # distancia entre a zebra atual e o vizinho
            if 0 < d < self.perception_radius: # só é vizinho caso esteja dentro do raio de percepção
                diff = (entity.position - z.position) # calcular o vetor do vizinho da zebra à zebra atual
                diff.normalize_ip() # normalização do vetor
                steer += diff #Soma esse vetor unitário ao acumulador
                count += 1
        return steer / count if count > 0 else steer #Retorna a média dos vetores de afastamento, dividindo pelo número de vizinhos

    def _cohesion_vector(self, entity, boids): #calcula o vetor de coesão para a zebra atual
        center = pygame.Vector2(0, 0) #acumular as posições dos vizinhos
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
        steer = pygame.Vector2(0,0)
        closest = min(predators, key=lambda p: entity.position.distance_to(p.position))
        dist = entity.position.distance_to(closest.position)
        # Se tiver a menos de 200px, foge
        if dist < 200:
            diff = entity.position - closest.position
            if diff.length() > 0: steer = diff.normalize()
        return steer

    def get_output_variables(self) -> list[str]:
        if not hasattr(self, 'boidz_controller'): return []
        return [consequent.label for consequent in self.boidz_controller.consequents]

    def get_input_variables(self) -> list[str]:
        if not hasattr(self, 'boidz_controller'): return []
        return [antecedent.label for antecedent in self.boidz_controller.antecedents]

# =========================================
#          Hiena 
# =========================================

class FuzzySystemPredator:
    def __init__(self, config):
        self.config = config
        # Aumentei a velocidade para 15 para ele conseguir apanhar os boids## isto é suposto acontecer?
        self.max_speed = getattr(config, 'max_speed', 15) 
        self.last_entity = None
        self.last_boids = []

        # ==== Setup Variables ====
        self.__setup_variables()
        # ==== Setup Membership Functions ====
        self.__setup_membership_functions()
        # ==== Setup Rules ====
        self.__setup_rules()
        # ==== Setup Inference System ====
        self.__setup_inference_system()

    def __setup_variables(self):
        self.distancia = ctrl.Antecedent(np.arange(0, 502, 1), 'distancia')
        self.alinhamento = ctrl.Antecedent(np.arange(-180, 182, 1), 'alinhamento') # assim faz 360
        
        # Universo estendido para velocidade (até 16)
        self.magnitude = ctrl.Consequent(np.arange(0, 16, 0.1), 'magnitude')
        self.correcao_direcao = ctrl.Consequent(np.arange(-90, 92, 1), 'correcao_direcao')

    def __setup_membership_functions(self):
        self.distancia['muito_perto'] = fuzz.trimf(self.distancia.universe, [0, 0, 100])
        self.distancia['longe'] = fuzz.trimf(self.distancia.universe, [80, 500, 501])

        # Alinhamento
        self.alinhamento['esquerda'] = fuzz.trimf(self.alinhamento.universe, [-180, -90, -10])
        # Aumentei o centro para [-40, 40] para ele não tremer tanto a perseguir
        self.alinhamento['centro'] = fuzz.trimf(self.alinhamento.universe, [-40, 0, 40])
        self.alinhamento['direita'] = fuzz.trimf(self.alinhamento.universe, [10, 90, 180])

        self.magnitude['lenta'] = fuzz.trimf(self.magnitude.universe, [0, 2, 8])
        self.magnitude['rapida'] = fuzz.trimf(self.magnitude.universe, [5, 15, 15])

        self.correcao_direcao['forte_esq'] = fuzz.trimf(self.correcao_direcao.universe, [-90, -90, -30])
        self.correcao_direcao['nenhuma'] = fuzz.trimf(self.correcao_direcao.universe, [-15, 0, 15])
        self.correcao_direcao['forte_dir'] = fuzz.trimf(self.correcao_direcao.universe, [30, 90, 90])

    def __setup_rules(self):
        # Regras simples: se tiver longe anda devagar, se perto ataca
        r1 = ctrl.Rule(self.distancia['muito_perto'], self.magnitude['rapida'])
        r2 = ctrl.Rule(self.distancia['longe'], self.magnitude['lenta'])
        
        r3 = ctrl.Rule(self.alinhamento['esquerda'], self.correcao_direcao['forte_esq'])
        r4 = ctrl.Rule(self.alinhamento['centro'], self.correcao_direcao['nenhuma'])
        r5 = ctrl.Rule(self.alinhamento['direita'], self.correcao_direcao['forte_dir'])

        self.rules = [r1, r2, r3, r4, r5]

    def __setup_inference_system(self):
        # ==== Inference System ====
        self.boidz_controller = ctrl.ControlSystem(self.rules)
        self.boidz_sys = ctrl.ControlSystemSimulation(self.boidz_controller)

    def get_system(self):
        return self.boidz_sys

    def calculate_fuzzy(self, current_entity, boids: list):
        self.last_entity = current_entity
        self.last_boids = boids if boids else []

        # --- Screen Wrap (Predator) ---
        w, h = pygame.display.get_surface().get_size()
        if current_entity.position.x > w: current_entity.position.x = 0
        elif current_entity.position.x < 0: current_entity.position.x = w
        if current_entity.position.y > h: current_entity.position.y = 0
        elif current_entity.position.y < 0: current_entity.position.y = h
        

        if not self.last_boids: return

        # Encontrar a presa mais proxima
        closest = min(self.last_boids, key=lambda b: current_entity.position.distance_to(b.position))
        dist = current_entity.position.distance_to(closest.position)

        # Calcular o angulo para a presa
        dir_to_prey = closest.position - current_entity.position
        if dir_to_prey.length() == 0:
            angle_diff = 0
        else:
            target_angle = math.degrees(math.atan2(dir_to_prey.y, dir_to_prey.x))
            current_angle = math.degrees(current_entity.angle)
            angle_diff = (target_angle - current_angle + 180) % 360 - 180

        self.boidz_sys.input['distancia'] = np.clip(dist, 0, 501)
        self.boidz_sys.input['alinhamento'] = np.clip(angle_diff, -180, 181)

        self.boidz_sys.compute()
        

    def compute(self, current_entity=None):
        if current_entity: self.last_entity = current_entity
        if self.last_entity is None: return pygame.Vector2(0, 0)

        try:
            outputs = getattr(self.boidz_sys, 'output', {})
            mag = outputs.get('magnitude', 3)
            corr = outputs.get('correcao_direcao', 0)

            # Aplicar a rotação e velocidade
            new_angle = self.last_entity.angle + math.radians(corr)
            desired_vel = pygame.Vector2(math.cos(new_angle), math.sin(new_angle)) * mag
            
            return desired_vel - self.last_entity.velocity
        except:
            return pygame.Vector2(0, 0)

    def get_output_variables(self) -> list[str]:
        if not hasattr(self, 'boidz_controller'): return []
        return [consequent.label for consequent in self.boidz_controller.consequents]

    def get_input_variables(self) -> list[str]:
        if not hasattr(self, 'boidz_controller'): return []
        return [antecedent.label for antecedent in self.boidz_controller.antecedents]