"""Gera relatorio.pdf lendo os CSVs de resultados/ (todos os números do texto vêm dos dados).

Uso:  python benchmark.py && python gerar_relatorio.py
Requer: pip install reportlab matplotlib
"""
import csv
import json
import math
from pathlib import Path
from statistics import mean

from reportlab.graphics.shapes import Drawing, Line, Rect, String, Circle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

RAIZ = Path(__file__).parent
RES = RAIZ / 'resultados'
CASOS = RAIZ / 'tests' / 'casos_teste.json'
SAIDA = RAIZ / 'relatorio.pdf'


# ------------------------------------------------------------------ fontes
def registrar_fontes():
    candidatos = [
        (Path(r'C:\Windows\Fonts'), 'arial.ttf', 'arialbd.ttf', 'ariali.ttf', 'arialbi.ttf'),
    ]
    try:
        import matplotlib
        d = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
        candidatos.append((d, 'DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf',
                           'DejaVuSans-BoldOblique.ttf'))
    except ImportError:
        pass
    for pasta, normal, negrito, italico, negrito_italico in candidatos:
        if (pasta / normal).exists():
            for nome, arq in (('F', normal), ('F-B', negrito), ('F-I', italico), ('F-BI', negrito_italico)):
                pdfmetrics.registerFont(TTFont(nome, str(pasta / arq)))
            pdfmetrics.registerFontFamily('F', normal='F', bold='F-B', italic='F-I', boldItalic='F-BI')
            return
    raise SystemExit('Nenhuma fonte TrueType encontrada (Arial ou DejaVu).')


registrar_fontes()

BASE = ParagraphStyle('base', fontName='F', fontSize=9, leading=12, alignment=TA_JUSTIFY, spaceAfter=4)
H1 = ParagraphStyle('h1', parent=BASE, fontName='F-B', fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=4,
                    alignment=0, textColor=colors.HexColor('#1f3a5f'), keepWithNext=1)
H2 = ParagraphStyle('h2', parent=BASE, fontName='F-B', fontSize=9.5, leading=12, spaceBefore=4, spaceAfter=2,
                    alignment=0, keepWithNext=1)
TITULO = ParagraphStyle('t', parent=BASE, fontName='F-B', fontSize=16, leading=20, alignment=0, spaceAfter=2)
LEGENDA = ParagraphStyle('leg', parent=BASE, fontSize=7.5, leading=9, textColor=colors.HexColor('#444444'),
                         alignment=0)
CELULA = ParagraphStyle('cel', parent=BASE, fontSize=7.8, leading=9.5, alignment=0, spaceAfter=0)


def br(x, casas=2):
    """Número no padrão brasileiro (vírgula decimal, ponto de milhar)."""
    s = f'{x:,.{casas}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def P(texto, estilo=BASE):
    return Paragraph(texto, estilo)


# ------------------------------------------------------------------ dados
def ler(caminho):
    with caminho.open(newline='', encoding='utf-8') as f:
        linhas = list(csv.DictReader(f))
    for l in linhas:
        for k, v in l.items():
            if k != 'algoritmo':
                l[k] = float(v) if '.' in v else int(v)
    return linhas


MEDIAS = ler(RES / 'medias.csv')
BRUTAS = ler(RES / 'medicoes.csv')
LIMIAR = ler(RES / 'limiar_medias.csv')
CRUZ = ler(RES / 'cruzamento.csv')
TAMANHOS = sorted({m['n'] for m in MEDIAS})
CASOS_JSON = json.loads(CASOS.read_text(encoding='utf-8'))
MAQUINA = dict(l.split(': ', 1) for l in (RES / 'maquina.txt').read_text(encoding='utf-8').splitlines() if ': ' in l)
LIMIAR_ESCOLHIDO = int(MAQUINA['Limiar usado na Etapa 2'])
REPS = int(MAQUINA['Repetições por tamanho'])
PONTUACAO = {}
for linha in (RES / 'limiar_escolhido.txt').read_text(encoding='utf-8').splitlines():
    if linha.strip().startswith('limiar '):
        k, v = linha.strip().split(':')
        PONTUACAO[int(k.split()[1])] = float(v)


