"""Benchmark único: gera CSVs, máquina, tabelas e gráficos a partir das mesmas medições.

Uso:
    python benchmark.py            # execução completa (alguns minutos)
    python benchmark.py --rapido   # smoke test: tamanhos pequenos, saída em resultados_rapido/
    python benchmark.py --regerar  # refaz tabelas e gráficos a partir dos CSVs de resultados/

Experimentos (semente 2026, perf_counter_ns, tempo só da chamada do algoritmo):
  1. Escalonamento: 5 algoritmos x n = 100..6400 x 10 repetições -> medicoes.csv / medias.csv
  2. Limiar da Etapa 2: limiares 2..64 em n = 1600, 3200, 6400, 10 repetições -> limiar_*.csv
  3. Cruzamento: n = 4..256, 10 repetições (cada uma é a média de várias chamadas) -> cruzamento.csv
O limiar com menor tempo relativo (mediana) é gravado em limiar_escolhido.txt e usado no experimento 1.
"""
import argparse
import csv
import gc
import os
import platform
import random
import sys
from pathlib import Path
from statistics import mean, median, pstdev
from time import perf_counter_ns

from algoritmos import (soma_maxima_bruta, soma_maxima_divisao, soma_maxima_linear,
                        par_mais_proximo_bruto, par_mais_proximo_divisao)

SEMENTE = 2026
REPETICOES = 10  # o enunciado exige no mínimo 5; 10 reduz o ruído de um notebook
TAMANHOS = (100, 200, 400, 800, 1600, 3200, 6400)
LIMIARES = (2, 4, 8, 16, 32, 64)
TAMANHOS_LIMIAR = (1600, 3200, 6400)
TAMANHOS_CRUZAMENTO = (4, 8, 16, 32, 64, 128, 256)
ALGORITMOS = ('soma_bruta', 'soma_divisao', 'soma_linear', 'par_bruto', 'par_divisao')


def gerar_vetor(rng, n):
    return [rng.randint(-100, 100) for _ in range(n)]


def gerar_pontos(rng, n):
    return [(rng.randint(-10000, 10000), rng.randint(-10000, 10000)) for _ in range(n)]


def cronometrar(funcao, entrada, chamadas=1):
    """Tempo médio (ms) de uma chamada, medindo `chamadas` chamadas seguidas."""
    gc.collect()
    gc.disable()  # evita que uma coleta de lixo caia no meio da medição
    try:
        inicio = perf_counter_ns()
        for _ in range(chamadas):
            funcao(entrada)
        return (perf_counter_ns() - inicio) / 1_000_000 / chamadas
    finally:
        gc.enable()


def estabilizar_processo():
    """Reduz o ruído: prioridade alta e um único núcleo (melhor esforço; ignora falhas)."""
    try:
        nucleo = (os.cpu_count() or 1) - 1
        if sys.platform == 'win32':
            import ctypes
            k32 = ctypes.windll.kernel32
            processo = k32.GetCurrentProcess()
            k32.SetPriorityClass(processo, 0x00000080)  # HIGH_PRIORITY_CLASS
            k32.SetProcessAffinityMask(processo, ctypes.c_size_t(1 << nucleo))
        elif hasattr(os, 'sched_setaffinity'):
            os.sched_setaffinity(0, {nucleo})
    except Exception:
        pass


def escrever_csv(caminho, campos, linhas):
    with caminho.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def resumo(valores):
    return {'media_ms': round(mean(valores), 6), 'mediana_ms': round(median(valores), 6),
            'desvio_ms': round(pstdev(valores), 6), 'min_ms': round(min(valores), 6)}


