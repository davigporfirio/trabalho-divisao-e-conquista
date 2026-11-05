"""Executa todos os casos de tests/casos_teste.json em todas as implementações."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from algoritmos import (soma_maxima_bruta, soma_maxima_divisao, soma_maxima_linear,
                        par_mais_proximo_bruto, par_mais_proximo_divisao)

CASOS = json.loads((Path(__file__).parent / 'casos_teste.json').read_text(encoding='utf-8'))
SOMAS = (soma_maxima_bruta, soma_maxima_divisao, soma_maxima_linear)
PARES = (par_mais_proximo_bruto, par_mais_proximo_divisao)
LIMIARES = (2, 3, 4, 8, 16, 32, 64)


class TestCasosJson(unittest.TestCase):
    def test_soma_maxima(self):
        for caso in CASOS['soma_maxima']:
            for func in SOMAS:
                with self.subTest(caso=caso['id'], func=func.__name__):
                    self.assertEqual(list(func(caso['entrada'])), caso['saida'])

    def test_par_mais_proximo(self):
        for caso in CASOS['par_mais_proximo']:
            pontos = [tuple(p) for p in caso['entrada']]
            esperado = caso['saida']
            for func in PARES:
                with self.subTest(caso=caso['id'], func=func.__name__):
                    dist, p, q = func(pontos)
                    self.assertAlmostEqual(dist, esperado['distancia'])
                    self.assertEqual((list(p), list(q)), (esperado['ponto1'], esperado['ponto2']))

    def test_par_mais_proximo_com_todos_os_limiares(self):
        # O resultado não pode depender do limiar da força bruta.
        for caso in CASOS['par_mais_proximo']:
            pontos = [tuple(p) for p in caso['entrada']]
            esperado = caso['saida']
            for limiar in LIMIARES:
                with self.subTest(caso=caso['id'], limiar=limiar):
                    dist, p, q = par_mais_proximo_divisao(pontos, limiar=limiar)
                    self.assertAlmostEqual(dist, esperado['distancia'])
                    self.assertEqual((list(p), list(q)), (esperado['ponto1'], esperado['ponto2']))

    def test_todos_os_casos_tem_justificativa(self):
        for grupo in ('soma_maxima', 'par_mais_proximo'):
            for caso in CASOS[grupo]:
                self.assertTrue(caso['justificativa'].strip(), caso['id'])


if __name__ == '__main__':
    unittest.main()
