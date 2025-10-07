import pickle
import numpy as np
from collections import deque
import networkx as nx
import matplotlib.pyplot as plt

#função para adicionar borda de segurança na matriz
def adicionar_borda_3d(matriz, tamanho_borda=1):
    n, m, k = len(matriz), len(matriz[0]), len(matriz[0][0])
    
    # Nova matriz com bordas
    nova_n = n + 2 * tamanho_borda
    nova_m = m + 2 * tamanho_borda  
    nova_k = k + 2 * tamanho_borda
    
    # Criar matriz preenchida com zeros
    matriz_com_borda = [[[0 for _ in range(nova_k)] 
                        for _ in range(nova_m)] 
                        for _ in range(nova_n)]
    
    # Copiar dados originais para o centro
    for i in range(n):
        for j in range(m):
            for l in range(k):
                matriz_com_borda[i + tamanho_borda][j + tamanho_borda][l + tamanho_borda] = matriz[i][j][l]
    
    return np.array(matriz_com_borda)

def encontrar_componentes_conexos(volume, direcoes):
    n, m, k = volume.shape
    visitado = np.zeros((n, m, k), dtype=bool)
    componentes = []

    def bfs(x, y, z, valor_alvo):
        componente = []
        fila = deque([(x, y, z)])
        visitado[x, y, z] = True
        
        while fila:
            cx, cy, cz = fila.popleft()
            componente.append((cx, cy, cz))
            
            # Usar a lista de direções que foi passada como argumento
            for dx, dy, dz in direcoes:
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                
                if (0 <= nx < n and 0 <= ny < m and 0 <= nz < k):
                    if not visitado[nx, ny, nz] and volume[nx, ny, nz] == valor_alvo:
                        visitado[nx, ny, nz] = True
                        fila.append((nx, ny, nz))
        
        return componente

    for i in range(n):
        for j in range(m):
            for l in range(k):
                if not visitado[i, j, l]:
                    valor_atual = volume[i, j, l]
                    if valor_atual in [140, 200, 255]:
                        componente = bfs(i, j, l, valor_atual)
                        if len(componente) > 1:
                            componentes.append({
                                'valor': valor_atual,
                                'voxels': componente,
                                'tamanho': len(componente)
                            })
    
    return componentes

def plotar_histogramas(componentes, titulo_sufixo=""):
    tamanhos_por_valor = {140: [], 200: [], 255: []}
    
    for comp in componentes:
        valor = comp['valor']
        if valor in tamanhos_por_valor:
            tamanhos_por_valor[valor].append(comp['tamanho'])
            
    for valor, tamanhos in tamanhos_por_valor.items():
        if not tamanhos:
            print(f"Nenhum componente encontrado para o valor {valor}")
            continue
            
        plt.figure() # figura nova para cada histograma
        plt.hist(tamanhos, bins=20) # 'bins' controla o número de barras
        plt.title(f'Histograma dos grupos de valor {valor} {titulo_sufixo}')
        plt.xlabel('Tamanho do Agrupamento (em voxels)')
        plt.ylabel('Frequência (Quantidade de Agrupamentos)')
        plt.show()

def componentes_para_grafos(componentes):
    grafos = []
    
    for idx, comp in enumerate(componentes):
        if comp['tamanho'] < 2:  # Componentes muito pequenos não formam grafos interessantes
            continue
            
        G = nx.Graph()
        G.graph['valor'] = comp['valor']
        G.graph['tamanho'] = comp['tamanho']
        G.graph['id'] = idx + 1
        
        # Adicionar vértices
        for voxel in comp['voxels']:
            G.add_node(voxel)
        
        # Adicionar arestas de forma mais eficiente
        voxel_set = set(comp['voxels'])
        direcoes = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        
        for voxel in comp['voxels']:
            x, y, z = voxel
            for dx, dy, dz in direcoes:
                vizinho = (x + dx, y + dy, z + dz)
                if vizinho in voxel_set:
                    G.add_edge(voxel, vizinho)
        
        grafos.append(G)
    
    return grafos

def visualizar_grafos_3d(grafos, titulo_sufixo=""):
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Cores por valor
    cor_por_valor = {
        140: 'red',
        200: 'green',
        255: 'blue'
    }
    
    contador_por_valor = {140: 0, 200: 0, 255: 0}
    
    for G in grafos:
        valor = G.graph['valor']
        cor = cor_por_valor.get(valor, 'gray')
        contador_por_valor[valor] += 1
        
        # Extrair coordenadas
        if G.number_of_nodes() > 0:
            xs = [node[0] for node in G.nodes]
            ys = [node[1] for node in G.nodes]
            zs = [node[2] for node in G.nodes]
            
            # Plotar nós com tamanho proporcional ao grafo
            tamanho_ponto = max(10, min(50, 200 / len(xs)))
            ax.scatter(xs, ys, zs, c=cor, s=tamanho_ponto, alpha=0.7, 
                      label=f'Valor {valor}' if contador_por_valor[valor] == 1 else "")
            
            # Plotar arestas (apenas para grafos não muito grandes)
            if G.number_of_edges() < 1000:  # Limite para não sobrecarregar a visualização
                for edge in G.edges:
                    x_vals = [edge[0][0], edge[1][0]]
                    y_vals = [edge[0][1], edge[1][1]]
                    z_vals = [edge[0][2], edge[1][2]]
                    ax.plot(x_vals, y_vals, z_vals, c=cor, alpha=0.3, linewidth=0.5)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Grafos 3D dos Componentes Conexos - Total: {len(grafos)} grafos {titulo_sufixo}')
    
    # Legenda
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels)
    
    plt.show()

