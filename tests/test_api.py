import json
import threading
import unittest
import urllib.error
import urllib.request

from surf_prediction.api import creer_serveur
from surf_prediction.models import PrevisionHoraire, Spot


class FauxFournisseur:
    def previsions_brutes(self, spot: Spot, jours: int):
        return [
            PrevisionHoraire(
                horodate="2026-08-22T10:00",
                hauteur_vagues_m=1.5, periode_vagues_s=12.0, direction_vagues_deg=250.0,
                hauteur_houle_m=1.2, periode_houle_s=13.0, hauteur_vagues_vent_m=0.3,
                vent_vitesse_kmh=8.0, vent_rafales_kmh=14.0, vent_direction_deg=120.0,
                temperature_air_c=24.0, temperature_eau_c=21.0, pression_hpa=1022.0,
            )
        ]


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = creer_serveur("127.0.0.1", 0, FauxFournisseur())
        cls.port = cls.serveur.server_address[1]
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()
        cls.thread.join(timeout=5)

    def _get(self, chemin):
        url = f"http://127.0.0.1:{self.port}{chemin}"
        try:
            with urllib.request.urlopen(url, timeout=5) as reponse:
                return reponse.status, reponse.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def test_spots(self):
        statut, corps = self._get("/api/spots")
        self.assertEqual(statut, 200)
        data = json.loads(corps.decode("utf-8"))
        cles = [s["cle"] for s in data["spots"]]
        self.assertIn("biarritz", cles)
        self.assertIn("hossegor", cles)

    def test_previsions(self):
        statut, corps = self._get("/api/previsions?spot=hossegor&jours=2")
        self.assertEqual(statut, 200)
        data = json.loads(corps.decode("utf-8"))
        self.assertEqual(data["spot"]["cle"], "hossegor")
        self.assertEqual(len(data["previsions"]), 1)
        p = data["previsions"][0]
        self.assertEqual(p["hauteur_vagues_m"], 1.5)
        self.assertEqual(p["temperature_eau_c"], 21.0)
        self.assertGreater(p["score"], 0)
        self.assertIn(p["avis"], ["Excellent", "Bon", "Moyen", "Mauvais", "Très mauvais"])

    def test_spot_inconnu(self):
        statut, corps = self._get("/api/previsions?spot=nowhere")
        self.assertEqual(statut, 404)
        self.assertIn("erreur", json.loads(corps.decode("utf-8")))

    def test_jours_invalide(self):
        statut, _ = self._get("/api/previsions?jours=abc")
        self.assertEqual(statut, 400)

    def test_page_web(self):
        statut, corps = self._get("/")
        self.assertEqual(statut, 200)
        self.assertIn("Prédicteur de qualité de surf", corps.decode("utf-8"))

    def test_route_inconnue(self):
        statut, _ = self._get("/api/rien")
        self.assertEqual(statut, 404)


if __name__ == "__main__":
    unittest.main()
