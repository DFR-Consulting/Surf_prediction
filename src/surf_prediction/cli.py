from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from . import scoring
from .models import Spot
from .providers.open_meteo import ErreurFournisseur, FournisseurOpenMeteo
from .spots import liste_spots, obtenir_spot, spot_par_defaut

ENTETES = [
    "Heure", "Vagues (m)", "Période (s)", "Dir. vagues", "Houle (m)",
    "Vent (km/h)", "Rafales (km/h)", "Dir. vent", "Air (°C)", "Eau (°C)",
    "Pression (hPa)", "Score", "Avis",
]


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="surf-prediction",
        description="Prédicteur de qualité de surf : vagues, vent, températures, pression et score 0-100.",
    )
    parser.add_argument("--spot", help="Clé d'un spot connu (voir --liste-spots). Par défaut : biarritz.")
    parser.add_argument("--liste-spots", action="store_true", help="Lister les spots connus puis quitter.")
    parser.add_argument("--lat", type=float, help="Latitude d'un spot personnalisé.")
    parser.add_argument("--lon", type=float, help="Longitude d'un spot personnalisé.")
    parser.add_argument("--orientation", type=float, help="Orientation du spot personnalisé (azimut vers la mer, en degrés).")
    parser.add_argument("--nom", help="Nom du spot personnalisé.")
    parser.add_argument("--jours", type=int, default=3, help="Nombre de jours de prévision (1-7, défaut 3).")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Format de sortie (défaut : table).")
    return parser


def _resoudre_spot(args: argparse.Namespace) -> Spot:
    if args.lat is not None and args.lon is not None:
        return Spot(
            cle="personnalise",
            nom=args.nom or "Spot personnalisé",
            latitude=args.lat,
            longitude=args.lon,
            orientation_deg=args.orientation or 0.0,
        )
    if args.spot:
        spot = obtenir_spot(args.spot)
        if spot is None:
            connus = ", ".join(sorted(s.cle for s in liste_spots()))
            raise ValueError(f"Spot inconnu : {args.spot!r}. Spots connus : {connus}.")
        return spot
    return spot_par_defaut()


def _fmt(valeur: float | None, decimales: int = 1) -> str:
    return f"{valeur:.{decimales}f}" if valeur is not None else "-"


def _fmt_dir(valeur: float | None) -> str:
    return f"{valeur:.0f}°" if valeur is not None else "-"


def _fmt_heure(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m %Hh%M")
    except ValueError:
        return iso


def _ligne(p) -> list[str]:
    return [
        _fmt_heure(p.horodate),
        _fmt(p.hauteur_vagues_m),
        _fmt(p.periode_vagues_s),
        _fmt_dir(p.direction_vagues_deg),
        _fmt(p.hauteur_houle_m),
        _fmt(p.vent_vitesse_kmh),
        _fmt(p.vent_rafales_kmh),
        _fmt_dir(p.vent_direction_deg),
        _fmt(p.temperature_air_c),
        _fmt(p.temperature_eau_c),
        _fmt(p.pression_hpa, 0),
        f"{p.score:.0f}",
        p.avis,
    ]


def _afficher_table(spot: Spot, previsions: list) -> None:
    lignes = [_ligne(p) for p in previsions]
    largeurs = [len(e) for e in ENTETES]
    for ligne in lignes:
        for i, cellule in enumerate(ligne):
            largeurs[i] = max(largeurs[i], len(cellule))
    print(f"Prévisions pour {spot.nom} ({spot.latitude:.4f}, {spot.longitude:.4f}) — {len(previsions)} heures")
    print("  ".join(e.ljust(largeurs[i]) for i, e in enumerate(ENTETES)))
    print("  ".join("-" * largeurs[i] for i in range(len(ENTETES))))
    for ligne in lignes:
        print("  ".join(cellule.ljust(largeurs[i]) for i, cellule in enumerate(ligne)))


def main(argv: list[str] | None = None) -> int:
    args = construire_parser().parse_args(argv)
    if args.liste_spots:
        for s in liste_spots():
            print(f"{s.cle:<12} {s.nom:<48} lat={s.latitude:.4f} lon={s.longitude:.4f} orientation={s.orientation_deg:.0f}°")
        return 0
    try:
        spot = _resoudre_spot(args)
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2
    try:
        brutes = FournisseurOpenMeteo().previsions_brutes(spot, args.jours)
    except ErreurFournisseur as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2
    previsions = [scoring.annoter(p, spot) for p in brutes]
    if args.format == "json":
        print(json.dumps(
            {"spot": spot.to_dict(), "previsions": [p.to_dict() for p in previsions]},
            ensure_ascii=False,
            indent=2,
        ))
    else:
        _afficher_table(spot, previsions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
