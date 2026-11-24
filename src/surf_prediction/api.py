from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import scoring
from .models import Spot
from .providers.open_meteo import ErreurFournisseur, FournisseurOpenMeteo
from .spots import liste_spots, obtenir_spot

DOSSIER_WEB = Path(__file__).resolve().parent / "web"


def previsions_completes(spot: Spot, jours: int, fournisseur) -> list[dict]:
    brutes = fournisseur.previsions_brutes(spot, jours)
    return [scoring.annoter(p, spot).to_dict() for p in brutes]


class GestionnaireRequetes(BaseHTTPRequestHandler):
    serveur_version = "SurfPrediction/0.1"
    fournisseur = FournisseurOpenMeteo()

    def _envoyer_json(self, donnees, statut: int = 200) -> None:
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        self.send_response(statut)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def _envoyer_erreur(self, statut: int, message: str) -> None:
        self._envoyer_json({"erreur": message}, statut)

    def do_GET(self) -> None:
        route = urlparse(self.path)
        if route.path == "/api/spots":
            self._envoyer_json({"spots": [s.to_dict() for s in liste_spots()]})
        elif route.path == "/api/previsions":
            params = parse_qs(route.query)
            cle = (params.get("spot") or ["biarritz"])[0]
            spot = obtenir_spot(cle)
            if spot is None:
                self._envoyer_erreur(404, f"Spot inconnu : {cle!r}")
                return
            try:
                jours = int((params.get("jours") or ["3"])[0])
            except ValueError:
                self._envoyer_erreur(400, "Paramètre 'jours' invalide (entier attendu)")
                return
            try:
                previsions = previsions_completes(spot, jours, self.fournisseur)
            except ErreurFournisseur as exc:
                self._envoyer_erreur(502, str(exc))
                return
            self._envoyer_json({"spot": spot.to_dict(), "previsions": previsions})
        elif route.path in ("/", "/index.html"):
            index = DOSSIER_WEB / "index.html"
            if not index.exists():
                self._envoyer_erreur(404, "Page web introuvable")
                return
            corps = index.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)
        else:
            self._envoyer_erreur(404, "Route inconnue")

    def log_message(self, format, *args) -> None:
        pass


def creer_serveur(hote: str = "127.0.0.1", port: int = 8000, fournisseur=None) -> ThreadingHTTPServer:
    class Gestionnaire(GestionnaireRequetes):
        pass

    Gestionnaire.fournisseur = fournisseur if fournisseur is not None else FournisseurOpenMeteo()
    return ThreadingHTTPServer((hote, port), Gestionnaire)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="surf-prediction-api",
        description="API HTTP du prédicteur de surf (écoute en boucle locale par défaut).",
    )
    parser.add_argument("--hote", default="127.0.0.1", help="Adresse d'écoute (défaut : 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut : 8000).")
    args = parser.parse_args(argv)
    serveur = creer_serveur(args.hote, args.port)
    print(f"API et page web disponibles sur http://{args.hote}:{args.port} (Ctrl+C pour arrêter)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        serveur.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
