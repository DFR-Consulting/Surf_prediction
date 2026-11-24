from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from ..models import PrevisionHoraire, Spot

URL_MARINE = "https://marine-api.open-meteo.com/v1/marine"
URL_METEO = "https://api.open-meteo.com/v1/forecast"

JOURS_MAX = 7

HOURLY_MARINE = ",".join([
    "wave_height",
    "wave_direction",
    "wave_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "wind_wave_height",
    "wind_wave_direction",
    "wind_wave_period",
    "sea_surface_temperature",
])

HOURLY_METEO = ",".join([
    "temperature_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
])


class ErreurFournisseur(RuntimeError):
    pass


def _telecharger_json(url: str, params: dict, transport, timeout: int = 30) -> dict:
    requete = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "surf-prediction/0.1.0"},
    )
    try:
        with transport(requete, timeout=timeout) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise ErreurFournisseur(f"Appel API impossible ({url}) : {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ErreurFournisseur(f"Réponse API invalide ({url}) : {exc}") from exc


def _get(horaire: dict, cle: str, index: int) -> float | None:
    valeurs = horaire.get(cle)
    if not valeurs or index >= len(valeurs):
        return None
    valeur = valeurs[index]
    return float(valeur) if valeur is not None else None


def _fusionner(marine: dict, meteo: dict) -> list[PrevisionHoraire]:
    hourly_marine = marine.get("hourly", {})
    previsions: dict[str, PrevisionHoraire] = {}
    for i, horodate in enumerate(hourly_marine.get("time", [])):
        previsions[horodate] = PrevisionHoraire(
            horodate=horodate,
            hauteur_vagues_m=_get(hourly_marine, "wave_height", i),
            periode_vagues_s=_get(hourly_marine, "wave_period", i),
            direction_vagues_deg=_get(hourly_marine, "wave_direction", i),
            hauteur_houle_m=_get(hourly_marine, "swell_wave_height", i),
            periode_houle_s=_get(hourly_marine, "swell_wave_period", i),
            hauteur_vagues_vent_m=_get(hourly_marine, "wind_wave_height", i),
            temperature_eau_c=_get(hourly_marine, "sea_surface_temperature", i),
        )
    hourly_meteo = meteo.get("hourly", {})
    for i, horodate in enumerate(hourly_meteo.get("time", [])):
        prevision = previsions.get(horodate)
        if prevision is None:
            continue
        prevision.temperature_air_c = _get(hourly_meteo, "temperature_2m", i)
        prevision.pression_hpa = _get(hourly_meteo, "surface_pressure", i)
        prevision.vent_vitesse_kmh = _get(hourly_meteo, "wind_speed_10m", i)
        prevision.vent_direction_deg = _get(hourly_meteo, "wind_direction_10m", i)
        prevision.vent_rafales_kmh = _get(hourly_meteo, "wind_gusts_10m", i)
    return [previsions[h] for h in sorted(previsions)]


class FournisseurOpenMeteo:
    def __init__(self, transport=None):
        self._transport = transport or urllib.request.urlopen

    def previsions_brutes(self, spot: Spot, jours: int = 5) -> list[PrevisionHoraire]:
        jours = max(1, min(int(jours), JOURS_MAX))
        base = {
            "latitude": spot.latitude,
            "longitude": spot.longitude,
            "forecast_days": jours,
            "timezone": "auto",
        }
        marine = _telecharger_json(URL_MARINE, {**base, "hourly": HOURLY_MARINE}, self._transport)
        meteo = _telecharger_json(
            URL_METEO,
            {**base, "hourly": HOURLY_METEO, "wind_speed_unit": "kmh"},
            self._transport,
        )
        return _fusionner(marine, meteo)
