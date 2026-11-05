import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from algoritmos import (soma_maxima_bruta, soma_maxima_divisao,
                        par_mais_proximo_bruto, par_mais_proximo_divisao)


class TestAlgoritmos(unittest.TestCase):
    def test_soma_negativos(self):
        self.assertEqual(soma_maxima_divisao([-5, -2, -7]), (-2, 1, 1))

    def test_soma_unico(self):
        self.assertEqual(soma_maxima_divisao([9]), (9, 0, 0))

    def test_soma_empate(self):
        self.assertEqual(soma_maxima_divisao([1, -1, 1]), (1, 0, 0))

    def test_soma_invalida(self):
        for func in (soma_maxima_bruta, soma_maxima_divisao):
            with self.assertRaises(ValueError):
                func([])

    def test_pontos_coincidentes(self):
        self.assertEqual(par_mais_proximo_divisao([(1, 2), (1, 2), (4, 5)])[0], 0)

    def test_pontos_dois(self):
        self.assertEqual(par_mais_proximo_divisao([(0, 0), (3, 4)])[0], 5)

    def test_pontos_invalidos(self):
        with self.assertRaises(ValueError):
            par_mais_proximo_divisao([(1, 2)])

    def test_soma_aleatoria(self):
        rng = random.Random(2026)
        for n in range(1, 80):
            for _ in range(5):
                v = [rng.randint(-30, 30) for _ in range(n)]
                self.assertEqual(soma_maxima_bruta(v), soma_maxima_divisao(v))

    def test_pontos_aleatorios(self):
        rng = random.Random(2026)
        for n in range(2, 80):
            for _ in range(5):
                pontos = [(rng.randint(-50, 50), rng.randint(-50, 50)) for _ in range(n)]
                self.assertEqual(par_mais_proximo_bruto(pontos), par_mais_proximo_divisao(pontos))


if __name__ == '__main__':
    unittest.main()
