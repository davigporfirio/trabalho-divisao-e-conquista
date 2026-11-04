# Trabalho Prático: Divisão e Conquista

**Alunos:** Davi Gomes Porfirio Brito e Carlos Trevia

Implementação em Python dos problemas descritos no relatório experimental:

- **Subarranjo de soma máxima:** força bruta `O(n²)` e divisão e conquista `O(n log n)`; retorno `(soma, índice_inicial, índice_final)`, índices inclusivos iniciados em zero. Em empate, menor índice inicial e depois menor índice final.
- **Par de pontos mais próximos:** força bruta `O(n²)` e divisão e conquista `O(n log n)`; retorno `(distância, ponto1, ponto2)`. A solução eficiente pré-ordena por x e y e verifica até sete sucessores na faixa. Limiar inicial de força bruta: 16, sem alegação de que seja ótimo.

## Executar

Requer Python 3.10+; não há dependências para os algoritmos e testes.

```bash
python -m unittest discover -s tests -v
python benchmark.py
```

Para gerar também os gráficos PNG:

```bash
python -m pip install matplotlib
python benchmark.py
```

Os arquivos de saída são criados em `resultados/`: `medicoes.csv`, `medias.csv`, `maquina.txt`, `grafico_soma.png` e `grafico_par.png` (os gráficos exigem matplotlib).

## Organização

- `algoritmos.py`: implementações dos quatro algoritmos.
- `tests/test_algoritmos.py`: testes, incluindo casos-limite e comparação aleatória com semente fixa.
- `benchmark.py`: tempos com `perf_counter_ns`, seis tamanhos, cinco repetições e semente 2026.
- `relatorio.pdf`: relatório da atividade.

**Observação:** os tempos de `benchmark.py` são novas medições realizadas no computador que executá-lo, não os tempos originais do relatório. A questão desafio que menciona `O(n)` não foi implementada porque o enunciado não consta no relatório.
