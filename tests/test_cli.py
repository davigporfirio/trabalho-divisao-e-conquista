"""Testa a interface de linha de comando (main.py) com stdin/stdout reais."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CASOS = json.loads((Path(__file__).parent / 'casos_teste.json').read_text(encoding='utf-8'))


def executar(*args, entrada=''):
    return subprocess.run([sys.executable, str(RAIZ / 'main.py'), *args], input=entrada,
                          capture_output=True, text=True, encoding='utf-8')


class TestCli(unittest.TestCase):
    def test_exemplo_soma(self):
        r = executar('soma', entrada='3\n-5 -2 -7\n')
        self.assertEqual((r.returncode, r.stdout.strip()), (0, '-2 1 1'))

    def test_exemplo_pontos(self):
        r = executar('pontos', entrada='2\n0 0\n3 4\n')
        self.assertEqual((r.returncode, r.stdout.strip()), (0, '5.000000 0 0 3 4'))

    def test_soma_casos_json_em_todos_os_algoritmos(self):
        for caso in CASOS['soma_maxima']:
            entrada = f"{len(caso['entrada'])}\n" + ' '.join(map(str, caso['entrada'])) + '\n'
            esperado = ' '.join(map(str, caso['saida']))
            for algoritmo in ('bruta', 'divisao', 'linear'):
                with self.subTest(caso=caso['id'], algoritmo=algoritmo):
                    r = executar('soma', '--algoritmo', algoritmo, entrada=entrada)
                    self.assertEqual(r.stdout.strip(), esperado)

    def test_pontos_casos_json_em_todos_os_algoritmos(self):
        for caso in CASOS['par_mais_proximo']:
            entrada = f"{len(caso['entrada'])}\n" + ''.join(f'{x} {y}\n' for x, y in caso['entrada'])
            s = caso['saida']
            esperado = f"{s['distancia']:.6f} {s['ponto1'][0]} {s['ponto1'][1]} {s['ponto2'][0]} {s['ponto2'][1]}"
            for algoritmo in ('bruto', 'divisao'):
                with self.subTest(caso=caso['id'], algoritmo=algoritmo):
                    r = executar('pontos', '--algoritmo', algoritmo, entrada=entrada)
                    self.assertEqual(r.stdout.strip(), esperado)

    def test_entrada_invalida_retorna_erro(self):
        for problema, entrada in (('soma', ''), ('soma', '0\n'), ('soma', '3\n1 2\n'), ('soma', 'x 1\n'),
                                  ('pontos', '1\n0 0\n'), ('pontos', '2\n0 0 1\n')):
            with self.subTest(problema=problema, entrada=entrada):
                r = executar(problema, entrada=entrada)
                self.assertEqual(r.returncode, 1)
                self.assertTrue(r.stderr.startswith('erro:'))


if __name__ == '__main__':
    unittest.main()
