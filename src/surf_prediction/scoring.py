from __future__ import annotations

from .models import PrevisionHoraire, Spot

POIDS = {
    "hauteur": 0.30,
    "periode": 0.25,
    "vent": 0.25,
    "thermique": 0.10,
    "pression": 0.10,
}

SEUILS_AVIS = (
    (80.0, "Excellent"),
    (60.0, "Bon"),
    (40.0, "Moyen"),
    (20.0, "Mauvais"),
    (0.0, "Très mauvais"),
)

POINTS_HAUTEUR = [
    (0.0, 5.0), (0.3, 25.0), (0.8, 80.0), (1.5, 100.0),
    (2.5, 90.0), (3.5, 55.0), (5.0, 20.0), (8.0, 5.0),
]
POINTS_PERIODE = [
    (0.0, 10.0), (3.0, 30.0), (5.0, 55.0), (7.0, 78.0),
    (9.0, 92.0), (12.0, 100.0), (20.0, 100.0),
]
POINTS_VENT = [
    (0.0, 100.0), (10.0, 95.0), (20.0, 75.0), (30.0, 55.0),
    (40.0, 35.0), (60.0, 15.0),
]
POINTS_T_AIR = [
    (0.0, 20.0), (10.0, 45.0), (15.0, 70.0), (20.0, 90.0),
    (24.0, 100.0), (28.0, 95.0), (32.0, 70.0), (40.0, 40.0),
]
POINTS_T_EAU = [
    (0.0, 20.0), (10.0, 35.0), (14.0, 60.0), (18.0, 90.0),
    (22.0, 100.0), (26.0, 90.0), (30.0, 60.0),
]
POINTS_PRESSION = [
    (992.0, 45.0), (1000.0, 65.0), (1008.0, 80.0),
    (1016.0, 90.0), (1024.0, 97.0), (1032.0, 100.0),
]


def _bornes(valeur: float) -> float:
    return min(100.0, max(0.0, valeur))


def _interpole(x: float, points: list[tuple[float, float]]) -> float:
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def score_hauteur(hauteur_m: float) -> float:
    return _bornes(_interpole(hauteur_m, POINTS_HAUTEUR))


def score_periode(periode_s: float) -> float:
    return _bornes(_interpole(periode_s, POINTS_PERIODE))


def ecart_angulaire(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def score_vent(
    vitesse_kmh: float,
    direction_deg: float | None = None,
    orientation_deg: float | None = None,
) -> float:
    score = _interpole(vitesse_kmh, POINTS_VENT)
    if direction_deg is not None and orientation_deg is not None:
        d = ecart_angulaire(direction_deg, orientation_deg)
        if d <= 45.0:
            score -= 25.0
        elif d >= 135.0:
            score += 5.0
        else:
            score -= 8.0
    return _bornes(score)


def score_thermique(t_air_c: float | None, t_eau_c: float | None) -> float | None:
    scores = []
    if t_air_c is not None:
        scores.append(_interpole(t_air_c, POINTS_T_AIR))
    if t_eau_c is not None:
        scores.append(_interpole(t_eau_c, POINTS_T_EAU))
    if not scores:
        return None
    return sum(scores) / len(scores)


def score_pression(pression_hpa: float) -> float:
    return _bornes(_interpole(pression_hpa, POINTS_PRESSION))


def avis_pour(score: float) -> str:
    for seuil, avis in SEUILS_AVIS:
        if score >= seuil:
            return avis
    return SEUILS_AVIS[-1][1]


def evaluer(prevision: PrevisionHoraire, spot: Spot) -> float:
    composantes: list[tuple[float, float]] = []
    if prevision.hauteur_vagues_m is not None:
        composantes.append((POIDS["hauteur"], score_hauteur(prevision.hauteur_vagues_m)))
    if prevision.periode_vagues_s is not None:
        composantes.append((POIDS["periode"], score_periode(prevision.periode_vagues_s)))
    if prevision.vent_vitesse_kmh is not None:
        composantes.append((
            POIDS["vent"],
            score_vent(prevision.vent_vitesse_kmh, prevision.vent_direction_deg, spot.orientation_deg),
        ))
    thermique = score_thermique(prevision.temperature_air_c, prevision.temperature_eau_c)
    if thermique is not None:
        composantes.append((POIDS["thermique"], thermique))
    if prevision.pression_hpa is not None:
        composantes.append((POIDS["pression"], score_pression(prevision.pression_hpa)))
    if not composantes:
        return 0.0
    total_poids = sum(p for p, _ in composantes)
    return sum(p * s for p, s in composantes) / total_poids


def annoter(prevision: PrevisionHoraire, spot: Spot) -> PrevisionHoraire:
    prevision.score = round(evaluer(prevision, spot), 1)
    prevision.avis = avis_pour(prevision.score)
    return prevision
