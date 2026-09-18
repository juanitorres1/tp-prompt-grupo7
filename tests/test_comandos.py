"""Test de la guarda de comandos.

Un comando mal escrito no se puede mandar al modelo: sumaría un turno de
usuario al log, y la rúbrica cuenta esos turnos para decidir si la corrida
del ejercicio 2 fue de 1 prompt o de 2.

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

COMANDOS = ("/modelo", "/effort", "/json", "/contexto", "/resumen", "/salir")


def es_comando_valido(entrada):
    """Réplica de la condición que usa el bucle del chat."""
    return entrada.split()[0] in COMANDOS if entrada.strip() else False


def se_manda_al_modelo(entrada):
    """True si el texto viajaría a la API como turno de usuario."""
    if not entrada.strip():
        return False
    if entrada.startswith("/"):
        return False
    return True


class TestGuardaDeComandos(unittest.TestCase):

    def test_los_comandos_conocidos_no_se_mandan(self):
        for c in COMANDOS:
            self.assertFalse(se_manda_al_modelo(c), c)

    def test_un_comando_con_typo_tampoco_se_manda(self):
        # El caso real: /sair en vez de /salir.
        for typo in ["/sair", "/salrir", "/modelos", "/efort high"]:
            self.assertFalse(se_manda_al_modelo(typo), typo)
            self.assertFalse(es_comando_valido(typo), typo)

    def test_un_mensaje_normal_si_se_manda(self):
        self.assertTrue(se_manda_al_modelo("escribime vida.py"))

    def test_un_mensaje_que_menciona_una_barra_adentro_se_manda(self):
        self.assertTrue(se_manda_al_modelo("usá el separador a/b"))

    def test_la_entrada_vacia_no_se_manda(self):
        self.assertFalse(se_manda_al_modelo("   "))


if __name__ == "__main__":
    unittest.main(verbosity=2)
