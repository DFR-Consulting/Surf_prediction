import json
import unittest
import urllib.error

from surf_prediction.models import Spot
from surf_prediction.providers.open_meteo import (
    ErreurFournisseur,
    FournisseurOpenMeteo,
    URL_MARINE,
    URL_METEO,
)

SPOT = Spot("test", "Test", 43.48, -1.56, 300.0)

REPONSE_MARINE = {
    "hourly": {
        "time": ["2026-08-22T10:00", "2026-08-22T11:00"],
        "wave_height": [1.2, 2.0],
        "wave_direction": [250.0, 260.0],
        "wave_period": [9.0, 11.0],
        "swell_wave_height": [1.0, 1.7],
        "swell_wave_direction": [245.0, 255.0],
        "swell_wave_period": [10.0, 12.0],
        "wind_wave_height": [0.3, 0.5],
        "wind_wave_direction": [300.0, 300.0],
        "wind_wave_period": [4.0, 5.0],
        "sea_surface_temperature": [19.5, 19.6],
    }
}

REPONSE_METEO = {
    "hourly": {
        "time": ["2026-08-22T10:00", "2026-08-22T11:00"],
        "temperature_2m": [22.0, 23.5],
        "surface_pressure": [1015.0, 1014.0],
        "wind_speed_10m": [12.5, 30.0],
        "wind_direction_10m": [300.0, 120.0],
        "wind_gusts_10m": [20.0, 45.0],
    }
}


class FauxReponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FauxTransport:
    def __init__(self, reponses):
        self.reponses = reponses
        self.appels = []

    def __call__(self, requete, timeout=30):
        self.appels.append(requete.full_url)
        for url, payload in self.reponses.items():
            if requete.full_url.startswith(url):
                return FauxReponse(payload)
        raise AssertionError("URL inattendue : " + requete.full_url)


class TestFournisseurOpenMeteo(unittest.TestCase):
    def setUp(self):
        self.transport = FauxTransport({URL_MARINE: REPONSE_MARINE, URL_METEO: REPONSE_METEO})
        self.fournisseur = FournisseurOpenMeteo(transport=self.transport)

    def test_fusion_des_deux_api(self):
        previsions = self.fournisseur.previsions_brutes(SPOT, jours=2)
        self.assertEqual(len(previsions), 2)
        p0 = previsions[0]
        self.assertEqual(p0.horodate, "2026-08-22T10:00")
        self.assertEqual(p0.hauteur_vagues_m, 1.2)
        self.assertEqual(p0.periode_vagues_s, 9.0)
        self.assertEqual(p0.direction_vagues_deg, 250.0)
        self.assertEqual(p0.hauteur_houle_m, 1.0)
        self.assertEqual(p0.periode_houle_s, 10.0)
        self.assertEqual(p0.hauteur_vagues_vent_m, 0.3)
        self.assertEqual(p0.temperature_eau_c, 19.5)
        self.assertEqual(p0.temperature_air_c, 22.0)
        self.assertEqual(p0.pression_hpa, 1015.0)
        self.assertEqual(p0.vent_vitesse_kmh, 12.5)
        self.assertEqual(p0.vent_direction_deg, 300.0)
        self.assertEqual(p0.vent_rafales_kmh, 20.0)
        self.assertEqual(previsions[1].vent_direction_deg, 120.0)

    def test_ordre_chronologique(self):
        previsions = self.fournisseur.previsions_brutes(SPOT, jours=2)
        self.assertEqual([p.horodate for p in previsions], sorted(p.horodate for p in previsions))

    def test_unite_kmh_demandee(self):
        self.fournisseur.previsions_brutes(SPOT, jours=2)
        appel_meteo = next(u for u in self.transport.appels if u.startswith(URL_METEO))
        self.assertIn("wind_speed_unit=kmh", appel_meteo)

    def test_jours_limites(self):
        self.fournisseur.previsions_brutes(SPOT, jours=99)
        self.assertIn("forecast_days=7", self.transport.appels[0])
        self.fournisseur.previsions_brutes(SPOT, jours=0)
        self.assertIn("forecast_days=1", self.transport.appels[-1])

    def test_erreur_reseau(self):
        def transport_ko(requete, timeout=30):
            raise urllib.error.URLError("connexion refusée")

        with self.assertRaises(ErreurFournisseur):
            FournisseurOpenMeteo(transport=transport_ko).previsions_brutes(SPOT, jours=1)

    def test_valeurs_manquantes(self):
        reponse = {"hourly": {"time": ["2026-08-22T10:00"], "wave_height": [None]}}
        transport = FauxTransport({
            URL_MARINE: reponse,
            URL_METEO: {"hourly": {"time": ["2026-08-22T10:00"], "temperature_2m": [20.0]}},
        })
        previsions = FournisseurOpenMeteo(transport=transport).previsions_brutes(SPOT, jours=1)
        self.assertIsNone(previsions[0].hauteur_vagues_m)
        self.assertEqual(previsions[0].temperature_air_c, 20.0)


if __name__ == "__main__":
    unittest.main()
