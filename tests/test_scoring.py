import unittest

from surf_prediction import scoring
from surf_prediction.models import PrevisionHoraire, Spot

SPOT = Spot("test", "Test", 43.0, -1.5, 300.0)


class TestInterpolation(unittest.TestCase):
    def test_bornes_inferieures_et_superieures(self):
        self.assertEqual(scoring._interpole(-5, [(0, 10), (10, 20)]), 10)
        self.assertEqual(scoring._interpole(50, [(0, 10), (10, 20)]), 20)

    def test_valeur_intermediaire(self):
        self.assertAlmostEqual(scoring._interpole(5, [(0, 10), (10, 20)]), 15)


class TestSousScores(unittest.TestCase):
    def test_hauteur_ideale(self):
        self.assertEqual(scoring.score_hauteur(1.5), 100.0)

    def test_hauteur_trop_faible_ou_trop_forte(self):
        self.assertLess(scoring.score_hauteur(0.1), 30)
        self.assertLess(scoring.score_hauteur(6.0), 30)

    def test_periode_longue_meilleure(self):
        self.assertEqual(scoring.score_periode(12.0), 100.0)
        self.assertLess(scoring.score_periode(2.0), 40)

    def test_ecart_angulaire(self):
        self.assertAlmostEqual(scoring.ecart_angulaire(350, 10), 20.0)
        self.assertAlmostEqual(scoring.ecart_angulaire(0, 180), 180.0)

    def test_vent_onshore_offshore_sideshore(self):
        onshore = scoring.score_vent(20, 300, 300)
        offshore = scoring.score_vent(20, 120, 300)
        sideshore = scoring.score_vent(20, 30, 300)
        self.assertAlmostEqual(onshore, 50.0)
        self.assertAlmostEqual(offshore, 80.0)
        self.assertAlmostEqual(sideshore, 67.0)
        self.assertGreater(offshore, sideshore)
        self.assertGreater(sideshore, onshore)

    def test_vent_sans_direction(self):
        self.assertAlmostEqual(scoring.score_vent(20, None, 300), 75.0)

    def test_thermique(self):
        self.assertEqual(scoring.score_thermique(24, 22), 100.0)
        self.assertIsNone(scoring.score_thermique(None, None))
        self.assertAlmostEqual(scoring.score_thermique(24, None), 100.0)

    def test_pression(self):
        self.assertEqual(scoring.score_pression(1032), 100.0)
        self.assertLess(scoring.score_pression(995), 60)


class TestEvaluer(unittest.TestCase):
    def test_conditions_ideales(self):
        p = PrevisionHoraire(
            horodate="2026-08-22T10:00",
            hauteur_vagues_m=1.5, periode_vagues_s=12.0,
            vent_vitesse_kmh=5.0, vent_direction_deg=120.0,
            temperature_air_c=24.0, temperature_eau_c=22.0, pression_hpa=1024.0,
        )
        self.assertAlmostEqual(scoring.evaluer(p, SPOT), 99.7, places=1)

    def test_aucune_donnee(self):
        self.assertEqual(scoring.evaluer(PrevisionHoraire(horodate="2026-08-22T10:00"), SPOT), 0.0)

    def test_renormalisation_si_donnees_manquantes(self):
        p = PrevisionHoraire(horodate="2026-08-22T10:00", hauteur_vagues_m=1.5)
        self.assertAlmostEqual(scoring.evaluer(p, SPOT), 100.0)

    def test_conditions_mauvaises(self):
        p = PrevisionHoraire(
            horodate="2026-08-22T10:00",
            hauteur_vagues_m=0.1, periode_vagues_s=2.0,
            vent_vitesse_kmh=45.0, vent_direction_deg=300.0,
            temperature_air_c=8.0, temperature_eau_c=11.0, pression_hpa=995.0,
        )
        self.assertLess(scoring.evaluer(p, SPOT), 40)


class TestAvisEtAnnotation(unittest.TestCase):
    def test_seuils(self):
        self.assertEqual(scoring.avis_pour(100), "Excellent")
        self.assertEqual(scoring.avis_pour(80), "Excellent")
        self.assertEqual(scoring.avis_pour(79.9), "Bon")
        self.assertEqual(scoring.avis_pour(60), "Bon")
        self.assertEqual(scoring.avis_pour(40), "Moyen")
        self.assertEqual(scoring.avis_pour(20), "Mauvais")
        self.assertEqual(scoring.avis_pour(19.9), "Très mauvais")
        self.assertEqual(scoring.avis_pour(0), "Très mauvais")

    def test_annoter(self):
        p = PrevisionHoraire(horodate="2026-08-22T10:00", hauteur_vagues_m=1.5)
        scoring.annoter(p, SPOT)
        self.assertEqual(p.score, 100.0)
        self.assertEqual(p.avis, "Excellent")


if __name__ == "__main__":
    unittest.main()
