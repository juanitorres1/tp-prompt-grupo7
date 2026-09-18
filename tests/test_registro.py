"""Tests del registro de conversaciones.

El log es la evidencia de auditoría: la misión dice que una corrida sin
log no cuenta. Estos tests fijan lo que el archivo tiene que contener.

    python -m unittest discover -s tests -v
"""
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import registro  # noqa: E402

MODELO = {
    "id": "anthropic/claude-haiku-4.5",
    "nombre": "Claude Haiku 4.5",
    "proveedor": "Anthropic",
    "capacidad": "prompt caching explícito",
}

USO = {"entrada": 1200, "salida": 300, "razonamiento": 250,
       "cacheados": 1024, "costo": 0.00042, "descuento_cache": 0.0}


class TestNombreArchivo(unittest.TestCase):

    def test_lleva_fecha_slot_y_modelo(self):
        nombre = registro.nombre_archivo(
            2, "anthropic/claude-haiku-4.5", datetime(2026, 9, 18, 19, 30))
        self.assertEqual(
            nombre, "2026-09-18_1930-slot2-anthropic-claude-haiku-4.5.md")

    def test_la_barra_del_id_no_rompe_el_nombre(self):
        nombre = registro.nombre_archivo(1, "openai/gpt-5.6-luna")
        self.assertNotIn("/", nombre)
        self.assertTrue(nombre.endswith(".md"))


class TestBloqueTurno(unittest.TestCase):

    def test_el_turno_del_usuario_no_lleva_tabla_de_usage(self):
        bloque = registro.bloque_turno("user", "hola")
        self.assertIn("hola", bloque)
        self.assertNotIn("usage", bloque)

    def test_la_respuesta_lleva_los_cinco_numeros(self):
        bloque = registro.bloque_turno("assistant", "hola", USO)
        for n in ["1200", "300", "250", "1024", "0.000420"]:
            self.assertIn(n, bloque)


class TestConversacion(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conv = registro.Conversacion(self.tmp.name, 2, MODELO)

    def tearDown(self):
        self.tmp.cleanup()

    def _contenido(self):
        return self.conv.ruta.read_text(encoding="utf-8")

    def test_el_encabezado_identifica_modelo_y_proveedor(self):
        texto = self._contenido()
        self.assertIn("anthropic/claude-haiku-4.5", texto)
        self.assertIn("Anthropic", texto)

    def test_cuenta_los_prompts_del_usuario(self):
        self.conv.anotar("user", "uno")
        self.conv.anotar("assistant", "respuesta", USO)
        self.conv.anotar("user", "dos")
        self.conv.anotar("assistant", "respuesta", USO)
        # Es el número que mira la rúbrica para saber si fue "1 prompt".
        self.assertEqual(self.conv.turnos, 2)

    def test_acumula_los_totales_de_todas_las_respuestas(self):
        self.conv.anotar("assistant", "a", USO)
        self.conv.anotar("assistant", "b", USO)
        self.assertEqual(self.conv.totales["entrada"], 2400)
        self.assertEqual(self.conv.totales["cacheados"], 2048)
        self.assertAlmostEqual(self.conv.totales["costo"], 0.00084)

    def test_registra_los_parametros_usados_en_el_turno(self):
        self.conv.anotar("user", "hola", parametros="reasoning.effort=high")
        self.assertIn("reasoning.effort=high", self._contenido())

    def test_cerrar_escribe_el_total_al_pie(self):
        self.conv.anotar("user", "uno")
        self.conv.anotar("assistant", "dos", USO)
        self.conv.cerrar()
        texto = self._contenido()
        self.assertIn("Total de la conversación", texto)
        self.assertIn("Prompts del usuario: **1**", texto)

    def test_el_log_se_escribe_turno_a_turno_no_al_final(self):
        # Si el proceso se cae a la mitad, lo que ya pasó tiene que estar.
        self.conv.anotar("user", "sobrevivo")
        self.assertIn("sobrevivo", self._contenido())


if __name__ == "__main__":
    unittest.main(verbosity=2)
