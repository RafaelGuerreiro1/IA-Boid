import matplotlib.pyplot as plt

# 1. Definição das coordenadas (x, y) 
# Forte Esquerda: [-90, -90, -30] -> Pico no início (-90) e desce até -30
forte_esq_x, forte_esq_y = [-90, -90, -30], [1, 1, 0]

# Nenhuma: [-15, 0, 15] -> Triângulo central perfeito
nenhuma_x, nenhuma_y = [-15, 0, 15], [0, 1, 0]

# Forte Direita: [30, 90, 90] -> Sobe em 30 e trava no pico em 90
forte_dir_x, forte_dir_y = [30, 90, 90], [0, 1, 1]

# 2. Criação do gráfico
plt.figure(figsize=(10, 5))

plt.plot(forte_esq_x, forte_esq_y, color='red', linewidth=2, label='Forte Esquerda')
plt.plot(nenhuma_x, nenhuma_y, color='gray', linewidth=2, label='Nenhuma')
plt.plot(forte_dir_x, forte_dir_y, color='green', linewidth=2, label='Forte Direita')

# 3. Estilização
plt.title('Funções de Pertinência: Correção de Direção')
plt.xlabel('Graus de Correção')
plt.ylabel('Grau de Pertinência')
plt.legend()

# Ajustes de eixos
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_position('zero') # Centraliza o eixo Y no valor 0

plt.xlim(-90, 90)
plt.ylim(0, 1.05)
plt.grid(axis='y', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.show()
