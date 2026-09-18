"""Tests de la extracción de código.

Lo que se guarda en vida.py tiene que ser exactamente lo que dijo el
modelo: la rúbrica compara ese archivo contra el texto del log.

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extraccion import extraer_codigo, parece_script_python  # noqa: E402

SCRIPT = "import sys\n\n\ndef main():\n    print('hola')\n"


class TestExtraerCodigo(unittest.TestCase):

    def test_sin_vallas_devuelve_el_texto_tal_cual(self):
        self.assertEqual(extraer_codigo(SCRIPT).strip(), SCRIPT.strip())

    def test_saca_las_vallas_de_markdown(self):
        respuesta = f"```python\n{SCRIPT}```"
        self.assertEqual(extraer_codigo(respuesta).strip(), SCRIPT.strip())

    def test_saca_vallas_sin_lenguaje(self):
        respuesta = f"```\n{SCRIPT}```"
        self.assertEqual(extraer_codigo(respuesta).strip(), SCRIPT.strip())

    def test_ignora_el_texto_que_rodea_al_bloque(self):
        respuesta = f"Acá va el script:\n\n```python\n{SCRIPT}```\n\nEspero que sirva."
        extraido = extraer_codigo(respuesta)
        self.assertNotIn("Espero que sirva", extraido)
        self.assertIn("def main", extraido)

    def test_se_queda_con_el_primer_bloque_si_hay_varios(self):
        respuesta = f"```python\n{SCRIPT}```\n\nY un ejemplo:\n\n```\n./vida.py x 3\n```"
        self.assertIn("def main", extraer_codigo(respuesta))
        self.assertNotIn("./vida.py x 3", extraer_codigo(respuesta))

    def test_no_reformatea_el_codigo(self):
        raro = "import sys\nx    =   1\n\n\n\nprint( x )\n"
        self.assertEqual(extraer_codigo(f"```python\n{raro}```").strip(),
                         raro.strip())

    def test_termina_en_salto_de_linea(self):
        self.assertTrue(extraer_codigo(f"```python\n{SCRIPT}```").endswith("\n"))

    def test_texto_vacio_devuelve_vacio(self):
        self.assertEqual(extraer_codigo(""), "")
        self.assertEqual(extraer_codigo(None), "")


class TestPareceScriptPython(unittest.TestCase):

    def test_reconoce_un_script(self):
        self.assertTrue(parece_script_python(SCRIPT))

    def test_rechaza_una_disculpa_del_modelo(self):
        self.assertFalse(parece_script_python(
            "Perdón, no puedo ayudarte con eso."))

    def test_rechaza_el_vacio(self):
        self.assertFalse(parece_script_python("   "))


if __name__ == "__main__":
    unittest.main(verbosity=2)
