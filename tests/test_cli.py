import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from surf_prediction import cli
from surf_prediction.models import PrevisionHoraire

PREVISION = PrevisionHoraire(
    horodate="2026-08-22T10:00",
    hauteur_vagues_m=1.5, periode_vagues_s=12.0, direction_vagues_deg=250.0,
    hauteur_houle_m=1.2, periode_houle_s=13.0, hauteur_vagues_vent_m=0.3,
    vent_vitesse_kmh=8.0, vent_rafales_kmh=14.0, vent_direction_deg=120.0,
    temperature_air_c=24.0, temperature_eau_c=21.0, pression_hpa=1022.0,
)


def _faux_fournisseur():
    instance = mock.Mock()
    instance.previsions_brutes.return_value = [PREVISION]
    return mock.Mock(return_value=instance)


class TestCli(unittest.TestCase):
    def test_format_json(self):
        with mock.patch.object(cli, "FournisseurOpenMeteo", _faux_fournisseur()):
            sortie = io.StringIO()
            with redirect_stdout(sortie):
                code = cli.main(["--spot", "biarritz", "--jours", "1", "--format", "json"])
        self.assertEqual(code, 0)
        data = json.loads(sortie.getvalue())
        self.assertEqual(data["spot"]["cle"], "biarritz")
        self.assertEqual(len(data["previsions"]), 1)
        p = data["previsions"][0]
        self.assertEqual(p["hauteur_vagues_m"], 1.5)
        self.assertEqual(p["pression_hpa"], 1022.0)
        self.assertGreater(p["score"], 80)

    def test_format_table(self):
        with mock.patch.object(cli, "FournisseurOpenMeteo", _faux_fournisseur()):
            sortie = io.StringIO()
            with redirect_stdout(sortie):
                code = cli.main(["--spot", "hossegor", "--jours", "1"])
        self.assertEqual(code, 0)
        texte = sortie.getvalue()
        self.assertIn("Hossegor", texte)
        self.assertIn("Pression (hPa)", texte)
        self.assertIn("Score", texte)
        self.assertIn("22/08 10h00", texte)

    def test_liste_spots(self):
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            code = cli.main(["--liste-spots"])
        self.assertEqual(code, 0)
        self.assertIn("biarritz", sortie.getvalue())
        self.assertIn("pipeline", sortie.getvalue())

    def test_spot_inconnu(self):
        sortie = io.StringIO()
        with redirect_stderr(sortie):
            code = cli.main(["--spot", "inconnu"])
        self.assertEqual(code, 2)
        self.assertIn("Spot inconnu", sortie.getvalue())

    def test_spot_personnalise(self):
        with mock.patch.object(cli, "FournisseurOpenMeteo", _faux_fournisseur()) as mock_fournisseur:
            sortie = io.StringIO()
            with redirect_stdout(sortie):
                code = cli.main([
                    "--lat", "43.48", "--lon", "-1.56",
                    "--orientation", "300", "--nom", "Ma plage",
                    "--jours", "1", "--format", "json",
                ])
        self.assertEqual(code, 0)
        data = json.loads(sortie.getvalue())
        self.assertEqual(data["spot"]["nom"], "Ma plage")
        self.assertEqual(data["spot"]["orientation_deg"], 300.0)
        mock_fournisseur.return_value.previsions_brutes.assert_called_once()


if __name__ == "__main__":
    unittest.main()
