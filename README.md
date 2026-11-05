# Trabalho Prático: Divisão e Conquista

**Alunos:** Davi Gomes Porfirio Brito e Carlos Trevia

Comparação experimental entre força bruta e divisão e conquista em dois problemas, com a versão O(n) da questão desafio. Python 3.10+; os algoritmos, o CLI e os testes não têm dependências.

## Algoritmos

| Problema | Algoritmo | Complexidade | Função em `algoritmos.py` |
|---|---|---|---|
| Subarranjo de soma máxima | Força bruta | O(n²) | `soma_maxima_bruta` |
| | Divisão e conquista (T(n) = 2T(n/2) + O(n)) | O(n log n) | `soma_maxima_divisao` |
| | **Kadane (questão desafio)** | **O(n)** | `soma_maxima_linear` |
| Par de pontos mais próximos | Força bruta | O(n²) | `par_mais_proximo_bruto` |
| | Divisão e conquista (faixa 2δ, até 7 vizinhos) | O(n log n) | `par_mais_proximo_divisao` |

Convenções:

- **Soma máxima:** retorna `(soma, início, fim)` com índices inclusivos e base 0. Vetor só com negativos devolve o maior elemento. Empate: menor início e, depois, menor fim. As três versões seguem a mesma regra.
- **Par mais próximo:** retorna `(distância, ponto1, ponto2)` com `ponto1 <= ponto2`. Empate: menor `(distância, ponto1, ponto2)`. Pontos repetidos valem distância 0.
- **Limiar:** subproblemas com até `limiar` pontos usam força bruta. O padrão é **8**, escolhido pelo experimento de limiares (veja o relatório, seção 7).

## Executar

Testes:

```bash
python -m unittest discover -s tests -v
```

CLI (lê a entrada padrão):

```bash
echo "3 -5 -2 -7" | python main.py soma
printf "2\n0 0\n3 4\n" | python main.py pontos
```

| Comando | Entrada | Saída |
|---|---|---|
| `python main.py soma [--algoritmo bruta\|divisao\|linear]` | `n` e depois `n` inteiros | `soma início fim` |
| `python main.py pontos [--algoritmo bruto\|divisao]` | `n` e depois `n` linhas `x y` | `distância x1 y1 x2 y2` (6 casas decimais) |

Em caso de entrada inválida, o CLI escreve `erro: ...` em stderr e sai com código 1. Sem `--algoritmo`, usa divisão e conquista.

Benchmark e relatório (precisam de `pip install -r requirements.txt`):

```bash
python benchmark.py             # medições completas (10 a 15 min)
python benchmark.py --rapido    # teste rápido, grava em resultados_rapido/
python benchmark.py --regerar   # refaz tabelas e gráficos a partir dos CSVs
python gerar_relatorio.py       # monta relatorio.pdf a partir de resultados/
```

## Estrutura

```text
algoritmos.py            implementações
main.py                  CLI (stdin/stdout)
benchmark.py             único gerador de CSVs, tabelas e gráficos
gerar_relatorio.py       monta o PDF lendo os CSVs
relatorio.pdf            relatório (5 páginas)
tests/
  casos_teste.json       30 casos: entrada, saída esperada e justificativa
  test_algoritmos.py     casos de borda e comparação aleatória com semente fixa
  test_casos_json.py     roda o JSON em todas as versões e em vários limiares
  test_cli.py            testa o CLI com stdin/stdout reais
resultados/
  medicoes.csv           medições brutas (algoritmo, n, repetição, tempo em ms)
  medias.csv             média, mediana, desvio e mínimo por algoritmo e n
  limiar_medicoes.csv    medições da varredura de limiar
  limiar_medias.csv      médias da varredura de limiar
  limiar_escolhido.txt   limiar escolhido e pontuação de cada candidato
  cruzamento.csv         tamanhos pequenos (ponto de cruzamento)
  maquina.txt            CPU, RAM, sistema e versão do Python
  tabelas.md             tabelas em Markdown
  grafico_*.png          gráficos usados no relatório
```

## Metodologia

7 tamanhos (100 a 6.400, dobrando), 10 repetições por tamanho (o enunciado pede no mínimo 5), entrada nova a cada repetição, semente 2026. Mede só a chamada do algoritmo com `perf_counter_ns`, com coletor de lixo desligado. O processo roda com prioridade alta e preso a um núcleo. `maquina.txt` registra a configuração (Intel Core i7-8565U, 7,8 GB de RAM, Windows 11, Python 3.14.7).

Resumo: a força bruta tem expoente ≈ 1,97 a 1,98 nos dois problemas (quadrática). A divisão e conquista tem expoente entre 0,99 e 1,08, compatível com n log n, mas os dados não separam n log n de n. O Kadane fica em ≈ 0,94. Em n = 6.400 a força bruta leva 21,4 s (soma) e 16,7 s (par), contra 31 ms e 71 ms da divisão e conquista. Os números completos e a discussão estão em `relatorio.pdf`.

## Casos de teste

`tests/casos_teste.json` cobre: vetor só com negativos, n = 1, empates com vários intervalos, todos zeros, pontos colineares (mesmo x, mesmo y e diagonal), grade com muitos empates, muitos pontos duplicados e par que cruza a linha mediana. Cada caso traz a justificativa no próprio arquivo.

## Histórico

O código-base entrou no repositório por upload em 04/11/2026, em poucos commits. O trabalho posterior (reorganização, Kadane, casos de borda, benchmark, CLI, relatório e README) vive em uma branch por etapa, com commits pequenos e mensagens descritivas:

| Branch | Conteúdo |
|---|---|
| `feat/01-estrutura-repo` | `tests/` e `resultados/`; remove zip e PDF duplicado |
| `feat/02-soma-linear-kadane` | `soma_maxima_linear` e testes |
| `feat/03-casos-teste-borda` | `casos_teste.json`, testes por caso e correção do limiar 2 |
| `feat/04-benchmark-limiar` | benchmark único, n = 6.400, varredura de limiares, limiar 8 |
| `feat/05-cli` | `main.py` e `tests/test_cli.py` |
| `feat/06-relatorio` | `gerar_relatorio.py` e novo `relatorio.pdf` |
| `feat/07-readme` | este README e `requirements.txt` |