# ---------------------------------------------------------------- experimento 2 (primeiro: define o limiar)
def experimento_limiar(tamanhos, repeticoes):
    rng = random.Random(SEMENTE + 1)
    registros = []
    for n in tamanhos:
        for repeticao in range(1, repeticoes + 1):
            pontos = gerar_pontos(rng, n)
            for limiar in LIMIARES:
                t = cronometrar(lambda p, L=limiar: par_mais_proximo_divisao(p, limiar=L), pontos)
                registros.append({'limiar': limiar, 'n': n, 'repeticao': repeticao, 'tempo_ms': round(t, 6)})
        print('Limiar: n =', n, 'concluído', flush=True)
    medias = []
    for limiar in LIMIARES:
        for n in tamanhos:
            vals = [r['tempo_ms'] for r in registros if r['limiar'] == limiar and r['n'] == n]
            medias.append({'limiar': limiar, 'n': n, **resumo(vals)})
    # Pontuação: mediana do limiar / melhor mediana entre os limiares, em cada n; média entre os n.
    # A mediana é usada na escolha por ser robusta a picos de ruído; as médias também ficam nos CSVs.
    pontuacao = {}
    for limiar in LIMIARES:
        razoes = []
        for n in tamanhos:
            melhor_n = min(m['mediana_ms'] for m in medias if m['n'] == n)
            razoes.append(next(m['mediana_ms'] for m in medias if m['limiar'] == limiar and m['n'] == n) / melhor_n)
        pontuacao[limiar] = mean(razoes)
    escolhido = min(pontuacao, key=lambda k: (pontuacao[k], k))
    return registros, medias, pontuacao, escolhido


