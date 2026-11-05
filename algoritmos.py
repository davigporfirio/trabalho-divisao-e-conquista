"""Algoritmos de força bruta, divisão e conquista e versão linear (Kadane)."""
from math import hypot


def _melhor(a, b):
    """Maior soma; em empate, menor início e menor fim."""
    return min((a, b), key=lambda t: (-t[0], t[1], t[2]))


def soma_maxima_bruta(vetor):
    if not vetor:
        raise ValueError('O vetor não pode ser vazio')
    melhor = (float('-inf'), 0, 0)
    for i in range(len(vetor)):
        soma = 0
        for j in range(i, len(vetor)):
            soma += vetor[j]
            melhor = _melhor(melhor, (soma, i, j))
    return melhor


def soma_maxima_divisao(vetor):
    if not vetor:
        raise ValueError('O vetor não pode ser vazio')

    def resolver(inicio, fim):
        if inicio == fim:
            return (vetor[inicio], inicio, fim)
        meio = (inicio + fim) // 2
        esquerda = resolver(inicio, meio)
        direita = resolver(meio + 1, fim)
        soma = 0
        melhor_esq = (float('-inf'), meio)
        for i in range(meio, inicio - 1, -1):
            soma += vetor[i]
            if soma > melhor_esq[0] or (soma == melhor_esq[0] and i < melhor_esq[1]):
                melhor_esq = (soma, i)
        soma = 0
        melhor_dir = (float('-inf'), meio + 1)
        for j in range(meio + 1, fim + 1):
            soma += vetor[j]
            if soma > melhor_dir[0]:
                melhor_dir = (soma, j)
        cruzado = (melhor_esq[0] + melhor_dir[0], melhor_esq[1], melhor_dir[1])
        return _melhor(_melhor(esquerda, direita), cruzado)

    return resolver(0, len(vetor) - 1)


def soma_maxima_linear(vetor):
    """Questão desafio: algoritmo de Kadane em O(n) tempo e O(1) espaço.

    Mantém a melhor soma de um intervalo que termina em j. Se a soma
    anterior é >= 0, estender o intervalo nunca piora a soma e, em
    empate (soma anterior == 0), preserva o menor índice inicial; só
    reinicia em j quando a soma anterior é negativa. A melhor resposta
    global usa a mesma ordem das outras versões: maior soma, depois
    menor início e depois menor fim.
    """
    if not vetor:
        raise ValueError('O vetor não pode ser vazio')
    atual, inicio_atual = vetor[0], 0
    melhor = (atual, 0, 0)
    for j in range(1, len(vetor)):
        if atual < 0:
            atual, inicio_atual = vetor[j], j
        else:
            atual += vetor[j]
        if (-atual, inicio_atual, j) < (-melhor[0], melhor[1], melhor[2]):
            melhor = (atual, inicio_atual, j)
    return melhor


def _validar_pontos(pontos):
    if len(pontos) < 2:
        raise ValueError('São necessários pelo menos dois pontos')
    for p in pontos:
        if len(p) != 2:
            raise ValueError('Cada ponto deve ter duas coordenadas')


def _candidato(a, b):
    p, q = sorted((tuple(a), tuple(b)))
    return (hypot(p[0] - q[0], p[1] - q[1]), p, q)


def par_mais_proximo_bruto(pontos):
    _validar_pontos(pontos)
    melhor = (float('inf'), (), ())
    for i in range(len(pontos)):
        for j in range(i + 1, len(pontos)):
            melhor = min(melhor, _candidato(pontos[i], pontos[j]))
    return melhor


def par_mais_proximo_divisao(pontos, limiar=16):
    """Ordena uma vez em x/y; combina em faixa com até 7 sucessores."""
    _validar_pontos(pontos)
    if limiar < 2:
        raise ValueError('O limiar deve ser pelo menos 2')
    # IDs preservam multiplicidade de pontos coincidentes.
    itens = [(p[0], p[1], i) for i, p in enumerate(pontos)]
    px = sorted(itens, key=lambda p: (p[0], p[1], p[2]))
    py = sorted(itens, key=lambda p: (p[1], p[0], p[2]))

    def resolver(xs, ys):
        n = len(xs)
        # Com n <= 3 dividir geraria uma metade de 1 ponto (sem par); por isso
        # limiar 2 e 3 se comportam igual: subproblemas de até 3 pontos vão à força bruta.
        if n <= limiar or n <= 3:
            return par_mais_proximo_bruto([(p[0], p[1]) for p in xs])
        meio = n // 2
        esq, dir = xs[:meio], xs[meio:]
        ids_esq = {p[2] for p in esq}
        yesq, ydir = [], []
        for p in ys:
            (yesq if p[2] in ids_esq else ydir).append(p)
        melhor = min(resolver(esq, yesq), resolver(dir, ydir))
        delta = melhor[0]
        linha = xs[meio][0]
        faixa = [p for p in ys if abs(p[0] - linha) <= delta]
        for i, p in enumerate(faixa):
            for q in faixa[i + 1:i + 8]:
                if q[1] - p[1] > melhor[0]:
                    break
                melhor = min(melhor, _candidato(p[:2], q[:2]))
        return melhor

    return resolver(px, py)
