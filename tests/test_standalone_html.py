import shutil
import subprocess
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SURF_HTML = RACINE / "surf.html"


class TestPageHtmlAutonome(unittest.TestCase):
    def test_fichier_present(self):
        self.assertTrue(SURF_HTML.exists(), "surf.html doit exister à la racine du dépôt")

    def test_contenu_essentiel(self):
        html = SURF_HTML.read_text(encoding="utf-8")
        self.assertIn("https://marine-api.open-meteo.com/v1/marine", html)
        self.assertIn("https://api.open-meteo.com/v1/forecast", html)
        self.assertIn('id="logique"', html)
        for cle in ["biarritz", "anglet", "hossegor", "guethary", "lacanau", "nazare", "pipeline"]:
            self.assertIn(f'cle: "{cle}"', html)
        self.assertIn("hauteur: 0.30", html)
        self.assertIn("periode: 0.25", html)
        self.assertIn("vent: 0.25", html)

    def test_scoring_js_conforme(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node non disponible")
        resultat = subprocess.run(
            [node, str(RACINE / "tests" / "scoring_check.js")],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertIn("passent", resultat.stdout)


if __name__ == "__main__":
    unittest.main()