def valor(fonte, alg, n, chave='media_ms'):
    return next(r[chave] for r in fonte if r['algoritmo'] == alg and r['n'] == n)


def inclinacao(alg, chave):
    xs = [math.log(n) for n in TAMANHOS]
    ys = [math.log(valor(MEDIAS, alg, n, chave)) for n in TAMANHOS]
    mx, my = mean(xs), mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def razao_media(alg):
    s = [valor(MEDIAS, alg, n) for n in TAMANHOS]
    return mean(s[i + 1] / s[i] for i in range(len(s) - 1))


def cruzamento(bruto, dc):
    ns = sorted({r['n'] for r in CRUZ})
    return next(n for n in ns if valor(CRUZ, dc, n) < valor(CRUZ, bruto, n))


# ------------------------------------------------------------------ componentes
def tabela(dados, larguras, cabecalho_linhas=1, zebra=True, alinhamento='RIGHT'):
    t = Table(dados, colWidths=larguras, repeatRows=cabecalho_linhas)
    estilo = [('FONT', (0, 0), (-1, -1), 'F', 7.8), ('FONT', (0, 0), (-1, cabecalho_linhas - 1), 'F-B', 7.8),
              ('BACKGROUND', (0, 0), (-1, cabecalho_linhas - 1), colors.HexColor('#dfe7f2')),
              ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#888888')),
              ('ALIGN', (0, 0), (-1, -1), alinhamento), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('TOPPADDING', (0, 0), (-1, -1), 1.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.6)]
    if zebra:
        for i in range(cabecalho_linhas, len(dados)):
            if (i - cabecalho_linhas) % 2:
                estilo.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f7fa')))
    t.setStyle(TableStyle(estilo))
    return t


def figura(nome, largura_cm):
    from reportlab.lib.utils import ImageReader
    caminho = RES / nome
    w, h = ImageReader(str(caminho)).getSize()
    return Image(str(caminho), width=largura_cm * cm, height=largura_cm * cm * h / w)


def desenho_vizinhos():
    """Faixa 2δ × δ dividida em 8 quadrados de lado δ/2, com a linha mediana ao centro."""
    lado = 1.25 * cm
    x0, y0 = 1.2 * cm, 0.9 * cm
    d = Drawing(10 * cm, 3.7 * cm)
    for i in range(4):
        for j in range(2):
            d.add(Rect(x0 + i * lado, y0 + j * lado, lado, lado, strokeColor=colors.HexColor('#555555'),
                       fillColor=colors.HexColor('#e6eefb') if i < 2 else colors.HexColor('#fbeee6'), strokeWidth=0.6))
    meio = x0 + 2 * lado
    d.add(Line(meio, y0 - 0.25 * cm, meio, y0 + 2 * lado + 0.3 * cm, strokeColor=colors.black, strokeWidth=1.1,
               strokeDashArray=[3, 2]))
    d.add(Circle(meio - 0.45 * cm, y0, 0.07 * cm, fillColor=colors.black))
    d.add(String(meio - 0.62 * cm, y0 - 0.32 * cm, 'p', fontName='F-I', fontSize=8))
    d.add(String(meio - 1.3 * cm, y0 + 2 * lado + 0.45 * cm, 'linha mediana x', fontName='F', fontSize=7))
    d.add(String(meio - 0.23 * cm, y0 + 2 * lado + 0.42 * cm, 'm', fontName='F', fontSize=5.5))
    d.add(String(x0 + 0.1 * cm, y0 - 0.7 * cm, 'esquerda (δ × δ)', fontName='F', fontSize=7))
    d.add(String(meio + 0.1 * cm, y0 - 0.7 * cm, 'direita (δ × δ)', fontName='F', fontSize=7))
    d.add(String(x0 + 4 * lado + 0.2 * cm, y0 + 0.4 * lado, 'δ/2', fontName='F', fontSize=7))
    d.add(String(x0 + 4 * lado + 0.2 * cm, y0 + 1.4 * lado, 'δ/2', fontName='F', fontSize=7))
    return d


