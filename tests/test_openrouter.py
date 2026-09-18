"""Tests del cliente de OpenRouter.

No tocan la red: prueban las funciones puras que interpretan lo que
devuelve la API. Son las que tienen que andar bien para que el usage que
se muestra y el que va al informe sean el mismo número.

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import openrouter  # noqa: E402


RESPUESTA_COMPLETA = {
    "choices": [{"message": {"content": "hola"}}],
    "usage": {
        "prompt_tokens": 1200,
        "completion_tokens": 300,
        "cost": 0.00042,
        "cache_discount": 0.0001,
        "prompt_tokens_details": {"cached_tokens": 1024},
        "completion_tokens_details": {"reasoning_tokens": 250},
    },
}

# Varios modelos no informan razonamiento ni cacheados. La interfaz igual
# tiene que poder mostrar los cinco campos.
RESPUESTA_MINIMA = {
    "choices": [{"message": {"content": "hola"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.000001},
}


class TestExtraerUsage(unittest.TestCase):

    def test_lee_los_seis_campos_cuando_estan_todos(self):
        uso = openrouter.extraer_usage(RESPUESTA_COMPLETA)
        self.assertEqual(uso["entrada"], 1200)
        self.assertEqual(uso["salida"], 300)
        self.assertEqual(uso["razonamiento"], 250)
        self.assertEqual(uso["cacheados"], 1024)
        self.assertAlmostEqual(uso["costo"], 0.00042)
        self.assertAlmostEqual(uso["descuento_cache"], 0.0001)

    def test_completa_con_cero_lo_que_el_proveedor_no_informa(self):
        uso = openrouter.extraer_usage(RESPUESTA_MINIMA)
        self.assertEqual(uso["razonamiento"], 0)
        self.assertEqual(uso["cacheados"], 0)
        self.assertEqual(uso["descuento_cache"], 0.0)

    def test_respuesta_sin_usage_no_rompe(self):
        uso = openrouter.extraer_usage({"choices": []})
        self.assertEqual(uso["entrada"], 0)
        self.assertEqual(uso["costo"], 0.0)

    def test_respuesta_vacia_no_rompe(self):
        self.assertEqual(openrouter.extraer_usage(None)["entrada"], 0)


class TestFormatearUsage(unittest.TestCase):

    def test_muestra_los_cinco_numeros_que_pide_la_consigna(self):
        linea = openrouter.formatear_usage(
            openrouter.extraer_usage(RESPUESTA_COMPLETA))
        for esperado in ["entrada 1200", "salida 300", "razonamiento 250",
                         "cacheados 1024", "$0.000420"]:
            self.assertIn(esperado, linea)


class TestAhorroPorCache(unittest.TestCase):

    def test_usa_el_descuento_que_informa_la_api_si_viene(self):
        uso = openrouter.extraer_usage(RESPUESTA_COMPLETA)
        ahorro = openrouter.ahorro_por_cache(uso, openrouter.MODELOS["2"])
        self.assertAlmostEqual(ahorro, 0.0001)

    def test_lo_estima_con_los_precios_cuando_la_api_no_lo_informa(self):
        uso = {"cacheados": 1_000_000, "descuento_cache": 0.0}
        # Haiku: entrada $1.00/M contra lectura de cache $0.10/M -> ahorra $0.90
        ahorro = openrouter.ahorro_por_cache(uso, openrouter.MODELOS["2"])
        self.assertAlmostEqual(ahorro, 0.90)

    def test_sin_tokens_cacheados_el_ahorro_es_cero(self):
        uso = {"cacheados": 0, "descuento_cache": 0.0}
        self.assertEqual(
            openrouter.ahorro_por_cache(uso, openrouter.MODELOS["4"]), 0.0)


class TestTextoDe(unittest.TestCase):

    def test_devuelve_el_contenido_del_primer_choice(self):
        self.assertEqual(openrouter.texto_de(RESPUESTA_COMPLETA), "hola")

    def test_sin_choices_devuelve_cadena_vacia(self):
        self.assertEqual(openrouter.texto_de({"choices": []}), "")


class TestCatalogoDeModelos(unittest.TestCase):

    def test_hay_cuatro_slots_de_cuatro_proveedores_distintos(self):
        self.assertEqual(len(openrouter.MODELOS), 4)
        proveedores = {m["proveedor"] for m in openrouter.MODELOS.values()}
        self.assertEqual(len(proveedores), 4)

    def test_el_slot_4_es_mucho_mas_barato_que_el_slot_2(self):
        # La consigna lo pide como "el escalón barato".
        caro = openrouter.MODELOS["2"]["precio_entrada"]
        barato = openrouter.MODELOS["4"]["precio_entrada"]
        self.assertGreater(caro / barato, 15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