# ---------------------------------------------------------------- experimento 1
def experimento_escalonamento(tamanhos, repeticoes, limiar):
    rng = random.Random(SEMENTE)
    funcoes = {'soma_bruta': soma_maxima_bruta, 'soma_divisao': soma_maxima_divisao,
               'soma_linear': soma_maxima_linear, 'par_bruto': par_mais_proximo_bruto,
               'par_divisao': lambda p: par_mais_proximo_divisao(p, limiar=limiar)}
    registros = []
    for n in tamanhos:
        for repeticao in range(1, repeticoes + 1):
            vetor, pontos = gerar_vetor(rng, n), gerar_pontos(rng, n)
            for nome, funcao in funcoes.items():
                entrada = vetor if nome.startswith('soma') else pontos
                # O(n) é rápido demais para um único disparo: média de várias chamadas.
                chamadas = max(1, 2000 // n) if nome == 'soma_linear' else 1
                registros.append({'algoritmo': nome, 'n': n, 'repeticao': repeticao,
                                  'tempo_ms': round(cronometrar(funcao, entrada, chamadas), 6)})
        print('Escalonamento: n =', n, 'concluído', flush=True)
    medias = []
    for nome in funcoes:
        for n in tamanhos:
            vals = [r['tempo_ms'] for r in registros if r['algoritmo'] == nome and r['n'] == n]
            medias.append({'algoritmo': nome, 'n': n, **resumo(vals)})
    return registros, medias


# ---------------------------------------------------------------- experimento 3
def experimento_cruzamento(tamanhos, repeticoes):
    rng = random.Random(SEMENTE + 2)
    funcoes = {'soma_bruta': soma_maxima_bruta, 'soma_divisao': soma_maxima_divisao,
               'soma_linear': soma_maxima_linear, 'par_bruto': par_mais_proximo_bruto,
               'par_divisao': lambda p: par_mais_proximo_divisao(p, limiar=2)}
    registros = []
    for n in tamanhos:
        chamadas = max(5, 20000 // n)
        for repeticao in range(1, repeticoes + 1):
            vetor, pontos = gerar_vetor(rng, n), gerar_pontos(rng, n)
            for nome, funcao in funcoes.items():
                entrada = vetor if nome.startswith('soma') else pontos
                registros.append({'algoritmo': nome, 'n': n, 'repeticao': repeticao,
                                  'tempo_ms': round(cronometrar(funcao, entrada, chamadas), 6)})
    medias = []
    for nome in funcoes:
        for n in tamanhos:
            vals = [r['tempo_ms'] for r in registros if r['algoritmo'] == nome and r['n'] == n]
            medias.append({'algoritmo': nome, 'n': n, **resumo(vals)})
    return registros, medias


# ---------------------------------------------------------------- máquina
def _cpu():
    try:
        if sys.platform == 'win32':
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as chave:
                return winreg.QueryValueEx(chave, 'ProcessorNameString')[0].strip()
        if sys.platform.startswith('linux'):
            for linha in Path('/proc/cpuinfo').read_text().splitlines():
                if linha.startswith('model name'):
                    return linha.split(':', 1)[1].strip()
        if sys.platform == 'darwin':
            import subprocess
            return subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
    except Exception:
        pass
    return platform.processor() or 'não informado'


def _ram_gb():
    try:
        if sys.platform == 'win32':
            import ctypes

            class MEM(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            m = MEM()
            m.dwLength = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys / 2**30
        if sys.platform.startswith('linux'):
            for linha in Path('/proc/meminfo').read_text().splitlines():
                if linha.startswith('MemTotal'):
                    return int(linha.split()[1]) / 2**20
        if sys.platform == 'darwin':
            import subprocess
            return int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True)) / 2**30
    except Exception:
        pass
    return None


def descrever_maquina(tamanhos, repeticoes, limiar):
    ram = _ram_gb()
    return '\n'.join([
        f'Sistema operacional: {platform.platform()}',
        f'Processador: {_cpu()}',
        f'Núcleos lógicos: {os.cpu_count()}',
        f'Memória RAM: {f"{ram:.1f} GB" if ram else "não informada"}',
        f'Python: {platform.python_version()} ({platform.python_implementation()})',
        f'Semente: {SEMENTE}',
        f'Repetições por tamanho: {repeticoes}',
        f'Tamanhos: {", ".join(map(str, tamanhos))}',
        f'Limiar usado na Etapa 2: {limiar}',
        '',
    ])


# ---------------------------------------------------------------- tabelas e gráficos
def tabela_markdown(medias, algoritmos, tamanhos):
    linhas = ['| n | ' + ' | '.join(algoritmos) + ' |', '|---|' + '---|' * len(algoritmos)]
    for n in tamanhos:
        celulas = [f"{next(m['media_ms'] for m in medias if m['algoritmo'] == a and m['n'] == n):.4f}"
                   for a in algoritmos]
        linhas.append(f'| {n} | ' + ' | '.join(celulas) + ' |')
    return '\n'.join(linhas)


def gerar_graficos(pasta, medias, tamanhos, lim_medias, escolhido, cruz_medias):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import math
    except ImportError:
        print('Gráficos opcionais: instale matplotlib (pip install matplotlib).')
        return

    def serie(m, nome):
        return [next(x['media_ms'] for x in m if x['algoritmo'] == nome and x['n'] == n) for n in tamanhos]

    estilos = {'soma_bruta': ('Força bruta O(n²)', 'tab:red'), 'soma_divisao': ('Divisão e conquista O(n log n)', 'tab:blue'),
               'soma_linear': ('Kadane O(n)', 'tab:green'), 'par_bruto': ('Força bruta O(n²)', 'tab:red'),
               'par_divisao': ('Divisão e conquista O(n log n)', 'tab:blue')}
    for tipo, titulo, nomes in (('soma', 'Subarranjo de soma máxima', ('soma_bruta', 'soma_divisao', 'soma_linear')),
                                ('par', 'Par de pontos mais próximos', ('par_bruto', 'par_divisao'))):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
        for nome in nomes:
            rotulo, cor = estilos[nome]
            ax1.plot(tamanhos, serie(medias, nome), marker='o', label=rotulo, color=cor)
            ax2.plot(tamanhos, serie(medias, nome), marker='o', label=rotulo, color=cor)
        # Referências teóricas ancoradas no último ponto do algoritmo mais rápido da figura
        base = nomes[1]
        t0, n0 = serie(medias, base)[0], tamanhos[0]
        ax2.plot(tamanhos, [t0 * (n * math.log2(n)) / (n0 * math.log2(n0)) for n in tamanhos], '--', color='gray',
                 label='ref. n log n (ancorada em n=100)')
        ax2.plot(tamanhos, [serie(medias, nomes[0])[0] * (n / n0) ** 2 for n in tamanhos], ':', color='black',
                 label='ref. n² (ancorada em n=100)')
        ax1.set(title=f'{titulo} (escala linear)', xlabel='Tamanho n', ylabel='Tempo médio (ms)')
        ax2.set(title=f'{titulo} (log-log)', xlabel='Tamanho n', ylabel='Tempo médio (ms)', xscale='log', yscale='log')
        ax1.legend()
        ax2.legend(fontsize=8)
        ax1.grid(alpha=.3)
        ax2.grid(alpha=.3, which='both')
        fig.tight_layout()
        fig.savefig(pasta / f'grafico_{tipo}.png', dpi=130)
        plt.close(fig)

    # razão de crescimento ao dobrar n
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for nome in ALGORITMOS:
        s = serie(medias, nome)
        ax.plot(tamanhos[1:], [s[i + 1] / s[i] for i in range(len(s) - 1)], marker='o', label=nome)
    ax.axhline(4, color='gray', ls=':', label='n²: razão 4')
    ax.axhline(2, color='gray', ls='--', label='n: razão 2')
    ax.set(title='Razão T(n)/T(n/2) ao dobrar n', xlabel='Tamanho n', ylabel='Razão entre tempos', xscale='log')
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(pasta / 'grafico_razao.png', dpi=130)
    plt.close(fig)

    # limiar
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ns = sorted({m['n'] for m in lim_medias})
    for n in ns:
        melhor = min(m['mediana_ms'] for m in lim_medias if m['n'] == n)
        ax.plot(LIMIARES, [next(m['mediana_ms'] for m in lim_medias if m['n'] == n and m['limiar'] == L) / melhor
                           for L in LIMIARES], marker='o', label=f'n = {n}')
    ax.axvline(escolhido, color='gray', ls='--', label=f'escolhido = {escolhido}')
    ax.set(title='Etapa 2: tempo (mediana) relativo ao melhor limiar', xlabel='Limiar (força bruta se n ≤ limiar)',
           ylabel='Mediana / melhor mediana', xscale='log', xticks=LIMIARES, xticklabels=LIMIARES)
    ax.minorticks_off()
    ax.legend()
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(pasta / 'grafico_limiar.png', dpi=130)
    plt.close(fig)

    # cruzamento
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ns = sorted({m['n'] for m in cruz_medias})
    for ax, (b, d, extra), titulo in ((axs[0], ('soma_bruta', 'soma_divisao', 'soma_linear'), 'Soma máxima'),
                                      (axs[1], ('par_bruto', 'par_divisao', None), 'Par mais próximo')):
        for nome in (b, d, extra):
            if nome:
                ax.plot(ns, [next(x['media_ms'] for x in cruz_medias if x['algoritmo'] == nome and x['n'] == n)
                             for n in ns], marker='o', label=estilos[nome][0] if nome != extra else 'Kadane O(n)')
        ax.set(title=f'Cruzamento — {titulo}', xlabel='Tamanho n', ylabel='Tempo médio (ms)', xscale='log', yscale='log')
        ax.legend(fontsize=8)
        ax.grid(alpha=.3, which='both')
    fig.tight_layout()
    fig.savefig(pasta / 'grafico_cruzamento.png', dpi=130)
    plt.close(fig)


def _ler_medias(caminho):
    """Lê um CSV de médias, convertendo n, limiar e os tempos para número."""
    with caminho.open(newline='', encoding='utf-8') as f:
        linhas = list(csv.DictReader(f))
    for linha in linhas:
        for chave, valor in linha.items():
            if chave != 'algoritmo':
                linha[chave] = float(valor) if '.' in valor else int(valor)
    return linhas


def regerar(pasta):
    """Recria tabelas e gráficos a partir dos CSVs já gravados (sem medir de novo)."""
    medias = _ler_medias(pasta / 'medias.csv')
    lim_medias = _ler_medias(pasta / 'limiar_medias.csv')
    cruz_medias = _ler_medias(pasta / 'cruzamento.csv')
    escolhido = int(next(l for l in (pasta / 'limiar_escolhido.txt').read_text(encoding='utf-8').splitlines()
                         if l.startswith('Limiar escolhido')).split(':')[1])
    tamanhos = sorted({m['n'] for m in medias})
    (pasta / 'tabelas.md').write_text(
        '## Soma máxima — tempo médio (ms)\n\n' + tabela_markdown(medias, ('soma_bruta', 'soma_divisao', 'soma_linear'), tamanhos)
        + '\n\n## Par mais próximo — tempo médio (ms)\n\n' + tabela_markdown(medias, ('par_bruto', 'par_divisao'), tamanhos)
        + '\n', encoding='utf-8')
    gerar_graficos(pasta, medias, tamanhos, lim_medias, escolhido, cruz_medias)
    print('Tabelas e gráficos regenerados a partir dos CSVs em', pasta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rapido', action='store_true', help='execução curta para testar o script')
    ap.add_argument('--regerar', action='store_true', help='só refaz tabelas e gráficos a partir dos CSVs')
    args = ap.parse_args()
    raiz = Path(__file__).parent
    pasta = raiz / ('resultados_rapido' if args.rapido else 'resultados')
    pasta.mkdir(exist_ok=True)
    if args.regerar:
        regerar(pasta)
        return
    estabilizar_processo()
    tamanhos, t_limiar, t_cruz = TAMANHOS, TAMANHOS_LIMIAR, TAMANHOS_CRUZAMENTO
    repeticoes = REPETICOES
    if args.rapido:
        tamanhos, t_limiar, repeticoes = (100, 200, 400), (200, 400), 2

    reg_lim, med_lim, pontuacao, escolhido = experimento_limiar(t_limiar, repeticoes)
    escrever_csv(pasta / 'limiar_medicoes.csv', ['limiar', 'n', 'repeticao', 'tempo_ms'], reg_lim)
    escrever_csv(pasta / 'limiar_medias.csv', ['limiar', 'n', 'media_ms', 'mediana_ms', 'desvio_ms', 'min_ms'], med_lim)
    (pasta / 'limiar_escolhido.txt').write_text(
        f'Limiar escolhido: {escolhido}\n'
        'Pontuação (mediana / melhor mediana entre limiares, média entre os tamanhos; menor é melhor):\n'
        + '\n'.join(f'  limiar {L}: {pontuacao[L]:.4f}' for L in LIMIARES) + '\n', encoding='utf-8')

    registros, medias = experimento_escalonamento(tamanhos, repeticoes, escolhido)
    escrever_csv(pasta / 'medicoes.csv', ['algoritmo', 'n', 'repeticao', 'tempo_ms'], registros)
    escrever_csv(pasta / 'medias.csv', ['algoritmo', 'n', 'media_ms', 'mediana_ms', 'desvio_ms', 'min_ms'], medias)

    reg_cruz, med_cruz = experimento_cruzamento(t_cruz, repeticoes)
    escrever_csv(pasta / 'cruzamento.csv', ['algoritmo', 'n', 'media_ms', 'mediana_ms', 'desvio_ms', 'min_ms'], med_cruz)

    (pasta / 'maquina.txt').write_text(descrever_maquina(tamanhos, repeticoes, escolhido), encoding='utf-8')
    (pasta / 'tabelas.md').write_text(
        '## Soma máxima — tempo médio (ms)\n\n' + tabela_markdown(medias, ('soma_bruta', 'soma_divisao', 'soma_linear'), tamanhos)
        + '\n\n## Par mais próximo — tempo médio (ms)\n\n' + tabela_markdown(medias, ('par_bruto', 'par_divisao'), tamanhos)
        + '\n', encoding='utf-8')
    gerar_graficos(pasta, medias, tamanhos, med_lim, escolhido, med_cruz)

    padrao = par_mais_proximo_divisao.__defaults__[0]
    if padrao != escolhido:
        print(f'ATENÇÃO: limiar padrão em algoritmos.py é {padrao}, mas o benchmark escolheu {escolhido}.')
    print('Limiar escolhido:', escolhido)
    print('Resultados gravados em', pasta)


if __name__ == '__main__':
    main()