# ------------------------------------------------------------------ conteúdo
def construir():
    c = []
    n_max = TAMANHOS[-1]
    soma_b, soma_d, soma_l = 'soma_bruta', 'soma_divisao', 'soma_linear'
    par_b, par_d = 'par_bruto', 'par_divisao'
    cruz_soma = cruzamento(soma_b, soma_d)
    cruz_par = cruzamento(par_b, par_d)
    tempos_par_max = [r['tempo_ms'] for r in BRUTAS if r['algoritmo'] == par_d and r['n'] == n_max]

    c += [P('Trabalho Prático: Divisão e Conquista', TITULO),
          P('Relatório experimental · Davi Gomes Porfirio Brito e Carlos Trevia', LEGENDA), Spacer(1, 6)]
    c.append(P(
        'Implementamos em Python, para dois problemas, uma solução de força bruta e uma de divisão e conquista, '
        'mais a versão <b>O(n)</b> da questão desafio (algoritmo de Kadane) para o subarranjo de soma máxima. '
        'Verificamos experimentalmente se o tempo segue as recorrências previstas. Todos os números, tabelas e '
        'gráficos deste PDF saem da mesma execução de <font name="F-I">benchmark.py</font> '
        '(<font name="F-I">resultados/*.csv</font>); o PDF é gerado por <font name="F-I">gerar_relatorio.py</font>.'))

    # ---- 1 metodologia
    c.append(P('1. Metodologia e máquina', H1))
    maq = [['Item', 'Valor'], ['Processador', MAQUINA['Processador']],
           ['Núcleos lógicos / RAM', f"{MAQUINA['Núcleos lógicos']} / {MAQUINA['Memória RAM']}"],
           ['Sistema operacional', MAQUINA['Sistema operacional']], ['Python', MAQUINA['Python']]]
    c.append(tabela(maq, [4 * cm, 12.8 * cm], zebra=False, alinhamento='LEFT'))
    c.append(Spacer(1, 4))
    c.append(P(
        f'Tamanhos: {", ".join(str(n) for n in TAMANHOS)} (o enunciado pede até 6.400). <b>{REPS} repetições</b> por '
        'tamanho (mínimo exigido: 5), com uma entrada nova a cada repetição (semente 2026; vetores com inteiros em '
        '[-100, 100], pontos com coordenadas inteiras em [-10.000, 10.000]). Mede-se só a chamada do algoritmo, com '
        '<font name="F-I">perf_counter_ns</font>, coletor de lixo desligado durante a medição e processo com '
        'prioridade alta preso a um núcleo. O Kadane é rápido demais para um único disparo; cada medição dele é a '
        'média de várias chamadas seguidas. Como o ambiente é um notebook, há ruído: '
        f'para o par de pontos com n = {n_max}, a mesma configuração variou de {br(min(tempos_par_max), 1)} a '
        f'{br(max(tempos_par_max), 1)} ms entre repetições. Por isso as tabelas trazem a <b>média</b> (exigida) e a '
        '<b>mediana</b> (robusta a picos), e a escolha do limiar usa a mediana.'))

    # ---- 2 etapa 1
    c.append(P('2. Etapa 1 — Subarranjo de soma máxima', H1))
    c.append(P(
        '<b>Força bruta.</b> Dois laços aninhados com soma acumulada examinam os n(n+1)/2 intervalos; '
        'T(n) = Θ(n²), espaço O(1).'))
    c.append(P(
        '<b>Divisão e conquista.</b> Divide o vetor ao meio, resolve cada metade e calcula, em Θ(n), o melhor '
        'intervalo que cruza o meio (melhor sufixo da esquerda + melhor prefixo da direita); a resposta é o maior dos '
        'três. Recorrência: <b>T(n) = 2T(n/2) + Θ(n)</b>, com T(1) = Θ(1). Teorema mestre: '
        '<b>a = 2, b = 2, f(n) = Θ(n)</b>; n<super>log<sub>b</sub>a</super> = n<super>log<sub>2</sub>2</super> = n. Como '
        'f(n) = Θ(n<super>log<sub>b</sub>a</super>), vale o caso 2 e <b>T(n) = Θ(n log n)</b>. Espaço auxiliar '
        'O(log n) (pilha de recursão).'))
    c.append(P(
        '<b>Versão linear (desafio).</b> Kadane: um único laço mantém a melhor soma de um intervalo que termina na '
        'posição atual; <b>T(n) = T(n−1) + Θ(1) = Θ(n)</b> (recorrência por subtração: o teorema mestre não se '
        'aplica, pois não há divisão do problema), espaço O(1). Para obedecer à mesma regra de desempate das outras '
        'versões, só reinicia o intervalo quando a soma anterior é <i>negativa</i> (com soma 0, estender preserva o '
        'menor índice inicial) e só troca o melhor quando (−soma, início, fim) é estritamente menor.'))
    c.append(P(
        '<b>Convenções.</b> Índices inclusivos e base 0. Vetor só com negativos devolve o maior elemento, não 0 '
        '(intervalo vazio não é permitido). Empate: menor índice inicial e, depois, menor índice final.'))

    # ---- 3 etapa 2
    c.append(P('3. Etapa 2 — Par de pontos mais próximos', H1))
    c.append(P(
        '<b>Força bruta.</b> Compara os n(n−1)/2 pares: Θ(n²).'))
    c.append(P(
        '<b>Divisão e conquista.</b> Ordena os pontos por x e por y uma única vez (Θ(n log n)). Em cada chamada: '
        'divide por uma linha vertical na mediana de x (Θ(n)), particiona a lista ordenada por y entre as metades '
        '(Θ(n)), resolve as duas metades obtendo δ = min(δ<sub>E</sub>, δ<sub>D</sub>) e examina a faixa de largura '
        '2δ em torno da linha, comparando cada ponto com no máximo 7 sucessores na ordem de y (Θ(n)). '
        'Recorrência: <b>T(n) = 2T(n/2) + Θ(n)</b>; <b>a = 2, b = 2, f(n) = Θ(n)</b>, caso 2 do teorema mestre: '
        'Θ(n log n). Somada à ordenação inicial Θ(n log n), o total continua <b>Θ(n log n)</b>. Subproblemas '
        f'com até <i>limiar</i> pontos (padrão {LIMIAR_ESCOLHIDO}, Seção 7) usam força bruta.'))
    c.append(P('<b>Por que bastam 7 comparações por ponto na faixa.</b>', H2))
    prova = P(
        'Seja p um ponto da faixa e considere só os q com y<sub>q</sub> entre y<sub>p</sub> e y<sub>p</sub> + δ: '
        'qualquer outro q está a mais de δ de p na vertical e não melhora a resposta. Esses pontos ficam no '
        'retângulo 2δ × δ de x<sub>m</sub> − δ a x<sub>m</sub> + δ, acima de p. Dividimos o retângulo em <b>8 '
        'quadrados de lado δ/2</b> (4 colunas × 2 linhas); a linha mediana passa entre a 2ª e a 3ª coluna, então '
        'cada quadrado fica inteiro de um lado. Dois pontos do <i>mesmo lado</i> distam pelo menos δ (δ é o mínimo '
        'de cada metade), mas dois pontos no mesmo quadrado distam no máximo (δ/2)√2 = δ/√2 &lt; δ. Logo cada '
        'quadrado tem no máximo 1 ponto e o retângulo tem no máximo 8, contando o próprio p: restam <b>no máximo 7 '
        'sucessores</b> a comparar. Pontos sobre a linha pertencem à metade em que foram colocados e a contagem '
        'vale por metade (no máximo 4 pontos em cada retângulo δ × δ), então o limite de 8 se mantém; os casos '
        '<i>par_grade_6x6</i> e <i>par_mesmo_x_21</i> exercitam esse cenário.')
    c.append(prova)
    desenho = desenho_vizinhos()
    desenho.hAlign = 'CENTER'
    c.append(KeepTogether([desenho, P('Figura — Retângulo 2δ × δ acima de p dividido em 8 quadrados de lado δ/2; '
                                      'a linha tracejada é a mediana em x.', LEGENDA)]))

    # ---- 4 resultados soma
    cab = ['n', 'Bruta\nmédia', 'Bruta\nmediana', 'D&C\nmédia', 'D&C\nmediana', 'Kadane\nmédia', 'Kadane\nmediana',
           'Bruta / D&C\n(médias)']
    linhas = [cab]
    for n in TAMANHOS:
        linhas.append([str(n)] + [br(valor(MEDIAS, a, n, k), 4 if a == soma_l else 3)
                                  for a in (soma_b, soma_d, soma_l) for k in ('media_ms', 'mediana_ms')]
                      + [br(valor(MEDIAS, soma_b, n) / valor(MEDIAS, soma_d, n), 1) + '×'])
    c.append(KeepTogether([P('4. Resultados — Subarranjo de soma máxima', H1),
                           P('Tabela 1 — Soma máxima: tempo (ms), média e mediana de ' + f'{REPS} repetições.', LEGENDA),
                           tabela(linhas, [1.3 * cm] + [2.1 * cm] * 6 + [2.6 * cm]), Spacer(1, 4),
                           figura('grafico_soma.png', 16.6),
                           P('Figura 1 — Soma máxima (médias). Esquerda: escala linear. Direita: log-log com '
                             'referências n log n e n² ancoradas em n = 100; o Kadane está abaixo das demais.',
                             LEGENDA)]))

    # ---- 5 resultados par
    linhas = [['n', 'Bruto média', 'Bruto mediana', 'D&C média', 'D&C mediana', 'Bruto / D&C']]
    for n in TAMANHOS:
        linhas.append([str(n)] + [br(valor(MEDIAS, a, n, k), 3) for a in (par_b, par_d)
                                  for k in ('media_ms', 'mediana_ms')]
                      + [br(valor(MEDIAS, par_b, n) / valor(MEDIAS, par_d, n), 1) + '×'])
    c.append(KeepTogether([P('5. Resultados — Par de pontos mais próximos', H1),
                           P('Tabela 2 — Par mais próximo: tempo (ms), média e mediana.', LEGENDA),
                           tabela(linhas, [1.5 * cm] + [2.6 * cm] * 4 + [2.8 * cm]), Spacer(1, 4),
                           figura('grafico_par.png', 16.6),
                           P('Figura 2 — Par mais próximo (médias), mesma convenção da Figura 1.', LEGENDA)]))

    # ---- 6 discussão
    c.append(P('6. Discussão: observado × previsto', H1))
    esperado = {soma_b: ('2', '4,00'), soma_d: ('≈ 1,1 a 1,2', '2,2'), soma_l: ('1', '2,00'),
                par_b: ('2', '4,00'), par_d: ('≈ 1,1 a 1,2', '2,2')}
    nomes = {soma_b: 'Soma — força bruta', soma_d: 'Soma — divisão e conquista', soma_l: 'Soma — Kadane O(n)',
             par_b: 'Par — força bruta', par_d: 'Par — divisão e conquista'}
    linhas = [['Algoritmo', 'Expoente\n(média)', 'Expoente\n(mediana)', 'Esperado', 'Razão\nT(2n)/T(n)', 'Esperada']]
    for a in (soma_b, soma_d, soma_l, par_b, par_d):
        linhas.append([nomes[a], br(inclinacao(a, 'media_ms')), br(inclinacao(a, 'mediana_ms')), esperado[a][0],
                       br(razao_media(a)), esperado[a][1]])
    c.append(P('Tabela 3 — Expoente α de T ≈ c·n<super>α</super> (regressão log-log nos 7 tamanhos) e razão '
               'média ao dobrar n.', LEGENDA))
    c.append(tabela(linhas, [4.6 * cm, 2.4 * cm, 2.6 * cm, 2.4 * cm, 2.8 * cm, 2 * cm]))
    c.append(Spacer(1, 4))
    c.append(KeepTogether([figura('grafico_razao.png', 10.6),
                           P('Figura 3 — Razão T(n)/T(n/2) em cada dobra de n.', LEGENDA)]))
    sp_soma, sp_par = (valor(MEDIAS, soma_b, n_max) / valor(MEDIAS, soma_d, n_max),
                       valor(MEDIAS, par_b, n_max) / valor(MEDIAS, par_d, n_max))
    c.append(P(
        f'<b>n² contra n log n.</b> As duas forças brutas têm expoente {br(inclinacao(soma_b, "media_ms"))} e '
        f'{br(inclinacao(par_b, "media_ms"))} e razão média {br(razao_media(soma_b))} e {br(razao_media(par_b))}: '
        'quadrupla ao dobrar n, como previsto para Θ(n²). As versões de divisão e conquista têm expoentes '
        f'{br(inclinacao(soma_d, "media_ms"))} (soma) e {br(inclinacao(par_d, "media_ms"))} (par) e razões em '
        'torno de 2: crescimento quase linear, compatível com Θ(n log n), cuja razão esperada vai de 2,30 (100 → 200) '
        'a 2,17 (3.200 → 6.400). <b>Limitação honesta:</b> em apenas seis dobras de n, com ruído de notebook e '
        'sobrecarga do interpretador, os dados <i>não distinguem</i> n log n de n; o que eles mostram com clareza '
        'é o contraste com n² (razão ≈ 2 contra ≈ 4). O Kadane tem expoente '
        f'{br(inclinacao(soma_l, "media_ms"))} e razão {br(razao_media(soma_l))}, linear como previsto, e é '
        f'cerca de {br(mean(valor(MEDIAS, soma_d, n) / valor(MEDIAS, soma_l, n) for n in TAMANHOS), 0)}× mais rápido '
        'que a divisão e conquista em todos os tamanhos (diferença só de fator constante: recursão, fatiamento e '
        'comparações de tuplas). A vantagem da técnica sobre a força bruta cresce com n: '
        f'{br(valor(MEDIAS, soma_b, TAMANHOS[0]) / valor(MEDIAS, soma_d, TAMANHOS[0]), 1)}× em n = {TAMANHOS[0]} '
        f'e {br(sp_soma, 0)}× em n = {n_max} na soma; '
        f'{br(valor(MEDIAS, par_b, TAMANHOS[0]) / valor(MEDIAS, par_d, TAMANHOS[0]), 1)}× e {br(sp_par, 0)}× no '
        f'par. Em n = {n_max} a força bruta leva {br(valor(MEDIAS, soma_b, n_max) / 1000, 1)} s (soma) e '
        f'{br(valor(MEDIAS, par_b, n_max) / 1000, 1)} s (par), contra {br(valor(MEDIAS, soma_d, n_max), 0)} ms e '
        f'{br(valor(MEDIAS, par_d, n_max), 0)} ms.'))

    # ---- cruzamento
    ns = sorted({r['n'] for r in CRUZ})
    linhas = [['n', 'Soma: bruta', 'Soma: D&C', 'Soma: Kadane', 'Par: bruto', 'Par: D&C']]
    for n in ns:
        linhas.append([str(n)] + [br(valor(CRUZ, a, n), 4) for a in (soma_b, soma_d, soma_l, par_b, par_d)])
    c.append(KeepTogether([
        P('Quem vence em cada tamanho e o ponto de cruzamento', H2),
        P('Tabela 4 — Tamanhos pequenos: tempo médio (ms). A divisão e conquista usa recursão pura (subproblemas '
          'de até 3 pontos vão à força bruta).', LEGENDA),
        tabela(linhas, [1.4 * cm] + [3 * cm] * 5), Spacer(1, 4), figura('grafico_cruzamento.png', 15.2),
        P('Figura 4 — Cruzamento entre força bruta e divisão e conquista (log-log).', LEGENDA)]))
    c.append(P(
        f'Para tamanhos pequenos a <b>força bruta vence</b>: na soma, até n = {ns[ns.index(cruz_soma) - 1]}; '
        f'no par, até n = {ns[ns.index(cruz_par) - 1]}. O cruzamento ocorre entre n = '
        f'{ns[ns.index(cruz_soma) - 1]} e {cruz_soma} na soma e entre n = {ns[ns.index(cruz_par) - 1]} e '
        f'{cruz_par} no par. Abaixo disso o custo é dominado por constantes (chamadas recursivas, fatiamento, '
        'ordenações, conjuntos de identificadores no par) enquanto n² ainda é pequeno. Acima, n² cresce mais '
        'depressa que n log n e a diferença só aumenta. O Kadane vence os dois desde o menor tamanho medido, '
        'porque faz uma passada simples sem recursão. O cruzamento do par (≈ 8 a 16 pontos) é a base prática do '
        'limiar da próxima seção.'))

    # ---- 7 limiar
    c.append(P('7. Limiar da Etapa 2', H1))
    ns_lim = sorted({r['n'] for r in LIMIAR})
    linhas = [['Limiar'] + [f'mediana n={n} (ms)' for n in ns_lim] + ['Pontuação']]
    for L in sorted(PONTUACAO):
        linhas.append([str(L)] + [br(next(r['mediana_ms'] for r in LIMIAR if r['limiar'] == L and r['n'] == n), 2)
                                  for n in ns_lim] + [br(PONTUACAO[L], 3) + ('  ← escolhido' if L == LIMIAR_ESCOLHIDO
                                                                               else '')])
    c.append(P('Tabela 5 — Varredura do limiar: mesma entrada para todos os limiares em cada repetição. '
               'Pontuação = mediana / melhor mediana entre os limiares, média entre os tamanhos (1,000 = melhor).',
               LEGENDA))
    c.append(tabela(linhas, [1.8 * cm] + [3.4 * cm] * len(ns_lim) + [4 * cm]))
    c.append(Spacer(1, 4))
    c.append(KeepTogether([figura('grafico_limiar.png', 10.6),
                           P('Figura 5 — Tempo relativo ao melhor limiar, por tamanho de entrada.', LEGENDA)]))
    pont_16 = PONTUACAO.get(16, float('nan'))
    c.append(P(
        f'<b>Escolha: limiar {LIMIAR_ESCOLHIDO}.</b> É o de menor pontuação nos três tamanhos testados. Os limiares '
        f'4 e 8 empatam (diferença de {br((PONTUACAO[4] / PONTUACAO[8] - 1) * 100, 1)}%, dentro do ruído); '
        f'o 2 é {br((PONTUACAO[2] / PONTUACAO[8] - 1) * 100, 0)}% pior e o 16, valor que usávamos antes sem '
        f'calibrar, é {br((pont_16 / PONTUACAO[8] - 1) * 100, 0)}% pior, o que mostra que não era ótimo. '
        f'A partir de 32 o custo sobe depressa ({br(PONTUACAO[32], 2)}× e {br(PONTUACAO[64], 2)}× o melhor). A '
        'forma da curva tem explicação: cada folha de L pontos custa ≈ c<sub>1</sub>·L² e há n/L folhas, logo as '
        'folhas somam ≈ c<sub>1</sub>·n·L (cresce com L); já a sobrecarga da recursão (≈ c<sub>2</sub> por '
        'chamada, n/L chamadas) diminui com L. O mínimo fica onde as duas se equilibram, perto de '
        'L* ≈ √(c<sub>2</sub>/c<sub>1</sub>), e a curva é plana ao redor dele. Isso '
        f'concorda com a Tabela 4, em que a força bruta ainda vence até ≈ {ns[ns.index(cruz_par) - 1]} pontos. '
        'Os limiares 2 e 3 são equivalentes na implementação (com n ≤ 3 dividir geraria uma metade de 1 ponto, '
        'sem par). O valor ótimo depende da máquina e do interpretador; o <font name="F-I">benchmark.py</font> '
        'refaz a escolha e avisa se o padrão de <font name="F-I">algoritmos.py</font> divergir.'))

    # ---- 8 testes
    n_soma, n_par = len(CASOS_JSON['soma_maxima']), len(CASOS_JSON['par_mais_proximo'])
    c.append(P('8. Testes e casos de borda', H1))
    c.append(P(
        f'<font name="F-I">tests/casos_teste.json</font> reúne {n_soma + n_par} casos ({n_soma} de soma máxima, '
        f'{n_par} de par de pontos) com entrada, saída esperada e justificativa; cada saída foi derivada à mão e '
        'conferida com a força bruta. Eles rodam em todas as implementações e, no par, em todos os limiares '
        '(2 a 64), e também pelo CLI (<font name="F-I">main.py</font>, entrada por stdin). Além disso há testes '
        'aleatórios com semente fixa que comparam as versões; na soma, valores em [−2, 2] forçam muitos empates.'))
    borda = [
        ['Caso de borda', 'Por que importa'],
        [P('Só negativos; negativos iguais', CELULA), P('A resposta é o maior elemento, não 0; ensina que o intervalo '
                                                     'vazio é proibido e que o desempate vale entre elementos iguais.', CELULA)],
        [P('n = 1 (positivo, negativo, zero)', CELULA), P('Caso base da recursão e do laço; índices (0, 0).', CELULA)],
        [P('Empates: simples, vários intervalos, alternado, cruzando o meio', CELULA),
         P('Verificam a regra menor início → menor fim e a combinação esquerda/direita/cruzado (ex.: [2,2,−4,4] → '
           '(4,0,1)).', CELULA)],
        [P('Todos zeros; zeros entre negativos; zero antes do máximo', CELULA),
         P('Todos os intervalos empatam; o Kadane precisa estender com soma 0 para preservar o menor início.', CELULA)],
        [P('Pontos coincidentes; 45 pontos em 3 posições', CELULA),
         P('Distância 0, vários pares empatados e faixa lotada de pontos iguais.', CELULA)],
        [P('Colineares: mesmo y, mesmo x, diagonal', CELULA),
         P('Faixa degenerada (todos na faixa ou todos em uma linha) e empate de raiz de 2 na diagonal.', CELULA)],
        [P('Grade 6×6; 21 pontos com mesmo x', CELULA),
         P('Dezenas de pares empatados e linha mediana cheia de pontos (valida o limite de 7 vizinhos).', CELULA)],
        [P('Par que cruza a mediana (n = 20 > limiar)', CELULA),
         P('Só a combinação na faixa encontra o melhor par; as metades isoladas não.', CELULA)],
        [P('Limiares 2, 3, 4, 8, 16, 32, 64', CELULA),
         P('O resultado não pode depender do limiar; achou um defeito real com limiar 2 (subproblema de 1 ponto), '
           'já corrigido.', CELULA)],
    ]
    t = tabela(borda, [5.6 * cm, 11.2 * cm], zebra=True)
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    c.append(t)

    # ---- 9 conclusão
    c.append(P('9. Conclusões, limitações e reprodução', H1))
    c.append(P(
        'As recorrências T(n) = 2T(n/2) + Θ(n) (a = 2, b = 2, f(n) = Θ(n), caso 2) valem nos dois problemas e a '
        'força bruta quadrática é muito superada a partir de algumas dezenas de elementos; o Kadane é o melhor '
        'para a soma máxima. Limitações: medições em um único notebook, com ruído; faixa de apenas 64× em n, que '
        'separa n² de n log n mas não n log n de n; o limiar ótimo depende de máquina e linguagem. '
        'Reprodução: <font name="F-I">python -m unittest discover -s tests</font>, '
        '<font name="F-I">python benchmark.py</font> e <font name="F-I">python gerar_relatorio.py</font>.'))
    return c


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont('F', 7.5)
    canvas.setFillColor(colors.HexColor('#666666'))
    canvas.drawString(2 * cm, 1.1 * cm, 'Divisão e Conquista — relatório experimental')
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f'Página {doc.page}')
    canvas.restoreState()


def main():
    doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title='Trabalho Prático: Divisão e Conquista',
                            author='Davi Gomes Porfirio Brito e Carlos Trevia')
    doc.build(construir(), onFirstPage=rodape, onLaterPages=rodape)
    print('Relatório gravado em', SAIDA)


if __name__ == '__main__':
    main()