# FUNÇÃO PARA CONTAR COMPONENTES POR VALOR
def contar_componentes_por_valor(componentes):
    """
    Conta quantos componentes existem para cada valor (140, 200, 255)
    """
    contagem = {140: 0, 200: 0, 255: 0}
    
    for comp in componentes:
        valor = comp['valor']
        if valor in contagem:
            contagem[valor] += 1
    
    return contagem

# FUNÇÃO PARA ESTATÍSTICAS DETALHADAS
def estatisticas_detalhadas(componentes):
    """
    Mostra estatísticas detalhadas dos componentes por valor
    """
    print("\n" + "="*60)
    print("ESTATÍSTICAS DETALHADAS DOS COMPONENTES CONEXOS")
    print("="*60)
    
    # Contagem por valor
    contagem = contar_componentes_por_valor(componentes)
    
    for valor in [140, 200, 255]:
        comps_valor = [comp for comp in componentes if comp['valor'] == valor]
        
        if comps_valor:
            tamanhos = [comp['tamanho'] for comp in comps_valor]
            voxels_totais = sum(tamanhos)
            
            print(f"\nVALOR {valor}:")
            print(f"  → Quantidade de componentes: {contagem[valor]}")
            print(f"  → Total de voxels: {voxels_totais}")
            print(f"  → Tamanho mínimo: {min(tamanhos)} voxels")
            print(f"  → Tamanho máximo: {max(tamanhos)} voxels")
            print(f"  → Tamanho médio: {np.mean(tamanhos):.1f} voxels")
            print(f"  → Tamanho mediano: {np.median(tamanhos):.1f} voxels")
            
            # Componentes por faixa de tamanho
            pequenos = len([t for t in tamanhos if t <= 10])
            medios = len([t for t in tamanhos if 10 < t <= 100])
            grandes = len([t for t in tamanhos if t > 100])
            
            print(f"  → Componentes pequenos (≤10): {pequenos}")
            print(f"  → Componentes médios (11-100): {medios}")
            print(f"  → Componentes grandes (>100): {grandes}")
        else:
            print(f"\nVALOR {valor}: Nenhum componente encontrado")
    
    # Estatísticas gerais
    total_componentes = len(componentes)
    total_voxels = sum([comp['tamanho'] for comp in componentes])
    
    print(f"\n{'='*60}")
    print(f"RESUMO GERAL:")
    print(f"  → Total de componentes: {total_componentes}")
    print(f"  → Total de voxels nos componentes: {total_voxels}")
    if total_componentes > 0:
        print(f"  → Média geral de tamanho: {total_voxels/total_componentes:.1f} voxels/componente")
    print("="*60)
    


def executar_analise_completa(volume, tipo_conectividade):

    print(f"# ANÁLISE COM CONECTIVIDADE-{tipo_conectividade}")
    
    # Define a lista de direções com base no tipo
    if tipo_conectividade == 6:
        direcoes = [
            (1,0,0), (-1,0,0), (0,1,0),
            (0,-1,0), (0,0,1), (0,0,-1)
        ]
    elif tipo_conectividade == 26:
        direcoes = []
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                for k in [-1, 0, 1]:
                    if i == 0 and j == 0 and k == 0:
                        continue
                    direcoes.append((i, j, k))
    else:
        print(f"Tipo de conectividade '{tipo_conectividade}' não suportado.")
        return

    # Passo 1: Encontrar componentes usando a função unificada
    componentes = encontrar_componentes_conexos(volume, direcoes)

    print(f"\nTotal de componentes encontrados: {len(componentes)}")
    
    # Adiciona o sufixo para os títulos dos gráficos
    sufixo_titulo = f"(Conectividade-{tipo_conectividade})"
    estatisticas_detalhadas(componentes)

    print("\nGerando histogramas...")
    plotar_histogramas(componentes, titulo_sufixo=sufixo_titulo)

    print("\nConvertendo para grafos para visualização...")
    grafos = componentes_para_grafos(componentes)
    
    if grafos:
        print(f"Convertidos para {len(grafos)} grafos.")
        print("Gerando visualização 3D...")
        visualizar_grafos_3d(grafos, titulo_sufixo=sufixo_titulo)
    else:
        print("Nenhum grafo grande o suficiente para visualizar!")

# Código principal
with open('volume_TAC', 'rb') as v:
    volume = pickle.load(v)

print(f"Dimensões originais: {volume.shape}")

# Criando matriz com borda de segurança
volume_cb = adicionar_borda_3d(volume, tamanho_borda=1)
print(f"Dimensões com borda: {volume_cb.shape}")

executar_analise_completa(volume_cb, tipo_conectividade=6)
executar_analise_completa(volume_cb, tipo_conectividade=26)

print("\nAnálise concluída.")
