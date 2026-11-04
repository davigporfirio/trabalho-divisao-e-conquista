"""Reproduz metodologia: 6 tamanhos, 5 repetições, semente 2026."""
import csv
import platform
import random
from pathlib import Path
from statistics import mean
from time import perf_counter_ns
from algoritmos import (soma_maxima_bruta, soma_maxima_divisao,
                        par_mais_proximo_bruto, par_mais_proximo_divisao)

PASTA = Path(__file__).parent / 'resultados'
PASTA.mkdir(exist_ok=True)
FUNCOES = {'soma_bruta': soma_maxima_bruta, 'soma_divisao': soma_maxima_divisao,
           'par_bruto': par_mais_proximo_bruto, 'par_divisao': par_mais_proximo_divisao}


def executar():
    rng = random.Random(2026)
    registros = []
    for n in (100, 200, 400, 800, 1600, 3200):
        for repeticao in range(1, 6):
            vetor = [rng.randint(-100, 100) for _ in range(n)]
            pontos = [(rng.randint(-10000, 10000), rng.randint(-10000, 10000)) for _ in range(n)]
            for nome, funcao in FUNCOES.items():
                entrada = vetor if nome.startswith('soma') else pontos
                inicio = perf_counter_ns()
                funcao(entrada)
                duracao_ms = (perf_counter_ns() - inicio) / 1_000_000
                registros.append({'algoritmo': nome, 'n': n, 'repeticao': repeticao,
                                  'tempo_ms': round(duracao_ms, 6)})
        print('Concluído:', n)
    with (PASTA / 'medicoes.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['algoritmo', 'n', 'repeticao', 'tempo_ms'])
        w.writeheader()
        w.writerows(registros)
    medias = []
    for nome in FUNCOES:
        for n in (100, 200, 400, 800, 1600, 3200):
            valores = [r['tempo_ms'] for r in registros if r['algoritmo'] == nome and r['n'] == n]
            medias.append({'algoritmo': nome, 'n': n, 'media_ms': round(mean(valores), 6)})
    with (PASTA / 'medias.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['algoritmo', 'n', 'media_ms'])
        w.writeheader()
        w.writerows(medias)
    (PASTA / 'maquina.txt').write_text(
        f'Sistema: {platform.platform()}\nPython: {platform.python_version()}\n'
        f'Processador: {platform.processor() or "não informado"}\n'
        'Semente: 2026\nRepetições: 5\nTamanhos: 100, 200, 400, 800, 1600, 3200\n', encoding='utf-8')
    try:
        import matplotlib.pyplot as plt
        for tipo in ('soma', 'par'):
            for nome in (f'{tipo}_bruta', f'{tipo}_divisao'):
                dados = [r for r in medias if r['algoritmo'] == nome]
                plt.plot([r['n'] for r in dados], [r['media_ms'] for r in dados], marker='o', label=nome)
            plt.title(f'Comparação: {tipo}')
            plt.xlabel('Tamanho n')
            plt.ylabel('Tempo médio (ms)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(PASTA / f'grafico_{tipo}.png')
            plt.close()
    except ImportError:
        print('Gráficos opcionais: instale matplotlib (pip install matplotlib).')
    print('Resultados gravados em', PASTA)


if __name__ == '__main__':
    executar()
