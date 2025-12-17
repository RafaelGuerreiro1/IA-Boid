import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import warnings
warnings.filterwarnings("ignore")


class FuzzySystemBoid:
    def __init__(self):
        self.__setup_variables()
        self.__setup_membership_functions()
        self.__setup_rules()
        self.__setup_inference_system()

    # ==========================================================
    # VARIÁVEIS
    # ==========================================================
    def __setup_variables(self):
        # Inputs
        self.Distancia = ctrl.Antecedent(np.arange(0, 51, 1), 'Distancia')
        self.Densidade = ctrl.Antecedent(np.arange(0, 101, 1), 'Densidade')
        self.Velocidade = ctrl.Antecedent(np.arange(0, 55, 0.1), 'Velocidade')

        # Outputs
        self.Forca_Separacao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Separacao')
        self.Forca_Coesao = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Coesao')
        self.Forca_Alinhamento = ctrl.Consequent(np.arange(0, 11, 1), 'Forca_Alinhamento')

    # ==========================================================
    # FUNÇÕES DE PERTENÇA (igual ao carolia.py)
    # ==========================================================
    def __setup_membership_functions(self):
        # Distância
        self.Distancia['muito_perto'] = fuzz.trimf(self.Distancia.universe, [0, 7.5, 15])
        self.Distancia['media'] = fuzz.trimf(self.Distancia.universe, [10, 20, 30])
        self.Distancia['longe'] = fuzz.trimf(self.Distancia.universe, [25, 37.5, 50])

        # Densidade
        self.Densidade['baixa'] = fuzz.trapmf(self.Densidade.universe, [0, 0, 20, 30])
        self.Densidade['media'] = fuzz.trapmf(self.Densidade.universe, [30, 40, 45, 50])
        self.Densidade['alta'] = fuzz.trapmf(self.Densidade.universe, [45, 55, 100, 100])

        # Velocidade
        self.Velocidade['baixa'] = fuzz.trimf(self.Velocidade.universe, [0, 0, 7.2])
        self.Velocidade['media'] = fuzz.trimf(self.Velocidade.universe, [7, 12.5, 18])
        self.Velocidade['alta'] = fuzz.trimf(self.Velocidade.universe, [18, 54, 54])

        # Outputs
        for c in [self.Forca_Separacao, self.Forca_Coesao, self.Forca_Alinhamento]:
            c['fraca'] = fuzz.trimf(c.universe, [0, 0, 4])
            c['media'] = fuzz.trimf(c.universe, [3, 5, 7])
            c['forte'] = fuzz.trimf(c.universe, [6, 10, 10])
            c['muito_forte'] = fuzz.trimf(c.universe, [8, 10, 10])

    # ==========================================================
    # REGRAS FUZZY (carolia.py)
    # ==========================================================
    def __setup_rules(self):
        rules = []

        # Distância → Separação
        rules.append(ctrl.Rule(self.Distancia['muito_perto'], self.Forca_Separacao['muito_forte']))
        rules.append(ctrl.Rule(self.Distancia['media'], self.Forca_Separacao['media']))
        rules.append(ctrl.Rule(self.Distancia['longe'], self.Forca_Separacao['fraca']))

        # Densidade → Coesão
        rules.append(ctrl.Rule(self.Densidade['baixa'], self.Forca_Coesao['forte']))
        rules.append(ctrl.Rule(self.Densidade['media'], self.Forca_Coesao['media']))
        rules.append(ctrl.Rule(self.Densidade['alta'], self.Forca_Coesao['fraca']))

        # Velocidade → Alinhamento
        rules.append(ctrl.Rule(self.Velocidade['baixa'], self.Forca_Alinhamento['fraca']))
        rules.append(ctrl.Rule(self.Velocidade['media'], self.Forca_Alinhamento['media']))
        rules.append(ctrl.Rule(self.Velocidade['alta'], self.Forca_Alinhamento['forte']))

        self.rules = rules

    # ==========================================================
    # SISTEMA
    # ==========================================================
    def __setup_inference_system(self):
        self.controller = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.controller)

    # ==========================================================
    # CÁLCULO FUZZY
    # ==========================================================
    def calculate(self, distancia, densidade, velocidade):
        self.simulation.input['Distancia'] = distancia
        self.simulation.input['Densidade'] = densidade
        self.simulation.input['Velocidade'] = velocidade

        self.simulation.compute()

        return {
            'Separacao': self.simulation.output['Forca_Separacao'],
            'Coesao': self.simulation.output['Forca_Coesao'],
            'Alinhamento': self.simulation.output['Forca_Alinhamento']
        }

if __name__ == "__main__":
    fuzzy = FuzzySystemBoid()

    resultado = fuzzy.calculate(
        distancia=12,     # perto
        densidade=45,     # média
        velocidade=10     # média
    )

    print("Resultados do sistema fuzzy:")
    for k, v in resultado.items():
        print(f"{k}: {v:.2f}")
