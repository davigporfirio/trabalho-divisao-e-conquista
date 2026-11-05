"""Interface de linha de comando: lê a entrada da entrada padrão e escreve a resposta na saída padrão.

Subarranjo de soma máxima
    entrada:  n e depois n inteiros (separados por espaço ou quebra de linha)
    saída:    soma inicio fim            (índices inclusivos, base 0)

Par de pontos mais próximos
    entrada:  n e depois n pares x y
    saída:    distancia x1 y1 x2 y2      (distância com 6 casas decimais)

Exemplos:
    echo "3 -5 -2 -7" | python main.py soma
    printf "2\\n0 0\\n3 4\\n" | python main.py pontos --algoritmo bruto
"""
import argparse
import sys

from algoritmos import (soma_maxima_bruta, soma_maxima_divisao, soma_maxima_linear,
                        par_mais_proximo_bruto, par_mais_proximo_divisao)

SOMAS = {'bruta': soma_maxima_bruta, 'divisao': soma_maxima_divisao, 'linear': soma_maxima_linear}
PARES = {'bruto': par_mais_proximo_bruto, 'divisao': par_mais_proximo_divisao}


def _numero(texto):
    try:
        return int(texto)
    except ValueError:
        return float(texto)


def ler_tokens(texto):
    tokens = texto.split()
    if not tokens:
        raise ValueError('entrada vazia')
    try:
        n = int(tokens[0])
    except ValueError:
        raise ValueError('o primeiro valor deve ser o inteiro n') from None
    if n < 0:
        raise ValueError('n não pode ser negativo')
    return n, tokens[1:]


def resolver_soma(texto, algoritmo='divisao'):
    n, resto = ler_tokens(texto)
    if len(resto) != n:
        raise ValueError(f'esperados {n} inteiros, recebidos {len(resto)}')
    soma, inicio, fim = SOMAS[algoritmo]([int(t) for t in resto])
    return f'{soma} {inicio} {fim}'


def resolver_pontos(texto, algoritmo='divisao'):
    n, resto = ler_tokens(texto)
    if len(resto) != 2 * n:
        raise ValueError(f'esperadas {2 * n} coordenadas para {n} pontos, recebidas {len(resto)}')
    numeros = [_numero(t) for t in resto]
    pontos = [(numeros[i], numeros[i + 1]) for i in range(0, len(numeros), 2)]
    distancia, p, q = PARES[algoritmo](pontos)
    return f'{distancia:.6f} {p[0]} {p[1]} {q[0]} {q[1]}'


def main(argv=None):
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding='utf-8')  # mensagens iguais em qualquer sistema (cp1252 no Windows)
    ap = argparse.ArgumentParser(description='Algoritmos de divisão e conquista (lê stdin, escreve stdout).')
    sub = ap.add_subparsers(dest='problema', required=True)
    a = sub.add_parser('soma', help='subarranjo de soma máxima')
    a.add_argument('--algoritmo', choices=SOMAS, default='divisao')
    b = sub.add_parser('pontos', help='par de pontos mais próximos')
    b.add_argument('--algoritmo', choices=PARES, default='divisao')
    args = ap.parse_args(argv)
    texto = sys.stdin.read()
    try:
        resolver = resolver_soma if args.problema == 'soma' else resolver_pontos
        print(resolver(texto, args.algoritmo))
    except ValueError as erro:
        print(f'erro: {erro}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
