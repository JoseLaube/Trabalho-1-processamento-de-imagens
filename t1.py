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

def encontrar_componente_conexo_6(volume):
    n, m, k = volume.shape 

    #cria uma cópia da matriz com 0s
    visitado = np.zeros((n, m, k), dtype=bool)

    #lista de direções conexão 6
    direcao = [
        (1,0,0),
        (-1,0,0),
        (0,1,0),
        (0,-1,0),
        (0,0,1),
        (0,0,-1)
    ]

    componentes = []

    def bfs(x, y, z, valor_alvo):
        componente = []
        fila = deque([(x, y, z)])
        visitado[x, y, z] = True
        
        while fila:
            cx, cy, cz = fila.popleft()
            componente.append((cx, cy, cz))
            
            # Verificar todos os vizinhos (conectividade-6)
            for dx, dy, dz in direcao:
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                
                if (0 <= nx < n and 0 <= ny < m and 0 <= nz < k):
                    # Verificar se não foi visitado e tem o mesmo valor
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
                        if len(componente) > 1:  # Pelo menos 2 voxels conectados
                            componentes.append({
                                'valor': valor_atual,
                                'voxels': componente,
                                'tamanho': len(componente)
                            })
    
    return componentes

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

def visualizar_grafos_3d(grafos):
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
    ax.set_title(f'Grafos 3D dos Componentes Conexos - Total: {len(grafos)} grafos')
    
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
    print(f"  → Média geral de tamanho: {total_voxels/total_componentes:.1f} voxels/componente")
    print("="*60)

# Código principal
with open('volume_TAC', 'rb') as v:
    volume = pickle.load(v)

print(f"Dimensões originais: {volume.shape}")

# Criando matriz com borda de segurança
volume_cb = adicionar_borda_3d(volume, tamanho_borda=1)
print(f"Dimensões com borda: {volume_cb.shape}")

# Busca dos componentes conexos
print("Buscando componentes conexos...")
componentes = encontrar_componente_conexo_6(volume_cb)
    
print(f"Total de componentes encontrados: {len(componentes)}")

# Ccontagem dos componentes por valor
contagem = contar_componentes_por_valor(componentes)
print(f"\nCONTAGEM POR VALOR:")
print(f"  Valor 140: {contagem[140]} componentes")
print(f"  Valor 200: {contagem[200]} componentes") 
print(f"  Valor 255: {contagem[255]} componentes")

estatisticas_detalhadas(componentes)

# Converter para grafos
print("\nConvertendo para grafos...")
grafos = componentes_para_grafos(componentes)
print(f"Convertidos para {len(grafos)} grafos")

# Visualização 3D
if grafos:
    print("Gerando visualização 3D...")
    visualizar_grafos_3d(grafos)
else:
    print("Nenhum grafo para visualizar!")